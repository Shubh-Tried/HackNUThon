import React from "react";
import "./About.css";

function About() {
  const features = [
    {
      icon: "⚡",
      title: "Real-Time Monitoring",
      desc: "Track live power output, voltage, and temperature across all your solar inverters in real-time."
    },
    {
      icon: "🤖",
      title: "AI-Powered Predictions",
      desc: "Our ML pipeline analyzes patterns to predict potential failures 7–10 days before they happen."
    },
    {
      icon: "📊",
      title: "Smart Analytics",
      desc: "Visual dashboards with trend charts, risk scores, and plant-wide performance comparisons."
    },
    {
      icon: "🔔",
      title: "Instant Alerts",
      desc: "Get notified immediately when an inverter shows signs of degradation or abnormal behavior."
    },
    {
      icon: "💬",
      title: "GenAI Insights",
      desc: "Ask AI for operational explanations and maintenance recommendations on any inverter."
    },
    {
      icon: "🛡️",
      title: "Risk Assessment",
      desc: "Color-coded risk indicators help you prioritize maintenance and reduce downtime."
    }
  ];

  return (
    <div className="about-section">
      <div className="about-header">
        <h1 className="about-title">About This Platform</h1>
        <p className="about-subtitle">
          An intelligent solar inverter monitoring and failure prediction system
          built to maximize plant uptime and operational efficiency.
        </p>
      </div>

      <div className="about-features-grid">
        {features.map((f, i) => (
          <div key={i} className="about-feature-card">
            <div className="about-feature-icon">{f.icon}</div>
            <h3 className="about-feature-title">{f.title}</h3>
            <p className="about-feature-desc">{f.desc}</p>
          </div>
        ))}
      </div>

      <div className="about-tech-strip">
        <div className="about-tech-item">
          <span className="tech-label">Frontend</span>
          <span className="tech-value">React + Chart.js</span>
        </div>
        <div className="about-tech-item">
          <span className="tech-label">Backend</span>
          <span className="tech-value">FastAPI + Uvicorn</span>
        </div>
        <div className="about-tech-item">
          <span className="tech-label">ML Engine</span>
          <span className="tech-value">Scikit-learn + SHAP</span>
        </div>
        <div className="about-tech-item">
          <span className="tech-label">AI Layer</span>
          <span className="tech-value">OpenAI GPT</span>
        </div>
      </div>
    </div>
  );
}

export default About;