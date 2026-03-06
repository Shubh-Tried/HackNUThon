import React, { useEffect, useState } from "react";
import "./InverterPopUp.css";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const modalCache = {};

function InverterModal({ inverterId, inverterName, status, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (modalCache[inverterId]) {
      setData(modalCache[inverterId]);
      setLoading(false);
      return;
    }

    const fetchDetail = async () => {
      try {
        const res = await fetch(`${API_BASE}/inverter/${inverterId}`);
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = await res.json();
        modalCache[inverterId] = json;
        setData(json);
      } catch (err) {
        console.error("Failed to fetch inverter detail:", err);
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [inverterId]);

  const getStatusColor = (st) => {
    switch (st) {
      case "Good":
      case "Normal":
        return "#28a745";
      case "Warning":
        return "#ffc107";
      case "Bad":
      case "Critical":
        return "#dc3545";
      default:
        return "#999";
    }
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="modal-container" style={{ textAlign: "center", padding: "60px" }}>
          Loading…
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-container" style={{ "--status-color": getStatusColor(status) }}>
        <div className="modal-header">
          <div className="modal-title-section">
            <h2 className="modal-inverter-name">
              {data.inverter_code || inverterName || `INV-${inverterId}`}
            </h2>
            <span className={`modal-status-badge badge-${status}`}>
              {status || (data.op_state === 1 ? "Online" : "Offline")}
            </span>
          </div>

          <div className="modal-actions">
            <button className="modal-btn analyze-btn">Predict next 7 days</button>
            <button className="modal-btn askai-btn">ASK AI</button>
            <button className="modal-close" onClick={onClose}>✕</button>
          </div>
        </div>

        <div className="modal-stats-row">
          <div className="modal-stat">
            <span>Power</span>
            <strong>{data.power != null ? `${data.power} kW` : "N/A"}</strong>
          </div>
          <div className="modal-stat">
            <span>PV Power</span>
            <strong>{data.pv_power != null ? `${data.pv_power} kW` : "N/A"}</strong>
          </div>
          <div className="modal-stat">
            <span>Temperature</span>
            <strong>{data.temperature != null ? `${data.temperature}°C` : "N/A"}</strong>
          </div>
          <div className="modal-stat">
            <span>Frequency</span>
            <strong>{data.frequency != null ? `${data.frequency} Hz` : "N/A"}</strong>
          </div>
          <div className="modal-stat">
            <span>Power Factor</span>
            <strong>{data.power_factor != null ? data.power_factor.toFixed(3) : "N/A"}</strong>
          </div>
          <div className="modal-stat">
            <span>kWh Today</span>
            <strong>{data.kwh_today != null ? `${data.kwh_today}` : "N/A"}</strong>
          </div>
        </div>

        <div className="modal-stats-row">
          <div className="modal-stat">
            <span>Voltage AB</span>
            <strong>{data.voltage_ab != null ? `${data.voltage_ab} V` : "N/A"}</strong>
          </div>
          <div className="modal-stat">
            <span>Voltage BC</span>
            <strong>{data.voltage_bc != null ? `${data.voltage_bc} V` : "N/A"}</strong>
          </div>
          <div className="modal-stat">
            <span>Voltage CA</span>
            <strong>{data.voltage_ca != null ? `${data.voltage_ca} V` : "N/A"}</strong>
          </div>
          <div className="modal-stat">
            <span>kWh Total</span>
            <strong>{data.kwh_total != null ? `${data.kwh_total}` : "N/A"}</strong>
          </div>
          <div className="modal-stat">
            <span>Op State</span>
            <strong>{data.op_state === 1 ? "Running" : data.op_state === 0 ? "Stopped" : "Unknown"}</strong>
          </div>
        </div>

        {data.top_features && data.top_features.length > 0 && (
          <div style={{ padding: "10px 20px" }}>
            <h4 style={{ margin: "0 0 6px", color: "#aaa" }}>Risk Factors</h4>
            <ul style={{ margin: 0, paddingLeft: "20px", color: "#ddd" }}>
              {data.top_features.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
        )}

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