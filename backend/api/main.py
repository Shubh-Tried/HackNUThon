from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ml.predict import predict_inverter
from genai.explanation_engine import generate_maintenance_ticket
from utils.ticket_generator import generate_ticket
import random
import math

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import json
import os

DASHBOARD_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets", "dashboard.json")

def _load_dashboard_data():
    if not os.path.exists(DASHBOARD_FILE):
        return []
    with open(DASHBOARD_FILE, "r") as f:
        return json.load(f)

def _get_inverter(inverter_id: str):
    data = _load_dashboard_data()
    for d in data:
        if str(d["id"]) == str(inverter_id):
            return d
    return None

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
    return {"message": "Solar Inverter AI API running"}


@app.get("/inverters")
def get_all_inverters():
    """Return summary data for all exact physical inverters."""
    return _load_dashboard_data()


@app.get("/inverter/{inverter_id}")
def get_inverter_detail(inverter_id: str):
    """Return detailed stats + 24 h time-series for one physical inverter."""
    inv = _get_inverter(inverter_id)
    if not inv:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Inverter not found")
        
    summary = dict(inv)
    top_features = []
    if summary.get("temperature", 0) > 60:
        top_features.append("High temperature")
    if summary.get("efficiency", 100) < 88:
        top_features.append("Efficiency drop")
    if summary.get("voltage", 230) > 240 or summary.get("voltage", 230) < 225:
        top_features.append("Voltage fluctuation")
    if summary.get("power_output", 6) < 4:
        top_features.append("Low power output")
    if not top_features:
        top_features.append("All parameters nominal")
    summary["top_features"] = top_features

    return summary


@app.post("/inverter/{inverter_id}/predict")
def predict_inverter_future(inverter_id: str):
    """7-day forecast for a specific physical inverter."""
    import random
    r = random.Random(hash(inverter_id) + 777)
    days = []
    inv = _get_inverter(inverter_id)
    if not inv: return {"inverter_id": inverter_id, "predictions": []}
    
    base_risk = inv["risk_score"]
    for day in range(1, 8):
        risk = round(min(1.0, max(0.0, base_risk + r.uniform(-0.15, 0.2))), 2)
        temp = round(r.uniform(32, 72), 1)
        eff = round(r.uniform(82, 98), 1)
        days.append({
            "day": day,
            "risk_score": risk,
            "status": _status_from_risk(risk),
            "predicted_temperature": temp,
            "predicted_efficiency": eff,
        })
    return {"inverter_id": inverter_id, "predictions": days}


@app.post("/inverter/{inverter_id}/explain")
def explain_inverter(inverter_id: str):
    """Get LLM explanation for a specific physical inverter's condition."""
    inv = _get_inverter(inverter_id)
    if not inv: return {"error": "Inverter not found"}
    summary = dict(inv)

    top_features = []
    if summary.get("temperature", 0) > 60:
        top_features.append("High temperature")
    if summary.get("efficiency", 100) < 88:
        top_features.append("Efficiency drop")
    if summary.get("voltage", 230) > 240 or summary.get("voltage", 230) < 225:
        top_features.append("Voltage fluctuation")
    if summary.get("power_output", 6) < 4:
        top_features.append("Low power output")
    if not top_features:
        top_features.append("All parameters nominal")

    ml_result = {
        "inverter_id": summary["name"],
        "risk_score": summary["risk_score"],
        "status": summary["status"],
        "top_features": top_features,
    }
    explanation = generate_maintenance_ticket(ml_result)
    return {"inverter_id": inverter_id, "name": summary["name"], "explanation": explanation}


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