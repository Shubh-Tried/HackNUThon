import React, { useEffect, useState } from "react";
import "./InverterPopUp.css";

const inverterCache = {}; // simple cache

function InverterModal({ inverterId, inverterName, status, onClose }) {
  const [data, setData] = useState(null);

  useEffect(() => {

    // if cached use it
    if (inverterCache[inverterId]) {
      setData(inverterCache[inverterId]);
      return;
    }

    // simulate API fetch
    const dummyData = {
      risk: "57%",
      temperature: "64.3°C",
      efficiency: "98.3%",
      power: "7.66 kW",
      dcVoltage: "495.9 V",
      acVoltage: "232 V"
    };

    inverterCache[inverterId] = dummyData;
    setData(dummyData);

  }, [inverterId]);

  const getStatusColor = (status) => {
    switch(status){
        case "Good":
        return "#28a745";
        case "Warning":
        return "#ffc107";
        case "Bad":
        return "#dc3545";
        default:
        return "#999";
    }
    };

  if (!data) return null;

  return (
    <div className="modal-overlay">

        <div className="modal-container" style={{ "--status-color": getStatusColor(status) }}>

        <div className="modal-header">

            <div className="modal-title-section">
            <h2 className="modal-inverter-name">{inverterName}</h2>
            <span className={`modal-status-badge badge-${status}`}>
                {status}
            </span>
            </div>

            <div className="modal-actions">

            <button className="modal-btn analyze-btn">
                Predict next 7 days
            </button>

            <button className="modal-btn askai-btn">
                ASK AI
            </button>

            <button className="modal-close" onClick={onClose}>
                ✕
            </button>

            </div>

        </div>


        <div className="modal-stats-row">

            <div className="modal-stat">
            <span>Risk Score</span>
            <strong>{data.risk}</strong>
            </div>

            <div className="modal-stat">
            <span>Temperature</span>
            <strong>{data.temperature}</strong>
            </div>

            <div className="modal-stat">
            <span>Efficiency</span>
            <strong>{data.efficiency}</strong>
            </div>

            <div className="modal-stat">
            <span>Power Output</span>
            <strong>{data.power}</strong>
            </div>

            <div className="modal-stat">
            <span>DC Voltage</span>
            <strong>{data.dcVoltage}</strong>
            </div>

            <div className="modal-stat">
            <span>AC Voltage</span>
            <strong>{data.acVoltage}</strong>
            </div>

        </div>


        <div className="modal-charts">

            <div className="chart-card">
            <h3>Temperature (past 7 days)</h3>
            <div className="graph-placeholder"></div>
            </div>

            <div className="chart-card">
            <h3>Voltage (past 7 days)</h3>
            <div className="graph-placeholder"></div>
            </div>

            <div className="chart-card">
            <h3>Efficiency</h3>
            <div className="graph-placeholder"></div>
            </div>

            <div className="chart-card">
            <h3>7-Day Risk Prediction</h3>
            <div className="graph-placeholder"></div>
            </div>

        </div>

        </div>

    </div>
    );
}

export default InverterModal;