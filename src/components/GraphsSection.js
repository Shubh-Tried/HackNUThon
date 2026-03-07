import React, { useState, useEffect } from "react";
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

const API_BASE = "http://localhost:8000";

function GraphsSection() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${API_BASE}/dashboard-stats`);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (err) {
        console.error("Failed to fetch dashboard stats:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="graphs-section">
        <div className="graph-box" style={{ display: "flex", alignItems: "center", justifyContent: "center", gridColumn: "1 / -1" }}>
          <p style={{ color: "#888", fontSize: "16px" }}>Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="graphs-section">
        <div className="graph-box" style={{ display: "flex", alignItems: "center", justifyContent: "center", gridColumn: "1 / -1" }}>
          <p style={{ color: "#dc3545", fontSize: "16px" }}>Failed to load dashboard data. Is the backend running?</p>
        </div>
      </div>
    );
  }

  const { health, shutdown_risk, feature_dominance, weekly_power } = stats;

  const inverterStatusData = {
    labels: [
      `Good: ${health.good}`,
      `Warning: ${health.warning}`,
      `Critical: ${health.critical}`
    ],
    datasets: [
      {
        label: "Inverter Status",
        data: [health.good, health.warning, health.critical],
        backgroundColor: ["#28a745", "#ffc107", "#dc3545"]
      }
    ]
  };

  const shutdownRiskData = {
    labels: ["Safe", "Risk of Shutdown"],
    datasets: [
      {
        label: "Shutdown Risk (Next 7 Days)",
        data: [shutdown_risk.safe, shutdown_risk.at_risk],
        backgroundColor: ["#007bff", "#ff5733"]
      }
    ]
  };

  const featureLabels = Object.keys(feature_dominance);
  const featureValues = Object.values(feature_dominance);

  const featureImportance = {
    labels: featureLabels,
    datasets: [
      {
        label: "Current ML Feature Weights",
        data: featureValues,
        backgroundColor: "rgba(0, 123, 255, 0.2)",
        borderColor: "rgba(0, 123, 255, 1)",
        borderWidth: 2,
        pointBackgroundColor: "rgba(0, 123, 255, 1)",
      }
    ]
  };

  const weeklyPowerData = {
    labels: weekly_power.map(wp => wp.label),
    datasets: [
      {
        label: "Power Generated (kWh)",
        data: weekly_power.map(wp => wp.value),
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