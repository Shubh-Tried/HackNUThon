import React, { useState, useEffect } from "react";
import "./Inverters.css";
import { Line } from "react-chartjs-2";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Tooltip,
    Legend,
    Filler
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

const API_BASE = "http://localhost:8000";

function Inverters() {
    const [inverters, setInverters] = useState([]);
    const [plants, setPlants] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [detail, setDetail] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);
    const [metrics, setMetrics] = useState([]);
    const [aiSummary, setAiSummary] = useState("");
    const [aiLoading, setAiLoading] = useState(false);
    const [filterStatus, setFilterStatus] = useState("All");
    const [searchTerm, setSearchTerm] = useState("");

    useEffect(() => {
        const fetchData = async () => {
            try {
                const invRes = await fetch(`${API_BASE}/inverters`);
                let invData = await invRes.json();

                const plantsRes = await fetch(`${API_BASE}/plants`);
                let plantsData = await plantsRes.json();

                if (!Array.isArray(plantsData)) plantsData = [];
                if (!Array.isArray(invData)) invData = [];

                // Fetch predictions
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

                    const plantName = plantsData.find(
                        (p) => p.plant_id === inv.plant_id || p.id === inv.plant_id
                    )?.name || "Unknown Plant";

                    return {
                        ...inv,
                        name: inv.inverter_code || `Inverter ${inv.id}`,
                        status,
                        risk_score: risk,
                        plantName,
                        power: inv.power || inv.pv_power || 0,
                        temperature: inv.temperature || 35,
                        voltage_ab: inv.voltage_ab || 230,
                        frequency: inv.frequency || 50,
                        power_factor: inv.power_factor || 0.95,
                        kwh_total: inv.kwh_total || 0,
                    };
                });

                setInverters(invData);
                setPlants(plantsData);
            } catch (error) {
                console.error("Error fetching inverters:", error);
            }
        };
        fetchData();
    }, []);

    const handleSelect = async (inv) => {
        if (selectedId === inv.id) {
            setSelectedId(null);
            setDetail(null);
            setMetrics([]);
            setAiSummary("");
            return;
        }

        setSelectedId(inv.id);
        setDetailLoading(true);
        setAiSummary("");
        setAiLoading(true);

        // Fetch detail
        try {
            const res = await fetch(`${API_BASE}/inverter/${inv.id}`);
            if (res.ok) {
                const json = await res.json();
                setDetail(json);
            } else {
                setDetail(inv);
            }
        } catch {
            setDetail(inv);
        }

        // Fetch 7-day metrics from real data
        try {
            let data = [];
            try {
                const res = await fetch(`${API_BASE}/inverter/${inv.id}/metrics?limit=7`);
                if (res.ok) {
                    const result = await res.json();
                    if (result && result.length > 0) data = result.reverse();
                }
            } catch { }

            setMetrics(data);
        } catch { }

        setDetailLoading(false);

        // Fetch AI summary (non-blocking, loads after detail)
        try {
            const aiRes = await fetch(`${API_BASE}/inverter/${inv.id}/ai-summary`);
            if (aiRes.ok) {
                const aiData = await aiRes.json();
                setAiSummary(aiData.summary || "No summary available.");
            } else {
                setAiSummary("Unable to generate AI analysis at this time.");
            }
        } catch {
            setAiSummary("Unable to connect to AI service.");
        }
        setAiLoading(false);
    };

    const getStatusColor = (status) => {
        switch (status) {
            case "Good": case "Normal": return "#28a745";
            case "Warning": return "#ffc107";
            case "Bad": case "Critical": return "#dc3545";
            default: return "#999";
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case "Good": case "Normal": return "✅";
            case "Warning": return "⚠️";
            case "Bad": case "Critical": return "🔴";
            default: return "⚪";
        }
    };

    const getRiskLabel = (risk) => {
        if (risk > 0.7) return "High Risk";
        if (risk > 0.4) return "Medium Risk";
        return "Low Risk";
    };

    // Filtering & Deduplication
    const seenNames = new Set();
    const filtered = inverters.filter((inv) => {
        if (seenNames.has(inv.name)) return false;

        const matchesStatus = filterStatus === "All" || inv.status === filterStatus;
        const matchesSearch = inv.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            inv.plantName.toLowerCase().includes(searchTerm.toLowerCase());

        if (matchesStatus && matchesSearch) {
            seenNames.add(inv.name);
            return true;
        }
        return false;
    });

    // Summary counts
    // Summary counts based on the deduplicated 'filtered' or overall unique list
    const uniqueOverall = [];
    const uniqueNames = new Set();
    for (const inv of inverters) {
        if (!uniqueNames.has(inv.name)) {
            uniqueNames.add(inv.name);
            uniqueOverall.push(inv);
        }
    }

    const goodCount = uniqueOverall.filter((i) => i.status === "Normal").length;
    const warningCount = uniqueOverall.filter((i) => i.status === "Warning").length;
    const badCount = uniqueOverall.filter((i) => i.status === "Critical").length;

    const chartOptions = {
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: false } },
    };

    return (
        <div className="inverters-page">
            <div className="inv-page-header">
                <h1>All Inverters</h1>
                <p className="inv-page-subtitle">
                    Monitor, filter, and inspect every inverter across all plants
                </p>
            </div>

            {/* Status Summary Bar */}
            <div className="inv-status-bar">
                <div className="inv-status-pill" onClick={() => setFilterStatus("All")}>
                    <span className="pill-dot" style={{ background: "#007bff" }} />
                    <span>All ({uniqueOverall.length})</span>
                </div>
                <div className="inv-status-pill" onClick={() => setFilterStatus("Normal")}>
                    <span className="pill-dot" style={{ background: "#28a745" }} />
                    <span>Normal ({goodCount})</span>
                </div>
                <div className="inv-status-pill" onClick={() => setFilterStatus("Warning")}>
                    <span className="pill-dot" style={{ background: "#ffc107" }} />
                    <span>Warning ({warningCount})</span>
                </div>
                <div className="inv-status-pill" onClick={() => setFilterStatus("Critical")}>
                    <span className="pill-dot" style={{ background: "#dc3545" }} />
                    <span>Critical ({badCount})</span>
                </div>
            </div>

            {/* Search */}
            <div className="inv-search-bar">
                <input
                    type="text"
                    placeholder="Search by inverter name or plant..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
            </div>

            {/* Inverter Table */}
            <div className="inv-table-wrapper">
                <table className="inv-table">
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th>Inverter</th>
                            <th>Plant</th>
                            <th>Power (kW)</th>
                            <th>Temp (°C)</th>
                            <th>Voltage (V)</th>
                            <th>kWh Total</th>
                            <th>Risk</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.map((inv) => (
                            <React.Fragment key={inv.id}>
                                <tr
                                    className={`inv-row ${selectedId === inv.id ? "inv-row-active" : ""}`}
                                    onClick={() => handleSelect(inv)}
                                >
                                    <td>
                                        <span
                                            className="inv-status-dot"
                                            style={{ background: getStatusColor(inv.status) }}
                                            title={inv.status}
                                        />
                                    </td>
                                    <td className="inv-name-cell">
                                        <span className="inv-name">{inv.name}</span>
                                        <span className="inv-id">ID: {inv.id}</span>
                                    </td>
                                    <td>{inv.plantName}</td>
                                    <td>{inv.power.toFixed(1)}</td>
                                    <td>
                                        <span style={{ color: inv.temperature > 60 ? "#dc3545" : inv.temperature > 50 ? "#ffc107" : "#333" }}>
                                            {inv.temperature.toFixed(1)}
                                        </span>
                                    </td>
                                    <td>{inv.voltage_ab.toFixed(1)}</td>
                                    <td>{inv.kwh_total != null ? inv.kwh_total.toLocaleString() : "N/A"}</td>
                                    <td>
                                        <span
                                            className="inv-risk-badge"
                                            style={{
                                                background: getStatusColor(inv.status) + "20",
                                                color: getStatusColor(inv.status),
                                                borderColor: getStatusColor(inv.status),
                                            }}
                                        >
                                            {(inv.risk_score * 100).toFixed(0)}% — {getRiskLabel(inv.risk_score)}
                                        </span>
                                    </td>
                                    <td className="inv-expand-cell">
                                        <span className={`inv-expand-arrow ${selectedId === inv.id ? "open" : ""}`}>▼</span>
                                    </td>
                                </tr>

                                {/* Expanded Detail Bio */}
                                {selectedId === inv.id && (
                                    <tr className="inv-detail-row">
                                        <td colSpan="8">
                                            {detailLoading ? (
                                                <div className="inv-detail-loading">Loading details...</div>
                                            ) : (
                                                <div className="inv-detail-panel">
                                                    <div className="inv-detail-header">
                                                        <div className="inv-detail-title">
                                                            <span className="inv-detail-icon">{getStatusIcon(inv.status)}</span>
                                                            <h2>{detail?.inverter_code || inv.name}</h2>
                                                            <span
                                                                className="inv-detail-badge"
                                                                style={{
                                                                    background: getStatusColor(inv.status),
                                                                }}
                                                            >
                                                                {inv.status}
                                                            </span>
                                                        </div>
                                                        <p className="inv-detail-plant">Plant: {inv.plantName}</p>
                                                    </div>

                                                    {/* Stats Grid */}
                                                    <div className="inv-detail-stats">
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">Power Output</span>
                                                            <span className="stat-value">{(detail?.power ?? inv.power).toFixed(1)} kW</span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">PV Power</span>
                                                            <span className="stat-value">{detail?.pv_power != null ? `${detail.pv_power} kW` : "N/A"}</span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">Temperature</span>
                                                            <span className="stat-value">{(detail?.temperature ?? inv.temperature).toFixed(1)}°C</span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">Frequency</span>
                                                            <span className="stat-value">{detail?.frequency != null ? `${detail.frequency} Hz` : `${inv.frequency} Hz`}</span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">Power Factor</span>
                                                            <span className="stat-value">{(detail?.power_factor ?? inv.power_factor)?.toFixed(3) || "N/A"}</span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">Voltage AB</span>
                                                            <span className="stat-value">{(detail?.voltage_ab ?? inv.voltage_ab).toFixed(1)} V</span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">Voltage BC</span>
                                                            <span className="stat-value">{detail?.voltage_bc != null ? `${detail.voltage_bc} V` : "N/A"}</span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">Voltage CA</span>
                                                            <span className="stat-value">{detail?.voltage_ca != null ? `${detail.voltage_ca} V` : "N/A"}</span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">kWh Today</span>
                                                            <span className="stat-value">{detail?.kwh_today != null ? `${detail.kwh_today.toLocaleString()} kWh` : "N/A"}</span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">kWh Total</span>
                                                            <span className="stat-value">{detail?.kwh_total != null ? `${detail.kwh_total.toLocaleString()} kWh` : "N/A"}</span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">Operating State</span>
                                                            <span className="stat-value">
                                                                {detail?.op_state === 1 ? "🟢 Running" : detail?.op_state === 0 ? "🔴 Stopped" : "Unknown"}
                                                            </span>
                                                        </div>
                                                        <div className="inv-stat-box">
                                                            <span className="stat-label">Risk Score</span>
                                                            <span className="stat-value" style={{ color: getStatusColor(inv.status), fontWeight: 700 }}>
                                                                {(inv.risk_score * 100).toFixed(1)}%
                                                            </span>
                                                        </div>
                                                    </div>

                                                    {/* AI Explanation */}
                                                    <div className="inv-ai-summary">
                                                        <div className="inv-ai-header">
                                                            <span className="inv-ai-icon">🤖</span>
                                                            <h3>AI Analysis</h3>
                                                        </div>
                                                        {aiLoading ? (
                                                            <div className="inv-ai-loading">
                                                                <div className="inv-ai-loading-dots">
                                                                    <span></span><span></span><span></span>
                                                                </div>
                                                                <p>Analyzing inverter data...</p>
                                                            </div>
                                                        ) : aiSummary ? (
                                                            <div className="inv-ai-content">
                                                                {aiSummary.split('\n').map((line, i) => (
                                                                    <p key={i}>{line}</p>
                                                                ))}
                                                            </div>
                                                        ) : null}
                                                    </div>

                                                    {/* Mini Charts */}
                                                    {metrics.length > 0 && (
                                                        <div className="inv-detail-charts">
                                                            <div className="inv-mini-chart">
                                                                <h4>7-Day Voltage</h4>
                                                                <div style={{ position: "relative", height: "140px", width: "100%", display: "block" }}>
                                                                    <Line
                                                                        data={{
                                                                            labels: metrics.length ? metrics.map((m) => new Date(m.timestamp).toLocaleDateString()) : ["No Data"],
                                                                            datasets: [{
                                                                                label: "Voltage (V)",
                                                                                data: metrics.length ? metrics.map((m) => m.voltage_ab) : [0],
                                                                                borderColor: "#007bff",
                                                                                backgroundColor: "rgba(0,123,255,0.08)",
                                                                                fill: true,
                                                                                tension: 0.3,
                                                                            }],
                                                                        }}
                                                                        options={chartOptions}
                                                                    />
                                                                </div>
                                                            </div>
                                                            <div className="inv-mini-chart">
                                                                <h4>7-Day Temperature</h4>
                                                                <div style={{ position: "relative", height: "140px", width: "100%", display: "block" }}>
                                                                    <Line
                                                                        data={{
                                                                            labels: metrics.length ? metrics.map((m) => new Date(m.timestamp).toLocaleDateString()) : ["No Data"],
                                                                            datasets: [{
                                                                                label: "Temp (°C)",
                                                                                data: metrics.length ? metrics.map((m) => m.temperature) : [0],
                                                                                borderColor: "#ff5733",
                                                                                backgroundColor: "rgba(255,87,51,0.08)",
                                                                                fill: true,
                                                                                tension: 0.3,
                                                                            }],
                                                                        }}
                                                                        options={chartOptions}
                                                                    />
                                                                </div>
                                                            </div>
                                                            <div className="inv-mini-chart">
                                                                <h4>7-Day Power</h4>
                                                                <div style={{ position: "relative", height: "140px", width: "100%", display: "block" }}>
                                                                    <Line
                                                                        data={{
                                                                            labels: metrics.length ? metrics.map((m) => new Date(m.timestamp).toLocaleDateString()) : ["No Data"],
                                                                            datasets: [{
                                                                                label: "Power (kW)",
                                                                                data: metrics.length ? metrics.map((m) => m.power) : [0],
                                                                                borderColor: "#28a745",
                                                                                backgroundColor: "rgba(40,167,69,0.08)",
                                                                                fill: true,
                                                                                tension: 0.3,
                                                                            }],
                                                                        }}
                                                                        options={chartOptions}
                                                                    />
                                                                </div>
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                )}
                            </React.Fragment>
                        ))}
                    </tbody>
                </table>

                {filtered.length === 0 && (
                    <div className="inv-no-results">
                        No inverters found matching your filter.
                    </div>
                )}
            </div>
        </div>
    );
}

export default Inverters;
