from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import requests
from typing import List
import os
import re
import logging
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI()

# MongoDB setup
client = MongoClient("mongodb://user1:cdac%40123%23@10.226.53.238:27017/textdata")
db = client["textdata"]
scrapped_data = db["scrappedPosts"]
sentiment_data = db["socialMediaSentiment"]

# Inference API URL
INFERENCE_API_URL = "http://10.226.53.238:5000/infer"
DEFAULT_MODEL_NAME = "sentiment-v3"

# Scheme
class TextInput(BaseModel):
    text: str
    model: str = DEFAULT_MODEL_NAME

class SessionRequest(BaseModel):
    session_ids: List[str]


# Scripts
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", "http", text)
    text = re.sub(r"@\w+", "@user", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def analyze_sentiment_remote(text: str, model: str = DEFAULT_MODEL_NAME) -> Dict:
    try:
        response = requests.post(INFERENCE_API_URL, json={
            "text": clean_text(text),
            "model": model
        })
        if response.status_code != 200:
            raise Exception(f"Inference API returned status {response.status_code}: {response.text}")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling inference API: {e}")

def extract_text_by_platform(doc: dict) -> str:
    platform = doc.get("platform", "").lower()
    if platform == "twitter":
        return doc.get("text", "")
    elif platform == "youtube":
        return doc.get("metadata", "")
    elif platform == "reddit":
        return doc.get("content", "")
    return ""


# routes

# sentiment anlaysis
@app.post("/process-session/{session_id}")
def process_all_in_session(session_id: str):
    unprocessed = list(scrapped_data.find({"sessionId": session_id, "status": 1}))

    if not unprocessed:
        raise HTTPException(status_code=404, detail="No unprocessed posts found for this session.")

    processed_count = 0
    for doc in unprocessed:
        try:
            text = extract_text_by_platform(doc)
            if not text:
                logging.warning(f"No valid text found in post {doc['_id']}. Skipping.")
                continue

            analysis = analyze_sentiment_remote(text)

            sentiment_data.insert_one({
                "raw_id": doc["_id"],
                "sessionId": session_id,
                "platform": doc.get("platform"),
                "text": text,
                "analysis": analysis,
                "datetime": doc.get("datetime"),
                "status": 3
            })

            scrapped_data.update_one({"_id": doc["_id"]}, {"$set": {"status": 3}})
            processed_count += 1

        except Exception as e:
            logging.error(f"Error processing post {doc['_id']}: {str(e)}")
            scrapped_data.update_one({"_id": doc["_id"]}, {"$set": {"status": 4}})

    return {
        "message": f"Session {session_id} processed.",
        "posts_processed": processed_count,
        "total_attempted": len(unprocessed)
    }

# Quick Text and Model Sentiment Anlaysis
@app.post("/analyze-text")
def analyze_text_endpoint(payload: TextInput):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Input text is empty.")
    
    result = analyze_sentiment_remote(payload.text, payload.model)
    return result


    
# Sentiment Summary Endpoint
@app.post("/session-sentiment-summary")
def analyze_sessions(request: SessionRequest):
    output = []

    for session_id in request.session_ids:
        posts = list(sentiment_data.find({"sessionId": session_id, "analysis.model": "sentiment-v3"}))
        if not posts:
            continue

        total_posts = len(posts)
        total_negative = sum(post.get("analysis", {}).get("scores", {}).get("Negative", 0.0) for post in posts)
        total_positive = sum(post.get("analysis", {}).get("scores", {}).get("Positive", 0.0) for post in posts)

        if total_posts == 0:
            continue

        normalized_negative_score = total_negative / total_posts
        negative_content_share = total_negative / (total_negative + total_positive) if (total_negative + total_positive) > 0 else 0.0

        summary = (
            f"Out of {total_posts} analyzed posts in this session, "
            f"the average negative sentiment is {normalized_negative_score:.4f}, "
            f"and negative content accounts for {negative_content_share * 100:.2f}% of the overall sentiment. "
        )

        if negative_content_share < 0.2:
            summary += "This indicates a predominantly positive tone."
        elif negative_content_share < 0.5:
            summary += "There is a moderate level of negative sentiment."
        else:
            summary += "The session contains a high amount of negative content."

        output.append({
            "session_id": session_id,
            "summary": summary
        })

    if not output:
        raise HTTPException(status_code=404, detail="No sentiment data found for provided session IDs")

    return output

# -------------------- 2. New Ranking Endpoint --------------------
@app.post("/session-sentiment-ranking")
def session_sentiment_ranking(request: SessionRequest):
    rankings = []

    for session_id in request.session_ids:
        posts = list(sentiment_data.find({"sessionId": session_id, "analysis.model": "sentiment-v3"}))
        if not posts:
            continue

        total_posts = len(posts)
        total_negative = sum(post.get("analysis", {}).get("scores", {}).get("Negative", 0.0) for post in posts)
        total_positive = sum(post.get("analysis", {}).get("scores", {}).get("Positive", 0.0) for post in posts)

        if total_posts == 0:
            continue

        rankings.append({
            "session_id": session_id,
            "avg_negative_score": round(total_negative / total_posts, 4),
            "avg_positive_score": round(total_positive / total_posts, 4),
            "total_posts": total_posts
        })

    if not rankings:
        raise HTTPException(status_code=404, detail="No data found for sentiment-v3")

    # Sort by scores
    sorted_by_negative = sorted(rankings, key=lambda x: x["avg_negative_score"], reverse=True)
    sorted_by_positive = sorted(rankings, key=lambda x: x["avg_positive_score"], reverse=True)

    # Best sessions
    most_negative = sorted_by_negative[0]
    most_positive = sorted_by_positive[0]

    # Human language summary
    human_summary = (
        f"Among the provided sessions, session '{most_negative['session_id']}' shows the highest average negative sentiment "
        f"with a score of {most_negative['avg_negative_score']:.4f} across {most_negative['total_posts']} posts. "
        f"This suggests that the content in this session may be more emotionally charged, critical, or negative.\n\n"
        f"In contrast, session '{most_positive['session_id']}' has the highest average positive sentiment score of "
        f"{most_positive['avg_positive_score']:.4f} over {most_positive['total_posts']} posts, indicating a more positive and constructive tone overall."
    )

    return {
        "highest_avg_negative_session": most_negative,
        "highest_avg_positive_session": most_positive,
        "all_session_rankings": rankings,
        "summary": human_summary
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("sentiment-pipeline:app", host="10.226.51.33", port=8000, reload=False)