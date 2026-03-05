import React from "react";
import { useNavigate } from "react-router-dom";

function InverterCard({ inverter }) {
  const navigate = useNavigate();

  return (
    <div 
      onClick={() => navigate(`/inverter/${inverter.id}`)}
      style={{
        border: "1px solid #ccc",
        padding: "20px",
        width: "200px",
        borderRadius: "10px",
        cursor: "pointer",
        boxShadow: "2px 2px 10px rgba(0,0,0,0.1)"
      }}
    >
      <h3>{inverter.name}</h3>
      <p>Power: {inverter.power}</p>
    </div>
  );
}

export default InverterCard;