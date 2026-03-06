def predict_inverter(data):

    # Example prediction
    return {
        "inverter_id": data["inverter_id"],
        "risk_score": 0.78,
        "status": "High Risk",
        "top_features": [
            "High temperature",
            "Efficiency drop",
            "Voltage fluctuation"
        ]
    }