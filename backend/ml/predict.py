"""
ml/predict.py — ML prediction for solar inverter risk scoring.

Uses a two-stage pipeline:
  1. Feature engineering:  raw Supabase data → 22 engineered features
  2. Isolation Forest:     anomaly detection → anomaly flag
  3. XGBoost Classifier:   22 features + anomaly → risk probability

Falls back to a heuristic if any model file fails to load.
"""

import os
import math
import pickle
import logging
import datetime

log = logging.getLogger(__name__)

ML_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Load models at import time
# ---------------------------------------------------------------------------
_feature_names: list[str] = []
_xgb_model = None
_iso_forest = None

# 1. Feature names
_features_path = os.path.join(ML_DIR, "features.pkl")
try:
    with open(_features_path, "rb") as f:
        _feature_names = pickle.load(f)
    print(f"[ML] Loaded {len(_feature_names)} feature names from features.pkl")
except Exception as exc:
    log.warning("Failed to load features.pkl: %s", exc)

# 2. XGBoost model
_xgb_path = os.path.join(ML_DIR, "xgboost_model.pkl")
try:
    with open(_xgb_path, "rb") as f:
        _xgb_model = pickle.load(f)
    print(f"[ML] Loaded XGBoost model from xgboost_model.pkl "
          f"(features: {_xgb_model.n_features_in_})")
except Exception as exc:
    log.warning("Failed to load xgboost_model.pkl: %s", exc)
    print(f"[ML] WARNING: Failed to load XGBoost model: {exc}")

# 3. Isolation Forest (needs joblib due to sklearn version)
_iso_path = os.path.join(ML_DIR, "isolation_forest.pkl")
try:
    import joblib
    _iso_forest = joblib.load(_iso_path)
    print("[ML] Loaded Isolation Forest from isolation_forest.pkl")
except Exception as exc:
    log.warning("Failed to load isolation_forest.pkl: %s", exc)
    print(f"[ML] WARNING: Failed to load Isolation Forest: {exc}")


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def _engineer_features(data: dict) -> list[float]:
    """
    Transform raw Supabase inverter data into the 22 engineered features
    that the models expect.

    Args:
        data: Dict with raw keys from inverter_latest_data table.

    Returns:
        List of 22 floats in the order defined by features.pkl.
    """
    # --- Raw values (with safe defaults) ---
    power = float(data.get("power", 0) or 0)
    pv_power = float(data.get("pv_power", 0) or 0)
    temp = float(data.get("temperature", 0) or 0)
    freq = float(data.get("frequency", 50.0) or 50.0)
    v_ab = float(data.get("voltage_ab", 230) or 230)
    v_bc = float(data.get("voltage_bc", 230) or 230)
    v_ca = float(data.get("voltage_ca", 230) or 230)
    pf = float(data.get("power_factor", 1.0) or 1.0)
    op_state = int(data.get("op_state", 0) or 0)

    now = datetime.datetime.now()
    hour = now.hour

    # --- Derived features ---
    pv_total_power = pv_power
    performance_ratio = (power / pv_power) if pv_power > 0 else 0.0
    ambient_temp = temp * 0.85  # estimate
    temp_stress = temp - ambient_temp
    voltage_diff = max(v_ab, v_bc, v_ca) - min(v_ab, v_bc, v_ca)
    current_diff = (power / max(v_ab, 1.0))  # estimated current

    # Reactive power ratio: Q/P ≈ sqrt(1 - pf²) / pf
    if pf > 0 and pf <= 1.0:
        reactive_ratio = math.sqrt(max(0, 1 - pf * pf)) / pf
    else:
        reactive_ratio = 0.0

    # Rolling stats — estimate realistic values from single snapshot
    # The model was trained with non-zero std and natural power variation
    power_mean_12 = power
    power_std_12 = power * 0.05 if power > 0 else 0.0  # ~5% natural variation
    power_mean_48 = power
    power_std_48 = power * 0.08 if power > 0 else 0.0  # slightly more over 48h

    # Trend features — slight positive trend for running inverters
    if op_state == 1 and power > 0:
        power_trend_12 = 0.01   # slight upward trend (normal)
        power_trend_48 = 0.005  # gentler over 48h
        efficiency_trend = 0.0  # stable efficiency
    else:
        power_trend_12 = -0.02  # declining if stopped
        power_trend_48 = -0.01
        efficiency_trend = -0.01

    # Alarm counts — infer from operating state
    is_alarm = 1 if op_state != 1 else 0
    alarm_count_12 = is_alarm
    alarm_count_48 = is_alarm * 2  # accumulate if stopped

    # Daylight flag
    daylight = 1 if 6 <= hour <= 18 else 0

    # --- Assemble in the exact order from features.pkl ---
    feature_map = {
        "power": power,
        "pv_total_power": pv_total_power,
        "performance_ratio": performance_ratio,
        "temp": temp,
        "ambient_temp": ambient_temp,
        "temp_stress": temp_stress,
        "voltage_diff": voltage_diff,
        "current_diff": current_diff,
        "pf": pf,
        "freq": freq,
        "reactive_ratio": reactive_ratio,
        "power_mean_12": power_mean_12,
        "power_std_12": power_std_12,
        "power_mean_48": power_mean_48,
        "power_std_48": power_std_48,
        "power_trend_12": power_trend_12,
        "power_trend_48": power_trend_48,
        "efficiency_trend": efficiency_trend,
        "alarm_count_12": alarm_count_12,
        "alarm_count_48": alarm_count_48,
        "hour": float(hour),
        "daylight": float(daylight),
    }

    return [feature_map.get(name, 0.0) for name in _feature_names]


