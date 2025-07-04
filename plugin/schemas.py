from pydantic import BaseModel
from typing import List
from plugin.inference_client import DEFAULT_MODEL_NAME

# Session Details model
class SessionRequest(BaseModel):
    session_ids: List[str]

# Calling Inference API for model
class TextInput(BaseModel):
    text: str
    model: str = DEFAULT_MODEL_NAME