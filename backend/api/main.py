from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from ml.predict import predict_inverter
from genai.explanation_engine import generate_maintenance_ticket

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


@app.get("/dashboard-stats")
def get_dashboard_stats():
    """
    Aggregated statistics for the dashboard charts.
    All data is computed from real Supabase data — no hardcoded values.
    """
    from collections import Counter
    import datetime

    cached = get_cached_latest()
    
    # Deduplicate cached inverters by inverter_code
    unique_inverters = []
    seen_codes = set()
    for inv in cached:
        code = inv.get("inverter_code")
        if code and code not in seen_codes:
            seen_codes.add(code)
            unique_inverters.append(inv)

    # --- 1. Inverter Health Overview (pie chart) ---
    status_counts = Counter()
    risk_scores = []
    feature_accum = {
        "Temperature": [],
        "Voltage Var": [],
        "Frequency Dev": [],
        "Power Factor": [],
        "Efficiency Loss": [],
    }

    for inv in unique_inverters:
        # Compute risk via heuristic/ML
        try:
            ml_result = predict_inverter({
                "inverter_id": inv.get("id"),
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
            })
            risk = ml_result.get("risk_score", 0.2)
        except Exception:
            risk = 0.2

        status = _status_from_risk(risk)
        status_counts[status] += 1
        risk_scores.append(risk)

        # Feature importance signals
        temp = float(inv.get("temperature", 0) or 0)
        freq = float(inv.get("frequency", 50.0) or 50.0)
        pf = float(inv.get("power_factor", 1.0) or 1.0)
        pv = float(inv.get("pv_power", 0) or 0)

        feature_accum["Temperature"].append(min(1.0, temp / 80.0) if temp > 0 else 0)
        v_ab = float(inv.get("voltage_ab", 230) or 230)
        v_bc = float(inv.get("voltage_bc", 230) or 230)
        v_ca = float(inv.get("voltage_ca", 230) or 230)
        v_var = abs(v_ab - v_bc) + abs(v_bc - v_ca) + abs(v_ca - v_ab)
        feature_accum["Voltage Var"].append(min(1.0, v_var / 30.0))
        feature_accum["Frequency Dev"].append(min(1.0, abs(freq - 50.0) / 2.0))
        feature_accum["Power Factor"].append(max(0, 1.0 - pf))
        power = float(inv.get("power", 0) or 0)
        pv_p = float(inv.get("pv_power", 0) or 0)
        eff_loss = 1.0 - (power / pv_p) if pv_p > 0 else 0.5
        feature_accum["Efficiency Loss"].append(min(1.0, max(0, eff_loss)))

    health = {
        "good": status_counts.get("Normal", 0),
        "warning": status_counts.get("Warning", 0),
        "critical": status_counts.get("Critical", 0),
    }

    # --- 2. Shutdown Risk (bar chart) ---
    safe_count = sum(1 for r in risk_scores if r <= 0.4)
    at_risk_count = sum(1 for r in risk_scores if r > 0.4)

    shutdown_risk = {"safe": safe_count, "at_risk": at_risk_count}

    # --- 3. Feature Dominance (radar chart) ---
    feature_dominance = {}
    for feat, vals in feature_accum.items():
        feature_dominance[feat] = round(sum(vals) / len(vals), 2) if vals else 0

    # --- 4. Weekly Power Generation (line chart) ---
    weekly_power = []
    
    # Use real historical data for the weekly power chart
    from database.supabase_client import fetch_all
    try:
        # Fetch up to 5000 recent metrics to cover the past few days across all inverters
        metric_query = fetch_all("inverter_latest_data", {"order": "timestamp.desc", "limit": "5000"})
        daily_kwh = {}
        
        for r in metric_query:
            if not r.get("timestamp"): continue
            # Handle possible 'Z' at the end of ISO format
            ts = r["timestamp"].replace('Z', '+00:00')
            try:
                dt = datetime.datetime.fromisoformat(ts)
            except ValueError:
                continue
                
            day_str = dt.strftime("%Y-%m-%d")
            inv_id = r.get("inverter_code")
            if not inv_id: continue
            
            kwh = float(r.get("kwh_today", 0) or 0)
            
            if day_str not in daily_kwh:
                daily_kwh[day_str] = {}
                
            if inv_id not in daily_kwh[day_str] or kwh > daily_kwh[day_str][inv_id]:
                daily_kwh[day_str][inv_id] = kwh
                
        # Sort days chronologically
        sorted_days = sorted(daily_kwh.keys())
        
        # Take the last 7 available days
        for day_str in sorted_days[-7:]:
            dt = datetime.datetime.strptime(day_str, "%Y-%m-%d")
            label = dt.strftime("%a, %b %d")
            total_kwh = sum(daily_kwh[day_str].values())
            weekly_power.append({"label": label, "value": round(total_kwh, 1)})
            
    except Exception as e:
        print(f"Error computing weekly power dynamically: {e}")
        # Fallback to static if the dynamic calculation fails
        today = datetime.date.today()
        for i in range(6, -1, -1):
            day = today - datetime.timedelta(days=i)
            label = day.strftime("%a, %b %d")
            # For fallback, sum kwh_today across unique inverters
            total_kwh = sum(float(inv.get("kwh_today", 0) or 0) for inv in unique_inverters)
    return {
        "health": health,
        "shutdown_risk": shutdown_risk,
        "feature_dominance": feature_dominance,
        "weekly_power": weekly_power,
        "total_inverters": len(unique_inverters),
    }


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

    inverter_code = inv.get("inverter_code")
    if not inverter_code:
        raise HTTPException(status_code=404, detail="Inverter code not found")

    # Enrich with recent metrics history using the true inverter_code
    recent_metrics = fetch_metrics(inverter_code, limit=50)

    # Build a risk-feature list from latest readings
    top_features = []
    if (inv.get("temperature") or 0) > 60:
        top_features.append("High temperature")
    if (inv.get("power_factor") or 1.0) < 0.85:
        top_features.append("Low power factor")
    if (inv.get("pv_power") or 0) < 1.0:
        top_features.append("Low PV power")
    freq = inv.get("frequency") or 50.0
    if freq < 49.5 or freq > 50.5:
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
    cached = get_cached_latest()
    inv = next((r for r in cached if r.get("id") == inverter_id), None)
    if not inv:
        inv = fetch_one("inverter_latest_data", "id", inverter_id)
    
    inverter_code = inv.get("inverter_code")
    if not inverter_code:
        raise HTTPException(status_code=404, detail="Inverter code not found")

    rows = fetch_metrics(inverter_code, limit=limit)
    if not rows:
        raise HTTPException(status_code=404, detail="No metrics found for this inverter")
    return rows


