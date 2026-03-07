import React, { useState, useEffect, useRef } from "react";
import "./Home.css";
import InverterPopUp from "../../components/InverterPopUp";
import GraphsSection from "../../components/GraphsSection";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

function Home() {
  const [inverters, setInverters] = useState([]);
  const [plants, setPlants] = useState([]);
  const [selected, setSelected] = useState(null);
  const detailRef = useRef(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [activeInverter, setActiveInverter] = useState(null);
  const [aiInsight, setAiInsight] = useState("Loading AI analysis...");
  const [metricsCache, setMetricsCache] = useState({});
  const [currentMetrics, setCurrentMetrics] = useState([]);

  const API_BASE = "http://localhost:8000";

  useEffect(() => {
    const fetchData = async () => {
      try {
        const invRes = await fetch(`${API_BASE}/inverters`);
        let invData = await invRes.json();

        const plantsRes = await fetch(`${API_BASE}/plants`);
        let plantsData = await plantsRes.json();

        if (!Array.isArray(plantsData)) plantsData = [];
        if (!Array.isArray(invData)) invData = [];

        // Fetch predictions to determine risk scores
        const predictions = await Promise.all(
          invData.map((inv) =>
            fetch(`${API_BASE}/inverter/${inv.id}/predict`, { method: "POST" })
              .then((res) => res.json())
              .catch(() => ({ prediction: { risk_score: 0.1, status: "Normal" } }))
          )
        );

        invData = invData.map((inv, index) => {
          const risk = predictions[index]?.prediction?.risk_score || parseFloat(inv.risk_score) || 0.1;
          const status = predictions[index]?.prediction?.status || "Normal";

          return {
            ...inv,
            name: inv.inverter_code || `Inverter ${inv.id}`,
            powerVal: (inv.power || inv.pv_power || 0).toFixed(1) + "kW",
            voltageVal: (inv.voltage_ab || 230).toFixed(1) + "V",
            tempVal: (inv.temperature || 35).toFixed(1) + "°C",
            kwhTotalVal: (inv.kwh_total || 0).toLocaleString() + " kWh",
            gridStatus: status,
            risk_score: risk,
            plant_id: inv.plant_id || plantsData[0].plant_id || 1,
            power: (inv.power || inv.pv_power || 0),
          };
        });

        setInverters(invData);
        setPlants(plantsData);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    fetchData();
  }, []);

  useEffect(() => {
    if (selected && detailRef.current) {
      detailRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });

      // Fetch 7-day metrics
      const fetchMetrics = async () => {
        if (metricsCache[selected.id]) {
          setCurrentMetrics(metricsCache[selected.id]);
          return;
        }

        try {
          let data = [];
          try {
            const res = await fetch(`${API_BASE}/inverter/${selected.id}/metrics?limit=7`);
            if (res.ok) {
              const result = await res.json();
              if (result && result.length > 0) {
                // reverse to get chronological
                data = result.reverse();
              }
            }
          } catch (e) { }

          setMetricsCache(prev => ({ ...prev, [selected.id]: data }));
          setCurrentMetrics(data);
        } catch (error) {
          console.error("Error fetching metrics:", error);
        }
      };

      fetchMetrics();
    }
  }, [selected]);

  const handleClick = (inv) => {
    if (selected && selected.id === inv.id) {
      setSelected(null);
      return;
    }
    setSelected(inv);
    setAiInsight("");
  };

  const openAiInsights = async () => {
    if (!selected) return;
    setAiInsight("Analyzing inverter data... please wait.");

    try {
      const res = await fetch(`${API_BASE}/inverter/${selected.id}/explain`, {
        method: "POST"
      });
      const result = await res.json();
      if (result.explanation) {
        setAiInsight(result.explanation);
      } else {
        setAiInsight("AI explanation is currently unavailable.");
      }
    } catch (error) {
      console.error("Explain error:", error);
      setAiInsight("Error communicating with AI engine.");
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "Good":
      case "Normal":
        return "#28a745";
      case "Bad":
      case "Critical":
        return "#dc3545";
      case "Warning":
        return "#ffc107";
      default:
        return "#cccccc";
    }
  };

  // Grouping and sorting
  const groupedInverters = plants.map((plant) => {
    const plantInverters = inverters.filter((inv) => inv.plant_id === plant.plant_id || inv.plant_id === plant.id);

    // Deduplicate by inverter name
    const uniqueInverters = [];
    const seenNames = new Set();

    for (const inv of plantInverters) {
      if (!seenNames.has(inv.name)) {
        seenNames.add(inv.name);
        uniqueInverters.push(inv);
      }
    }

    return {
      ...plant,
      inverters: uniqueInverters.sort((a, b) => b.risk_score - a.risk_score),
    };
  }).filter(p => p.inverters.length > 0);

  // Summary stats
  const uniqueOverall = [];
  const uniqueNames = new Set();
  for (const inv of inverters) {
    if (!uniqueNames.has(inv.name)) {
      uniqueNames.add(inv.name);
      uniqueOverall.push(inv);
    }
  }

  const totalInverters = uniqueOverall.length;
  const activeInvs = uniqueOverall.filter((i) => i.gridStatus !== "Critical").length;
  const atRisk = uniqueOverall.filter((i) => i.gridStatus !== "Normal").length;
  const totalPower = uniqueOverall.reduce((acc, inv) => acc + (inv.power || 0), 0);

  const handleFetchNextData = async () => {
    try {
      alert("Fetching next data and running ML models. Please wait...");
      const res = await fetch(`${API_BASE}/refresh-data`, { method: "POST" });
      if (res.ok) {
        window.location.reload();
      }
    } catch (e) {
      console.error(e);
      alert("Failed to fetch fresh data");
    }
  };

  return (
    <div className="home">
      <GraphsSection />

      <div style={{ display: "flex", justifyContent: "flex-end", padding: "10px 40px" }}>
        <button onClick={handleFetchNextData} style={{ padding: "12px 24px", background: "#ff8c00", color: "#fff", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: "bold", fontSize: "16px", boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
          Fetch Next Data (ML Refresh)
        </button>
      </div>

      {/* Summary Dashboard */}
      <div className="summary-dashboard">
        <div className="summary-card">
          <h4>Total Inverters</h4>
          <p>{totalInverters}</p>
        </div>
        <div className="summary-card">
          <h4>Active</h4>
          <p>{activeInvs}</p>
        </div>
        <div className="summary-card">
          <h4>At Risk (7-10 days)</h4>
          <p>{atRisk}</p>
        </div>
        <div className="summary-card">
          <h4>Total Power</h4>
          <p>{totalPower.toFixed(2)} kW</p>
        </div>
      </div>

      <div className="plants-container">
        {groupedInverters.map((plant) => (
          <div key={plant.plant_id || plant.id} className="plant-section">
            <h2 className="plant-title">{plant.name || `Plant ${plant.plant_id}`}</h2>
            <div className="cards-container">
              {plant.inverters.map((inv) => (
                <div
                  key={inv.id}
                  className={`small-info-cards status-${inv.gridStatus} ${selected?.id === inv.id ? "selected" : ""
                    }`}
                  onClick={() => handleClick(inv)}
                  style={{
                    borderColor: getStatusColor(inv.gridStatus),
                  }}
                >
                  <h3>{inv.name}</h3>
                  <p>Power: {inv.powerVal}</p>
                  <p>Temp: {inv.tempVal}</p>
                  <p>Energy: {inv.kwhTotalVal}</p>
                  <p style={{ color: getStatusColor(inv.gridStatus), fontWeight: 'bold' }}>
                    Status: {inv.gridStatus === "Critical" ? "Bad" : inv.gridStatus} ({(inv.risk_score * 100).toFixed(1)}%)
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {selected && (
        <div
          className={`status-card ${selected.gridStatus}`}
          ref={detailRef}
          style={{
            borderColor: getStatusColor(selected.gridStatus),
            "--status-color": getStatusColor(selected.gridStatus),
          }}
        >
          <div id="top-slide">
            <h2>{selected.name} - Full Details</h2>
            <div className="ai-help" onClick={openAiInsights}>
              ASK AI
            </div>
          </div>

          {aiInsight && (
            <div className="ai-insight-box" style={{
              marginTop: "20px",
              padding: "15px",
              backgroundColor: "#f4f7f6",
              borderRadius: "8px",
              borderLeft: "4px solid #007bff"
            }}>
              <h4 style={{ margin: "0 0 10px 0", color: "#333" }}>GenAI Operational Insight</h4>
              <p style={{ margin: 0, color: "#555", whiteSpace: "pre-wrap" }}>{aiInsight}</p>
            </div>
          )}

          <div className="graph-container">
            <div className="graph-card">
              <div style={{ position: "relative", height: '200px', width: '100%', display: "block" }}>
                <Line
                  data={{
                    labels: currentMetrics.length ? currentMetrics.map(m => new Date(m.timestamp).toLocaleDateString()) : ["No Data"],
                    datasets: [{
                      label: "Voltage (V)",
                      data: currentMetrics.length ? currentMetrics.map(m => m.voltage_ab) : [0],
                      borderColor: "#007bff",
                      backgroundColor: "rgba(0,123,255,0.08)",
                      fill: true,
                      tension: 0.3
                    }]
                  }}
                  options={{ maintainAspectRatio: false }}
                />
              </div>
              <p className="graph-title">7-Day Voltage Trend</p>
            </div>

            <div className="graph-card">
              <div style={{ position: "relative", height: '200px', width: '100%', display: "block" }}>
                <Line
                  data={{
                    labels: currentMetrics.length ? currentMetrics.map(m => new Date(m.timestamp).toLocaleDateString()) : ["No Data"],
                    datasets: [{
                      label: "Temp (°C)",
                      data: currentMetrics.length ? currentMetrics.map(m => m.temperature) : [0],
                      borderColor: "#ff5733",
                      backgroundColor: "rgba(255,87,51,0.08)",
                      fill: true,
                      tension: 0.3
                    }]
                  }}
                  options={{ maintainAspectRatio: false }}
                />
              </div>
              <p className="graph-title">7-Day Temperature Trend</p>
            </div>

            <div className="graph-card">
              <div style={{ position: "relative", height: '200px', width: '100%', display: "block" }}>
                <Line
                  data={{
                    labels: currentMetrics.length ? currentMetrics.map(m => new Date(m.timestamp).toLocaleDateString()) : ["No Data"],
                    datasets: [{
                      label: "Power (kW)",
                      data: currentMetrics.length ? currentMetrics.map(m => m.power) : [0],
                      borderColor: "#28a745",
                      backgroundColor: "rgba(40,167,69,0.08)",
                      fill: true,
                      tension: 0.3
                    }]
                  }}
                  options={{ maintainAspectRatio: false }}
                />
              </div>
              <p className="graph-title">7-Day Power Output</p>
            </div>
          </div>
        </div>
      )}

      {modalOpen && activeInverter && (
        <InverterPopUp
          inverterId={activeInverter.id}
          inverterName={activeInverter.name}
          status={activeInverter.gridStatus}
          onClose={() => setModalOpen(false)}
        />
      )}
    </div>
  );
}

export default Home;