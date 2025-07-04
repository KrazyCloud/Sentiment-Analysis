from fastapi import APIRouter, HTTPException, Query, Header
from plugin.schemas import SessionRequest
from plugin.db import sentiment_data, scrapped_data
from utils.auth import authenticate_token

session_ranking_router = APIRouter(tags=["Session Ranking"])

@session_ranking_router.post("/session-sentiment-ranking")
def session_sentiment_ranking(
    request: SessionRequest,
    min_posts: int = Query(3, description="Minimum number of posts to include session in analysis"),
    authorization: str = Header(..., description="Bearer token or raw token")
):
    
    # Handle both "Bearer <token>" and plain "<token>"
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        token = authorization
        
    # 🔐 Validate the token
    authenticate_token(token)

    rankings = []
    skipped_sessions = []

    for session_id in request.session_ids:
        posts = list(sentiment_data.find({"sessionId": session_id, "analysis.model": "sentiment-v3"}))
        if not posts:
            skipped_sessions.append({"session_id": session_id, "reason": "No posts found"})
            continue

        total_posts = len(posts)
        if total_posts < min_posts:
            skipped_sessions.append({"session_id": session_id, "reason": f"Only {total_posts} posts"})
            continue

        total_negative = sum(post.get("analysis", {}).get("scores", {}).get("Negative", 0.0) for post in posts)
        total_positive = sum(post.get("analysis", {}).get("scores", {}).get("Positive", 0.0) for post in posts)
        total_neutral = sum(post.get("analysis", {}).get("scores", {}).get("Neutral", 0.0) for post in posts)

        scrapped_doc = scrapped_data.find_one({"sessionId": session_id})
        keyword = scrapped_doc.get("keyword", "Unknown") if scrapped_doc else "Unknown"

        rankings.append({
            "session_id": session_id,
            "keyword": keyword,
            "avg_negative_score": round(total_negative / total_posts, 4),
            "avg_positive_score": round(total_positive / total_posts, 4),
            "avg_neutral_score": round(total_neutral / total_posts, 4),
            "total_posts": total_posts
        })

    if not rankings:
        raise HTTPException(status_code=404, detail="No valid session data found (posts <= threshold or missing)")

    # Sort sessions
    sorted_by_negative = sorted(rankings, key=lambda x: x["avg_negative_score"], reverse=True)
    sorted_by_positive = sorted(rankings, key=lambda x: x["avg_positive_score"], reverse=True)
    sorted_by_total_posts = sorted(rankings, key=lambda x: x["total_posts"], reverse=True)

    most_negative = sorted_by_negative[0]
    most_positive = sorted_by_positive[0]

    # Edge case: Same session is both highest positive and negative
    if most_negative["session_id"] == most_positive["session_id"]:
        summary = (
            f"The session '{most_negative['keyword']}' stands out by having both the highest average positive sentiment "
            f"({most_positive['avg_positive_score']:.4f}) and the highest average negative sentiment "
            f"({most_negative['avg_negative_score']:.4f}) across {most_negative['total_posts']} posts. "
            f"This indicates that people expressed very mixed opinions in this session—some posts were highly positive while others were strongly negative."
        )

        return {
            "is_session_shared": True,
            "mixed_sentiment_session": most_negative,
            "all_session_rankings": sorted_by_total_posts,
            "skipped_sessions": skipped_sessions,
            "summary": summary
        }

    # Normal case
    summary = (
        f"Among the provided sessions, session '{most_negative['keyword']}' shows the highest average negative sentiment "
        f"with a score of {most_negative['avg_negative_score']:.4f} across {most_negative['total_posts']} posts. "
        f"This suggests that the content in this session may be more emotionally charged, critical, or negative."
        f"In contrast, session '{most_positive['keyword']}' has the highest average positive sentiment score of "
        f"{most_positive['avg_positive_score']:.4f} over {most_positive['total_posts']} posts, indicating a more positive and constructive tone overall."
    )

    return {
        "is_session_shared": False,
        "highest_avg_negative_session": most_negative,
        "highest_avg_positive_session": most_positive,
        "all_session_rankings": sorted_by_total_posts,
        "skipped_sessions": skipped_sessions,
        "summary": summary
    }
