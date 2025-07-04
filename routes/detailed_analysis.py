from fastapi import APIRouter, HTTPException, Header
from plugin.db import scrapped_data, sentiment_data
from utils.inference_helpers import analyze_sentiment_remote, extract_text_by_platform
from utils.log import logging
from utils.auth import authenticate_token
from utils.text_cleaner import clean_text, extract_hashtags

detailed_analysis_router = APIRouter(tags=["Detailed Analysis"])

@detailed_analysis_router.post("/process-session/{session_id}")
def process_all_in_session(session_id: str, authorization: str = Header(..., description="Bearer token or raw token")):

    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        token = authorization
    
    # 🔐 Validate the token
    authenticate_token(token)
    
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

            hashtags = extract_hashtags(text)
            cleaned_text = clean_text(text) 

            analysis = analyze_sentiment_remote(cleaned_text)

            sentiment_data.insert_one({
                "raw_id": doc["_id"],
                "sessionId": session_id,
                "platform": doc.get("platform"),
                "text": text,
                "hashtags": hashtags,
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