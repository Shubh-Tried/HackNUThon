import React, { useEffect, useState } from "react";
import InverterCard from "../components/InverterCard";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";
const REFRESH_MS = 5 * 60 * 1000; // 5 minutes

function Home() {
  const [inverters, setInverters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchInverters = async () => {
    try {
      const res = await fetch(`${API_BASE}/inverters`);
      if (!res.ok) throw new Error(`API error ${res.status}`);
      const data = await res.json();
      setInverters(data);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch inverters:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInverters();
    const interval = setInterval(fetchInverters, REFRESH_MS);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div style={{ padding: "40px", textAlign: "center" }}>Loading inverters…</div>;
  }

  if (error) {
    return (
      <div style={{ padding: "40px", textAlign: "center", color: "#dc3545" }}>
        Error: {error}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", gap: "20px", padding: "20px", flexWrap: "wrap" }}>
      {inverters.map((inv) => (
        <InverterCard key={inv.id || inv.inverter_code} inverter={inv} />
      ))}
    </div>
  );
}

export default Home;