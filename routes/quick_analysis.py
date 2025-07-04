from fastapi import APIRouter, HTTPException, Header
from utils.inference_helpers import analyze_sentiment_remote
from plugin.schemas import TextInput
from utils.auth import authenticate_token

quick_analysis_router = APIRouter(tags=["Quick Analysis"])

@quick_analysis_router.post("/anlaysis-sentiment")
def analyze_text_endpoint(payload: TextInput, authorization: str = Header(..., description="Bearer token or raw token")):

    # Handle both "Bearer <token>" and plain "<token>"
    if authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        token = authorization
    # 🔐 Validate the token
    authenticate_token(token)
    
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Input text is empty.")
    
    result = analyze_sentiment_remote(payload.text, payload.model)
    return result