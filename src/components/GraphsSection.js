import React from "react";
import "./GraphsSection.css";
import { Pie, Bar, Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler
} from "chart.js";

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler
);

function GraphsSection() {

  const inverterStatusData = {
    labels: ["Good: 4", "Warning: 2", "Critical: 1"],
    datasets: [
      {
        label: "Inverter Status",
        data: [4, 2, 1],
        backgroundColor: [
          "#28a745",
          "#ffc107",
          "#dc3545"
        ]
      }
    ]
  };

  const shutdownRiskData = {
    labels: ["Safe", "Risk of Shutdown"],
    datasets: [
      {
        label: "Shutdown Risk (Next 7 Days)",
        data: [5, 2],
        backgroundColor: [
          "#007bff",
          "#ff5733"
        ]
      }
    ]
  };

  const featureImportance = {
    labels: ["Temperature", "Voltage Var", "Frequency Dev", "Power Factor", "Efficiency Loss"],
    datasets: [
      {
        label: "Current ML Feature Weights",
        data: [0.85, 0.45, 0.60, 0.30, 0.70],
        backgroundColor: "rgba(0, 123, 255, 0.2)",
        borderColor: "rgba(0, 123, 255, 1)",
        borderWidth: 2,
        pointBackgroundColor: "rgba(0, 123, 255, 1)",
      }
    ]
  };

  return (
    <div className="graphs-section">

      <div className="graph-box">
        <h3>Inverter Health Overview</h3>
        <div style={{ position: "relative", height: "180px", width: "100%" }}>
          <Pie data={inverterStatusData} options={{ maintainAspectRatio: false }} />
        </div>
      </div>

      <div className="graph-box">
        <h3>Shutdown Risk Prediction</h3>
        <div style={{ position: "relative", height: "180px", width: "100%" }}>
          <Bar data={shutdownRiskData} options={{ maintainAspectRatio: false }} />
        </div>
      </div>

      <div className="graph-box">
        <h3>ML Model Feature Dominance</h3>
        <div style={{ position: "relative", height: "180px", width: "100%" }}>
          <Radar data={featureImportance} options={{ maintainAspectRatio: false }} />
        </div>
      </div>

    </div>
  );
}

export default GraphsSection;