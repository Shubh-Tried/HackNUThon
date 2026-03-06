"""
ml/predict.py — ML prediction for solar inverter risk scoring.

Supports two modes:
  1. **Pickle model** — if a .pkl file is found in backend/ml/, it is loaded
     and used for predictions.
  2. **Heuristic fallback** — if no model file exists, a rule-based risk
     score is calculated from the raw features.

When you have a trained model, drop the .pkl file into backend/ml/ and
restart the server.
"""

import os
import logging
import glob

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to load a pickle / joblib model at import time
# ---------------------------------------------------------------------------
_model = None
_model_path = None

ML_DIR = os.path.dirname(os.path.abspath(__file__))

def _find_and_load_model():
    """Scan the ml/ directory for a .pkl or .joblib file and load it."""
    global _model, _model_path

    for ext in ("*.pkl", "*.joblib"):
        candidates = glob.glob(os.path.join(ML_DIR, ext))
        if candidates:
            path = candidates[0]
            try:
                import joblib
                _model = joblib.load(path)
                _model_path = path
                log.info("Loaded ML model from %s", path)
                return
            except ImportError:
                pass
            try:
                import pickle
                with open(path, "rb") as f:
                    _model = pickle.load(f)
                _model_path = path
                log.info("Loaded ML model (pickle) from %s", path)
                return
            except Exception as exc:
                log.warning("Failed to load model %s: %s", path, exc)

    log.info("No pickle/joblib model found in %s — using heuristic fallback.", ML_DIR)


# Run once on import
_find_and_load_model()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_inverter(data: dict) -> dict:
    """
    Predict risk for an inverter given its feature dict.

    Expected keys (all optional, the function is tolerant):
        inverter_id, power, pv_power, temperature, frequency,
        voltage_ab, voltage_bc, voltage_ca, power_factor,
        op_state, kwh_today, kwh_total

    Returns:
        {"inverter_id": …, "risk_score": float, "status": str, "top_features": [...]}
    """
    inv_id = data.get("inverter_id", "unknown")

    if _model is not None:
        return _predict_with_model(data, inv_id)
    else:
        return _predict_heuristic(data, inv_id)


def _predict_with_model(data: dict, inv_id) -> dict:
    """Run the loaded sklearn / pickle model."""
    import numpy as np

    # Build feature vector in consistent order
    feature_names = [
        "power", "pv_power", "temperature", "frequency",
        "voltage_ab", "voltage_bc", "voltage_ca",
        "power_factor", "op_state", "kwh_today", "kwh_total",
    ]
    features = [float(data.get(f, 0) or 0) for f in feature_names]
    X = np.array([features])

    try:
        # If the model has predict_proba (classifier), use probability
        if hasattr(_model, "predict_proba"):
            proba = _model.predict_proba(X)
            # Assume last class is "high risk"
            risk = float(proba[0][-1])
        else:
            # Regressor — output directly
            risk = float(_model.predict(X)[0])
            risk = max(0.0, min(1.0, risk))
    except Exception as exc:
        log.error("Model prediction error: %s — falling back to heuristic", exc)
        return _predict_heuristic(data, inv_id)

    status = _status_from_risk(risk)
    top_features = _compute_top_features(data)

    return {
        "inverter_id": inv_id,
        "risk_score": round(risk, 3),
        "status": status,
        "top_features": top_features,
        "model": os.path.basename(_model_path) if _model_path else "unknown",
    }


def _predict_heuristic(data: dict, inv_id) -> dict:
    """Rule-based risk estimation when no pickle model is available."""
    risk = 0.2  # baseline

    temp = float(data.get("temperature", 0) or 0)
    power = float(data.get("power", 0) or 0)
    pv_power = float(data.get("pv_power", 0) or 0)
    pf = float(data.get("power_factor", 1.0) or 1.0)
    freq = float(data.get("frequency", 50.0) or 50.0)

    # Temperature penalties
    if temp > 70:
        risk += 0.35
    elif temp > 60:
        risk += 0.2
    elif temp > 50:
        risk += 0.1

    # Low power factor
    if pf < 0.8:
        risk += 0.15
    elif pf < 0.9:
        risk += 0.05

    # Low PV power
    if pv_power < 1.0:
        risk += 0.1

    # Frequency deviation
    if freq < 49.0 or freq > 51.0:
        risk += 0.15
    elif freq < 49.5 or freq > 50.5:
        risk += 0.05

    risk = round(min(1.0, max(0.0, risk)), 3)
    status = _status_from_risk(risk)
    top_features = _compute_top_features(data)

    return {
        "inverter_id": inv_id,
        "risk_score": risk,
        "status": status,
        "top_features": top_features,
        "model": "heuristic",
    }


def _status_from_risk(risk: float) -> str:
    if risk > 0.7:
        return "Critical"
    elif risk > 0.4:
        return "Warning"
    return "Normal"


def _compute_top_features(data: dict) -> list[str]:
    """Determine which features are contributing to elevated risk."""
    features = []
    temp = float(data.get("temperature", 0) or 0)
    pf = float(data.get("power_factor", 1.0) or 1.0)
    pv = float(data.get("pv_power", 0) or 0)
    freq = float(data.get("frequency", 50.0) or 50.0)

    if temp > 60:
        features.append("High temperature")
    if pf < 0.85:
        features.append("Low power factor")
    if pv < 1.0:
        features.append("Low PV power")
    if freq < 49.5 or freq > 50.5:
        features.append("Frequency deviation")
    if not features:
        features.append("All parameters nominal")
    return features