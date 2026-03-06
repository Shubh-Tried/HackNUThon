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

        if (!Array.isArray(plantsData) || plantsData.length === 0) {
          // Fallback dummy plant if backend has none
          plantsData = [
            { plant_id: 1, name: "Alpha Solar Plant" },
            { plant_id: 2, name: "Beta Solar Plant" }
          ];
        }

        if (!Array.isArray(invData) || invData.length === 0) {
          // Fallback dummy inverters if backend has none (because of dummy Supabase connection)
          invData = [
            { id: 101, inverter_code: "INV-Alpha-01", plant_id: 1, power: 50.2, temperature: 45, risk_score: 0.1 },
            { id: 102, inverter_code: "INV-Alpha-02", plant_id: 1, power: 48.1, temperature: 48, risk_score: 0.45 },
            { id: 103, inverter_code: "INV-Alpha-03", plant_id: 1, power: 12.0, temperature: 75, risk_score: 0.8 },
            { id: 201, inverter_code: "INV-Beta-01", plant_id: 2, power: 65.5, temperature: 40, risk_score: 0.05 },
            { id: 202, inverter_code: "INV-Beta-02", plant_id: 2, power: 60.2, temperature: 42, risk_score: 0.15 },
          ];
        }

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
          let status = predictions[index]?.prediction?.status || "Normal";
          if (risk > 0.7) status = "Bad";
          else if (risk > 0.4) status = "Warning";
          else status = "Good";

          return {
            ...inv,
            name: inv.inverter_code || `Inverter ${inv.id}`,
            powerVal: (inv.power || inv.pv_power || 0).toFixed(1) + "kW",
            voltageVal: (inv.voltage_ab || 230).toFixed(1) + "V",
            tempVal: (inv.temperature || 35).toFixed(1) + "°C",
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
          // Fallback dummy 7 day data
          const dummyMetrics = Array.from({ length: 7 }).map((_, i) => ({
            timestamp: new Date(Date.now() - (6 - i) * 86400000).toISOString().split('T')[0],
            voltage_ab: 220 + Math.random() * 20,
            temperature: 30 + Math.random() * 20,
            power: 40 + Math.random() * 20
          }));

          let data = dummyMetrics;
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
  const groupedInverters = plants.map((plant) => ({
    ...plant,
    inverters: inverters
      .filter((inv) => inv.plant_id === plant.plant_id || inv.plant_id === plant.id)
      .sort((a, b) => b.risk_score - a.risk_score),
  })).filter(p => p.inverters.length > 0);

  // Summary stats
  const totalInverters = inverters.length;
  const activeInvs = inverters.filter((i) => i.gridStatus !== "Bad").length;
  const atRisk = inverters.filter((i) => i.gridStatus !== "Good").length;
  const totalPower = inverters.reduce((acc, inv) => acc + (inv.power || 0), 0);

  return (
    <div className="home">
      <GraphsSection />

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
                  <p style={{ color: getStatusColor(inv.gridStatus), fontWeight: 'bold' }}>
                    Status: {inv.gridStatus} ({(inv.risk_score * 100).toFixed(1)}%)
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
              <div style={{ position: "relative", height: '200px', width: '100%' }}>
                <Line
                  data={{
                    labels: currentMetrics.map(m => new Date(m.timestamp).toLocaleDateString()),
                    datasets: [{
                      label: "Voltage (V)",
                      data: currentMetrics.map(m => m.voltage_ab),
                      borderColor: "#007bff",
                      tension: 0.3
                    }]
                  }}
                  options={{ maintainAspectRatio: false }}
                />
              </div>
              <p className="graph-title">7-Day Voltage Trend</p>
            </div>

            <div className="graph-card">
              <div style={{ position: "relative", height: '200px', width: '100%' }}>
                <Line
                  data={{
                    labels: currentMetrics.map(m => new Date(m.timestamp).toLocaleDateString()),
                    datasets: [{
                      label: "Temp (°C)",
                      data: currentMetrics.map(m => m.temperature),
                      borderColor: "#ff5733",
                      tension: 0.3
                    }]
                  }}
                  options={{ maintainAspectRatio: false }}
                />
              </div>
              <p className="graph-title">7-Day Temperature Trend</p>
            </div>

            <div className="graph-card">
              <div style={{ position: "relative", height: '200px', width: '100%' }}>
                <Line
                  data={{
                    labels: currentMetrics.map(m => new Date(m.timestamp).toLocaleDateString()),
                    datasets: [{
                      label: "Power (kW)",
                      data: currentMetrics.map(m => m.power),
                      borderColor: "#28a745",
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