import React from "react";
import { useParams } from "react-router-dom";

function InverterDetail() {
  const { id } = useParams();

  // Normally you'd fetch data using id
  return (
    <div style={{ padding: "40px" }}>
      <h2>Inverter Details</h2>
      <p>Showing full details for inverter ID: {id}</p>
      <p>Here you can show voltage, temperature, efficiency, etc.</p>
    </div>
  );
}

export default InverterDetail;