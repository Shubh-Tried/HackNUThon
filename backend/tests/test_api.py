"""Tests for core API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_dashboard_summary():
    response = client.get("/dashboard-summary")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["summary"]["total_inverters"] > 0


def test_list_inverters():
    response = client.get("/inverters")
    assert response.status_code == 200
    data = response.json()
    assert "inverters" in data
    assert data["total"] > 0


def test_list_inverters_filter_block():
    response = client.get("/inverters?block=A")
    assert response.status_code == 200
    data = response.json()
    for inv in data["inverters"]:
        assert inv["block"] == "A"


def test_get_inverter():
    response = client.get("/inverters/INV-101")
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["inverter_id"] == "INV-101"


def test_get_inverter_not_found():
    response = client.get("/inverters/INV-999")
    assert response.status_code == 404


def test_get_inverter_metrics():
    response = client.get("/inverters/INV-101/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "dc_voltage" in data
    assert "temperature" in data
    assert len(data["dc_voltage"]) > 0


def test_predict():
    payload = {
        "inverter_id": "INV-TEST",
        "telemetry": {
            "dc_voltage": 520.0,
            "ac_voltage": 230.0,
            "current": 20.5,
            "power_output": 30750.0,
            "temperature": 65.0,
            "efficiency": 91.2,
            "daily_generation": 172.3,
            "inverter_runtime": 24000.0,
            "alarm_frequency": 8
        }
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_category" in data
    assert "top_feature_contributions" in data
    assert "genai_summary" in data
    assert len(data["top_feature_contributions"]) <= 5


def test_predict_invalid_input():
    payload = {
        "telemetry": {
            "dc_voltage": -100,  # Invalid: below 0
            "ac_voltage": 230.0,
            "current": 20.0,
            "power_output": 30000.0,
            "temperature": 50.0,
            "efficiency": 95.0,
            "daily_generation": 200.0,
            "inverter_runtime": 20000.0,
            "alarm_frequency": 2
        }
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422  # Validation error


def test_alerts():
    response = client.get("/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert data["total"] > 0


def test_alerts_by_inverter():
    response = client.get("/alerts?inverter_id=INV-203")
    assert response.status_code == 200
    data = response.json()
    for alert in data["alerts"]:
        assert alert["inverter_id"] == "INV-203"


def test_qa():
    payload = {"question": "Which inverters have elevated risk?"}
    response = client.post("/qa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "confidence" in data
