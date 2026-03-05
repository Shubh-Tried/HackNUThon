"""
Solar Inverter Failure Prediction & Intelligence Platform
FastAPI Application Entry Point
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import health, dashboard, inverters, predict, alerts, qa

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Solar Inverter Failure Prediction API",
    description="AI-driven platform for predicting solar inverter failures and providing operational intelligence.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(inverters.router)
app.include_router(predict.router)
app.include_router(alerts.router)
app.include_router(qa.router)


@app.on_event("startup")
async def startup_event():
    """Initialize ML pipeline on startup."""
    logger.info("Starting Solar Inverter Prediction API...")
    
    # Pre-load ML pipeline
    from app.ml.pipeline import get_pipeline
    pipeline = get_pipeline()
    logger.info(f"ML Pipeline loaded. Metrics: {pipeline.metrics}")
    
    # Check for OpenAI API key
    if os.getenv("OPENAI_API_KEY"):
        logger.info("OpenAI API key detected — GenAI insights will use LLM.")
    else:
        logger.info("No OpenAI API key — GenAI insights will use template-based generation.")
    
    logger.info("API ready.")
