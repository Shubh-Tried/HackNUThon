import React from "react";
import "./GraphsSection.css";
import { Pie, Bar, Radar, Line } from "react-chartjs-2";
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

  // Weekly power generation data
  const today = new Date();
  const weekLabels = Array.from({ length: 7 }).map((_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() - (6 - i));
    return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  });

  const weeklyPowerData = {
    labels: weekLabels,
    datasets: [
      {
        label: "Power Generated (kWh)",
        data: [320, 410, 385, 450, 430, 395, 460],
        borderColor: "#28a745",
        backgroundColor: "rgba(40, 167, 69, 0.1)",
        tension: 0.4,
        fill: true,
        pointRadius: 5,
        pointBackgroundColor: "#28a745",
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
      }
    ]
  };

  const weeklyPowerOptions = {
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: "top" }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: { display: true, text: "kWh", font: { size: 12 } }
      }
    }
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

      <div className="graph-box graph-box-wide">
        <h3>Weekly Power Generation</h3>
        <div style={{ position: "relative", height: "220px", width: "100%" }}>
          <Line data={weeklyPowerData} options={weeklyPowerOptions} />
        </div>
      </div>

    </div>
  );
}

export default GraphsSection;