import React from "react";
import { useNavigate } from "react-router-dom";

function InverterCard({ inverter }) {
  const navigate = useNavigate();

  const statusColor =
    inverter.op_state === 1
      ? "#28a745"
      : inverter.op_state === 0
        ? "#dc3545"
        : "#ffc107";

  return (
    <div
      onClick={() => navigate(`/inverter/${inverter.id || inverter.inverter_id}`)}
      style={{
        border: "1px solid #333",
        padding: "20px",
        width: "220px",
        borderRadius: "12px",
        cursor: "pointer",
        background: "#1a1a2e",
        color: "#eee",
        boxShadow: "0 2px 12px rgba(0,0,0,0.3)",
        transition: "transform 0.15s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.03)")}
      onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
    >
      <h3 style={{ margin: "0 0 8px" }}>
        {inverter.inverter_code || inverter.name || `INV-${inverter.id}`}
      </h3>
      <p style={{ margin: "4px 0", fontSize: "14px" }}>
        Power: <strong>{inverter.power != null ? `${inverter.power} kW` : "N/A"}</strong>
      </p>
      <p style={{ margin: "4px 0", fontSize: "14px" }}>
        Temp: <strong>{inverter.temperature != null ? `${inverter.temperature}°C` : "N/A"}</strong>
      </p>
      <p style={{ margin: "4px 0", fontSize: "14px" }}>
        PF: <strong>{inverter.power_factor != null ? inverter.power_factor.toFixed(2) : "N/A"}</strong>
      </p>
      <div
        style={{
          marginTop: "10px",
          padding: "4px 10px",
          borderRadius: "6px",
          background: statusColor,
          display: "inline-block",
          fontSize: "12px",
          fontWeight: 600,
        }}
      >
        {inverter.op_state === 1 ? "Online" : inverter.op_state === 0 ? "Offline" : "Unknown"}
      </div>
    </div>
  );
}

export default InverterCard;