# ---------------------------------------------------------------------------
# Prediction pipeline
# ---------------------------------------------------------------------------

def predict_inverter(data: dict) -> dict:
    """
    Predict risk for an inverter given its feature dict.

    Uses the two-stage ML pipeline if models are loaded,
    otherwise falls back to heuristic.

    Returns:
        {"inverter_id": …, "risk_score": float, "status": str,
         "top_features": [...], "model": str}
    """
    inv_id = data.get("inverter_id", "unknown")

    if _xgb_model is not None and _feature_names:
        return _predict_with_models(data, inv_id)
    else:
        return _predict_heuristic(data, inv_id)

def run_batch_predictions_and_log(latest_data: list[dict]):
    """Run `predict_inverter` on a batch of latest data and print the results."""
    print(f"\n--- [ML] Running Batch Predictions ({len(latest_data)} inverters) ---")
    for inv in latest_data:
        try:
            # Map raw fields to what predict_inverter expects if necessary
            input_data = {
                "inverter_id": inv.get("id"),
                "power": inv.get("power", 0),
                "pv_power": inv.get("pv_power", 0),
                "temperature": inv.get("temperature", 0),
                "frequency": inv.get("frequency", 50.0),
                "voltage_ab": inv.get("voltage_ab", 230),
                "voltage_bc": inv.get("voltage_bc", 230),
                "voltage_ca": inv.get("voltage_ca", 230),
                "power_factor": inv.get("power_factor", 1.0),
                "op_state": inv.get("op_state", 1),
                "kwh_today": inv.get("kwh_today", 0),
                "kwh_total": inv.get("kwh_total", 0),
            }
            res = predict_inverter(input_data)
            code = inv.get("inverter_code", f"ID:{res['inverter_id']}")
            print(f"[ML] Inverter {code} | Risk: {res['risk_score']:.3f} | Status: {res['status']} | Features: {', '.join(res['top_features'])}")
        except Exception as e:
            print(f"[ML] Error predicting for inverter {inv.get('inverter_code', 'unknown')}: {e}")
    print("------------------------------------------------------------------\n")


def _predict_with_models(data: dict, inv_id) -> dict:
    """Run the full ML pipeline: features → IsolationForest → XGBoost."""
    import numpy as np

    try:
        # Step 1: Engineer 22 features
        features_22 = _engineer_features(data)
        X_22 = np.array([features_22])

        # Step 2: Isolation Forest anomaly detection
        anomaly = 0
        if _iso_forest is not None:
            iso_pred = _iso_forest.predict(X_22)
            # IsolationForest returns -1 for anomalies, 1 for normal
            anomaly = 1 if iso_pred[0] == -1 else 0

        # Step 3: Append anomaly as 23rd feature for XGBoost
        features_23 = features_22 + [float(anomaly)]
        X_23 = np.array([features_23])

        # Step 4: XGBoost prediction
        if hasattr(_xgb_model, "predict_proba"):
            proba = _xgb_model.predict_proba(X_23)
            # Class 1 = at-risk
            risk = float(proba[0][1])
        else:
            risk = float(_xgb_model.predict(X_23)[0])
            risk = max(0.0, min(1.0, risk))

    except Exception as exc:
        log.error("ML prediction error: %s — falling back to heuristic", exc)
        print(f"[ML] Prediction error: {exc} — using heuristic")
        return _predict_heuristic(data, inv_id)

    status = _status_from_risk(risk)
    top_features = _compute_top_features(data, anomaly)

    return {
        "inverter_id": inv_id,
        "risk_score": round(risk, 3),
        "status": status,
        "top_features": top_features,
        "is_anomaly": bool(anomaly),
        "model": "xgboost_model.pkl",
    }


def _predict_heuristic(data: dict, inv_id) -> dict:
    """Rule-based risk estimation when no pickle model is available."""
    risk = 0.2  # baseline

    temp = float(data.get("temperature", 0) or 0)
    pv_power = float(data.get("pv_power", 0) or 0)
    pf = float(data.get("power_factor", 1.0) or 1.0)
    freq = float(data.get("frequency", 50.0) or 50.0)

    if temp > 70:
        risk += 0.35
    elif temp > 60:
        risk += 0.2
    elif temp > 50:
        risk += 0.1

    if pf < 0.8:
        risk += 0.15
    elif pf < 0.9:
        risk += 0.05

    if pv_power < 1.0:
        risk += 0.1

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _status_from_risk(risk: float) -> str:
    if risk > 0.7:
        return "Critical"
    elif risk > 0.4:
        return "Warning"
    return "Normal"


def _compute_top_features(data: dict, anomaly: int = 0) -> list[str]:
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
    if anomaly:
        features.append("Anomaly detected (Isolation Forest)")
    if not features:
        features.append("All parameters nominal")
    return features