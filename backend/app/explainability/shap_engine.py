"""
SHAP-based explainability for inverter failure predictions.
Returns the top 5 most important features contributing to a prediction.
"""

import numpy as np
import pandas as pd
import shap
import logging
from app.ml.pipeline import get_pipeline, engineer_features, FEATURE_COLUMNS, build_training_data

logger = logging.getLogger(__name__)


def get_shap_explanations(telemetry_dict: dict, top_n: int = 5) -> list:
    """
    Compute SHAP values for a single prediction and return top N
    feature contributions with direction of impact.
    """
    pipeline = get_pipeline()
    
    # Prepare input
    df = pd.DataFrame([telemetry_dict])
    X_input = engineer_features(df)
    
    # Build background data for SHAP
    bg_df = build_training_data()
    X_background = engineer_features(bg_df)
    
    try:
        explainer = shap.TreeExplainer(pipeline.model)
        shap_values = explainer.shap_values(X_input)
        
        # For multi-class, shap_values is a list of arrays.
        # Sum absolute SHAP values across classes for overall importance.
        if isinstance(shap_values, list):
            combined = np.sum([np.abs(sv) for sv in shap_values], axis=0)[0]
            # Use class with highest predicted probability for direction
            pred_class = int(pipeline.model.predict(X_input)[0])
            direction_values = shap_values[pred_class][0]
        else:
            combined = np.abs(shap_values[0])
            direction_values = shap_values[0]
        
        feature_names = list(X_input.columns)
        
        # Sort by absolute importance
        indices = np.argsort(combined)[::-1][:top_n]
        
        contributions = []
        for idx in indices:
            contributions.append({
                "feature": feature_names[idx],
                "importance": round(float(combined[idx]), 4),
                "direction": "increasing_risk" if direction_values[idx] > 0 else "decreasing_risk"
            })
        
        return contributions
    
    except Exception as e:
        logger.warning(f"SHAP computation failed, using feature importances: {e}")
        # Fallback to model feature importances
        importances = pipeline.model.feature_importances_
        feature_names = list(X_input.columns)
        indices = np.argsort(importances)[::-1][:top_n]
        
        return [
            {
                "feature": feature_names[idx],
                "importance": round(float(importances[idx]), 4),
                "direction": "contributing"
            }
            for idx in indices
        ]
