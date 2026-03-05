"""Prediction router."""

from fastapi import APIRouter, HTTPException
from app.schemas.requests import PredictRequest
from app.ml.predictor import predict_risk
from app.genai.insight_engine import generate_insight
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Prediction"])


@router.post("/predict")
async def predict(request: PredictRequest):
    """
    Predict inverter failure risk from telemetry data.
    Returns risk score, category, feature contributions, and GenAI summary.
    """
    try:
        telemetry_dict = request.telemetry.model_dump()
        
        # Run ML prediction
        result = predict_risk(telemetry_dict, request.inverter_id)
        
        # Generate GenAI insight
        genai_summary = await generate_insight(
            inverter_id=request.inverter_id or "Unknown",
            risk_score=result["risk_score"],
            risk_category=result["risk_category"],
            feature_contributions=result["top_feature_contributions"],
            telemetry=telemetry_dict
        )
        
        return {
            "inverter_id": result["inverter_id"],
            "risk_score": result["risk_score"],
            "risk_category": result["risk_category"],
            "top_feature_contributions": result["top_feature_contributions"],
            "genai_summary": genai_summary,
        }
    
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
