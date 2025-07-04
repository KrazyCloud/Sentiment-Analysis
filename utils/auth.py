import jwt
import datetime
import base64
import os
from dotenv import load_dotenv
from fastapi import HTTPException

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret")
ALGORITHM = "HS256"

# Fix base64 padding
missing_padding = len(SECRET_KEY) % 4
if missing_padding:
    SECRET_KEY += "=" * (4 - missing_padding)

SECRET_KEY_DECODE = base64.b64decode(SECRET_KEY)

def authenticate_token(token: str):
    try:
        if not token or len(token.split('.')) != 3:
            raise HTTPException(status_code=401, detail="Malformed token")

        # Decode without verifying to check exp
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        exp_time = datetime.datetime.utcfromtimestamp(unverified_payload["exp"])
        current_time = datetime.datetime.utcnow()

        # Decode with signature
        payload = jwt.decode(token, SECRET_KEY_DECODE, algorithms=[ALGORITHM])

        if current_time > exp_time:
            raise HTTPException(status_code=401, detail="Token expired")

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Token decode error")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
