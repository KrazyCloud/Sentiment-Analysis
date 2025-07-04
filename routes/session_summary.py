from fastapi import APIRouter, HTTPException,Header
from plugin.schemas import SessionRequest
from plugin.db import sentiment_data, scrapped_data
from utils.auth import authenticate_token

session_summary_router = APIRouter(tags=["Session Summary"])

@session_summary_router.post("/session-sentiment-summary")
def analyze_sessions(request: SessionRequest, authorization: str = Header(..., description="Bearer token or raw token")):

    # Handle both "Bearer <token>" and plain "<token>"
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        token = authorization
    # 🔐 Validate the token
    authenticate_token(token)

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

        # Get keyword from scrapped_data
        scrapped_doc = scrapped_data.find_one({"sessionId": session_id})
        keyword = scrapped_doc.get("keyword", "Unknown") if scrapped_doc else "Unknown"

        normalized_negative_score = total_negative / total_posts
        negative_content_share = total_negative / (total_negative + total_positive) if (total_negative + total_positive) > 0 else 0.0

        summary = (
            f"For The Topic: {keyword}, out of {total_posts} analyzed posts in this session, "
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
            "summary": summary,
            "keyword": keyword,
            "normalized_score": normalized_negative_score
        })

    if not output:
        raise HTTPException(status_code=404, detail="No sentiment data found for provided session IDs")

    return output