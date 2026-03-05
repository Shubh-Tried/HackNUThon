"""
Prediction service: wraps the ML pipeline and SHAP explainability.
"""

from app.ml.pipeline import get_pipeline
from app.explainability.shap_engine import get_shap_explanations
from app.models.inverter import PredictionResult, FeatureContribution, RiskCategory


def predict_risk(telemetry_dict: dict, inverter_id: str = None) -> dict:
    """
    Run prediction on telemetry data and return risk assessment
    with feature contributions.
    """
    pipeline = get_pipeline()
    result = pipeline.predict(telemetry_dict)
    
    # Get SHAP-based feature contributions
    contributions = get_shap_explanations(telemetry_dict)
    
    return {
        "inverter_id": inverter_id,
        "risk_score": result["risk_score"],
        "risk_category": result["risk_category"],
        "class_probabilities": result["class_probabilities"],
        "top_feature_contributions": contributions
    }
