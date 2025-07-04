from plugin.inference_client import INFERENCE_API_URL, DEFAULT_MODEL_NAME
from typing import Dict
import requests
from fastapi import HTTPException
from utils.text_cleaner import clean_text


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