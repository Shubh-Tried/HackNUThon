from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from ml.predict import predict_inverter
from genai.explanation_engine import generate_maintenance_ticket
from utils.ticket_generator import generate_ticket

app = FastAPI(title="Solar Inverter AI API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Supabase-backed data helpers  (real schema)
# ---------------------------------------------------------------------------
from database.supabase_client import (
    get_cached_latest,
    get_cached_plants,
    get_cached_inverters,
    get_cache_age,
    fetch_one,
    fetch_metrics,
    fetch_string_metrics,
    fetch_latest_data,
)


def _status_from_risk(risk: float) -> str:
    if risk > 0.7:
        return "Critical"
    elif risk > 0.4:
        return "Warning"
    return "Normal"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Solar Inverter AI API running",
        "cache_age_seconds": round(get_cache_age(), 1),
    }


@app.get("/plants")
def get_plants():
    """Return all plants from Supabase."""
    return get_cached_plants()


@app.get("/inverters")
def get_all_inverters():
    """Return latest snapshot for every inverter (from the 5-min cache)."""
    return get_cached_latest()


@app.get("/inverter/{inverter_id}")
def get_inverter_detail(inverter_id: int):
    """Detailed view of one inverter: latest data + recent metrics."""
    # Try cache first for the latest snapshot
    cached = get_cached_latest()
    inv = next((r for r in cached if r.get("id") == inverter_id), None)

    # Fall back to a direct query if not in cache
    if not inv:
        inv = fetch_one("inverter_latest_data", "id", inverter_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Inverter not found")

    # Enrich with recent metrics history
    recent_metrics = fetch_metrics(inverter_id, limit=50)

    # Build a risk-feature list from latest readings
    top_features = []
    if inv.get("temperature", 0) > 60:
        top_features.append("High temperature")
    if inv.get("power_factor", 1.0) < 0.85:
        top_features.append("Low power factor")
    if inv.get("pv_power", 0) < 1.0:
        top_features.append("Low PV power")
    freq = inv.get("frequency", 50.0)
    if freq and (freq < 49.5 or freq > 50.5):
        top_features.append("Frequency deviation")
    if not top_features:
        top_features.append("All parameters nominal")

    return {
        **inv,
        "top_features": top_features,
        "recent_metrics": recent_metrics[:20],  # last 20 readings
    }


@app.get("/inverter/{inverter_id}/metrics")
def get_inverter_metrics(inverter_id: int, limit: int = Query(100, le=500)):
    """Time-series telemetry from `inverter_metrics`."""
    rows = fetch_metrics(inverter_id, limit=limit)
    if not rows:
        raise HTTPException(status_code=404, detail="No metrics found for this inverter")
    return rows


@app.get("/inverter/{inverter_id}/strings")
def get_string_metrics(inverter_id: int, limit: int = Query(50, le=200)):
    """String-level current readings from `string_metrics`."""
    rows = fetch_string_metrics(inverter_id, limit=limit)
    return rows


@app.post("/inverter/{inverter_id}/predict")
def predict_inverter_future(inverter_id: int):
    """Run ML prediction for a specific inverter using latest data."""
    cached = get_cached_latest()
    inv = next((r for r in cached if r.get("id") == inverter_id), None)
    if not inv:
        inv = fetch_one("inverter_latest_data", "id", inverter_id)
    if not inv:
        return {"inverter_id": inverter_id, "prediction": None, "error": "Inverter not found"}

    # Feed real features to the ML model
    ml_input = {
        "inverter_id": inverter_id,
        "power": inv.get("power", 0),
        "pv_power": inv.get("pv_power", 0),
        "temperature": inv.get("temperature", 0),
        "frequency": inv.get("frequency", 0),
        "voltage_ab": inv.get("voltage_ab", 0),
        "voltage_bc": inv.get("voltage_bc", 0),
        "voltage_ca": inv.get("voltage_ca", 0),
        "power_factor": inv.get("power_factor", 0),
        "op_state": inv.get("op_state", 0),
        "kwh_today": inv.get("kwh_today", 0),
        "kwh_total": inv.get("kwh_total", 0),
    }

    result = predict_inverter(ml_input)
    return {
        "inverter_id": inverter_id,
        "inverter_code": inv.get("inverter_code"),
        "prediction": result,
    }


@app.post("/inverter/{inverter_id}/explain")
def explain_inverter(inverter_id: int):
    """Get LLM explanation for a specific inverter's condition."""
    cached = get_cached_latest()
    inv = next((r for r in cached if r.get("id") == inverter_id), None)
    if not inv:
        inv = fetch_one("inverter_latest_data", "id", inverter_id)
    if not inv:
        return {"error": "Inverter not found"}

    top_features = []
    if inv.get("temperature", 0) > 60:
        top_features.append("High temperature")
    if inv.get("power_factor", 1.0) < 0.85:
        top_features.append("Low power factor")
    if inv.get("pv_power", 0) < 1.0:
        top_features.append("Low PV power")
    if not top_features:
        top_features.append("All parameters nominal")

    # Use heuristic risk until pickle model is loaded
    risk = predict_inverter({
        "inverter_id": inverter_id,
        "temperature": inv.get("temperature", 0),
        "power": inv.get("power", 0),
        "power_factor": inv.get("power_factor", 1.0),
        "pv_power": inv.get("pv_power", 0),
    })

    ml_result = {
        "inverter_id": inv.get("inverter_code", str(inverter_id)),
        "risk_score": risk.get("risk_score", 0.5),
        "status": risk.get("status", "Unknown"),
        "top_features": top_features,
    }
    explanation = generate_maintenance_ticket(ml_result)
    return {
        "inverter_id": inverter_id,
        "inverter_code": inv.get("inverter_code"),
        "explanation": explanation,
    }


@app.post("/ask")
def ask_ai(data: dict):
    """RAG-powered Q&A — retrieves relevant inverter data and answers via Gemini."""
    question = data.get("question", "")
    if not question:
        return {"answer": "Please provide a question."}

    try:
        from rag.rag_engine import rag_answer
        answer = rag_answer(question)
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}


@app.post("/predict")
def predict(data: dict):
    # Step 1: ML prediction
    ml_result = predict_inverter(data)
    # Step 2: LLM explanation
    explanation = generate_maintenance_ticket(ml_result)
    # Step 3: Maintenance ticket
    ticket = generate_ticket(ml_result)

    return {
        "inverter_id": ml_result["inverter_id"],
        "risk_score": ml_result["risk_score"],
        "status": ml_result["status"],
        "explanation": explanation,
        "maintenance_ticket": ticket,
    }