@app.get("/inverter/{inverter_id}/strings")
def get_string_metrics(inverter_id: int, limit: int = Query(50, le=200)):
    """String-level current readings from `string_metrics`."""
    cached = get_cached_latest()
    inv = next((r for r in cached if r.get("id") == inverter_id), None)
    if not inv:
        inv = fetch_one("inverter_latest_data", "id", inverter_id)
        
    true_inv_id = inverter_id
    if inv and inv.get("inverter_code"):
        cached_invs = get_cached_inverters()
        match = next((r for r in cached_invs if r.get("inverter_code") == inv.get("inverter_code")), None)
        if match and "inverter_id" in match:
            true_inv_id = match["inverter_id"]
            
    rows = fetch_string_metrics(true_inv_id, limit=limit)
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


@app.get("/inverter/{inverter_id}/ai-summary")
def get_inverter_ai_summary(inverter_id: int):
    """Generate an AI-powered plain-English explanation of an inverter's statistics."""
    # Get inverter data
    cached = get_cached_latest()
    inv = next((r for r in cached if r.get("id") == inverter_id), None)
    if not inv:
        inv = fetch_one("inverter_latest_data", "id", inverter_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Inverter not found")

    inv_code = inv.get("inverter_code", str(inverter_id))

    # Build a targeted question for the RAG engine
    question = (
        f"Give me a detailed analysis of inverter {inv_code} (ID: {inverter_id}). "
        f"Explain its current operating status, power output, temperature, "
        f"voltage readings, frequency, power factor, and energy generation. "
        f"Highlight any concerns or risk factors in plain English. "
        f"Also provide a brief recommendation on whether any maintenance action is needed."
    )

    try:
        from rag.rag_engine import rag_answer
        summary = rag_answer(question)
        return {"inverter_id": inverter_id, "inverter_code": inv_code, "summary": summary}
    except Exception as e:
        return {"inverter_id": inverter_id, "summary": f"Unable to generate AI summary: {str(e)}"}


@app.post("/predict")
def predict(data: dict):
    # Step 1: ML prediction
    ml_result = predict_inverter(data)
    # Step 2: LLM explanation
    explanation = generate_maintenance_ticket(ml_result)

    return {
        "inverter_id": ml_result["inverter_id"],
        "risk_score": ml_result["risk_score"],
        "status": ml_result["status"],
        "explanation": explanation,
        "maintenance_ticket": explanation,
    }
