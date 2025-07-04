from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.detailed_analysis import detailed_analysis_router
from routes.quick_analysis import quick_analysis_router
from routes.session_summary import session_summary_router
from routes.session_ranking import session_ranking_router
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers with error handling
try:
    app.include_router(detailed_analysis_router)
    logger.info("✅ Sentiment Analysis loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading Sentiment Analysis: {e}")

try:
    app.include_router(quick_analysis_router)
    logger.info("✅ Quick Analysis loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading Quick Analysis: {e}")

try:
    app.include_router(session_summary_router)
    logger.info("✅ Session Summary Report loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading Session Summary Report: {e}")

try:
    app.include_router(session_ranking_router)
    logger.info("✅ Session Ranking Report loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading Session Ranking Report: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="10.226.51.33", port=8000, reload=False)