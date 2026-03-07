import React, { useState, useEffect, useRef } from "react";
import "./NotificationBell.css";

const API_BASE = "http://localhost:8000";

function NotificationBell() {
    const [alerts, setAlerts] = useState([]);
    const [isOpen, setIsOpen] = useState(false);
    const [hasNew, setHasNew] = useState(false);
    const dropdownRef = useRef(null);

    useEffect(() => {
        const fetchAlerts = async () => {
            try {
                const invRes = await fetch(`${API_BASE}/inverters`);
                let invData = await invRes.json();

                if (!Array.isArray(invData) || invData.length === 0) {
                    invData = [
                        { id: 101, inverter_code: "INV-Alpha-01", power: 50.2, temperature: 45, risk_score: 0.1 },
                        { id: 102, inverter_code: "INV-Alpha-02", power: 48.1, temperature: 48, risk_score: 0.45 },
                        { id: 103, inverter_code: "INV-Alpha-03", power: 12.0, temperature: 75, risk_score: 0.8 },
                        { id: 201, inverter_code: "INV-Beta-01", power: 65.5, temperature: 40, risk_score: 0.05 },
                        { id: 202, inverter_code: "INV-Beta-02", power: 60.2, temperature: 42, risk_score: 0.15 },
                    ];
                }

                const generated = [];

                invData.forEach((inv) => {
                    const risk = parseFloat(inv.risk_score) || 0;
                    const name = inv.inverter_code || `Inverter ${inv.id}`;
                    const temp = inv.temperature || 0;

                    if (risk > 0.7) {
                        generated.push({
                            id: `${inv.id}-critical`,
                            type: "critical",
                            title: `${name} — Critical Risk`,
                            message: `Risk score at ${(risk * 100).toFixed(0)}%. Immediate inspection recommended.`,
                            time: "Just now",
                        });
                    } else if (risk > 0.4) {
                        generated.push({
                            id: `${inv.id}-warning`,
                            type: "warning",
                            title: `${name} — Warning`,
                            message: `Risk score at ${(risk * 100).toFixed(0)}%. Monitor closely.`,
                            time: "Just now",
                        });
                    }

                    if (temp > 65) {
                        generated.push({
                            id: `${inv.id}-temp`,
                            type: "critical",
                            title: `${name} — High Temperature`,
                            message: `Temperature at ${temp.toFixed(1)}°C exceeds safe threshold.`,
                            time: "Just now",
                        });
                    }
                });

                setAlerts(generated);
                if (generated.length > 0) setHasNew(true);
            } catch (err) {
                console.error("Failed to fetch alerts:", err);
            }
        };

        fetchAlerts();
        const interval = setInterval(fetchAlerts, 30000);
        return () => clearInterval(interval);
    }, []);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const toggleDropdown = () => {
        setIsOpen(!isOpen);
        if (!isOpen) setHasNew(false);
    };

    const getTypeIcon = (type) => {
        switch (type) {
            case "critical": return "🔴";
            case "warning": return "⚠️";
            default: return "ℹ️";
        }
    };

    const getTypeColor = (type) => {
        switch (type) {
            case "critical": return "#dc3545";
            case "warning": return "#ffc107";
            default: return "#007bff";
        }
    };

    const criticalCount = alerts.filter((a) => a.type === "critical").length;
    const warningCount = alerts.filter((a) => a.type === "warning").length;

    return (
        <div className="notif-bell-wrapper" ref={dropdownRef}>
            <div className="notif-bell" onClick={toggleDropdown}>
                <span className="bell-icon">🔔</span>
                {alerts.length > 0 && (
                    <span className={`notif-badge ${hasNew ? "notif-badge-pulse" : ""}`}>
                        {alerts.length}
                    </span>
                )}
            </div>

            {isOpen && (
                <div className="notif-dropdown">
                    <div className="notif-header">
                        <h3>Notifications</h3>
                        <div className="notif-summary">
                            {criticalCount > 0 && (
                                <span className="notif-tag notif-tag-critical">{criticalCount} Critical</span>
                            )}
                            {warningCount > 0 && (
                                <span className="notif-tag notif-tag-warning">{warningCount} Warning</span>
                            )}
                            {alerts.length === 0 && (
                                <span className="notif-tag notif-tag-ok">All Clear</span>
                            )}
                        </div>
                    </div>

                    <div className="notif-list">
                        {alerts.length === 0 ? (
                            <div className="notif-empty">
                                <span className="notif-empty-icon">✅</span>
                                <p>No alerts — all inverters operating normally.</p>
                            </div>
                        ) : (
                            alerts.map((alert) => (
                                <div
                                    key={alert.id}
                                    className="notif-item"
                                    style={{ borderLeftColor: getTypeColor(alert.type) }}
                                >
                                    <div className="notif-item-icon">{getTypeIcon(alert.type)}</div>
                                    <div className="notif-item-content">
                                        <p className="notif-item-title">{alert.title}</p>
                                        <p className="notif-item-msg">{alert.message}</p>
                                        <span className="notif-item-time">{alert.time}</span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default NotificationBell;
