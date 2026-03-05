import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar.js"
import "./App.css"

function Home() {
  const [inverters, setInverters] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    // Replace with your API later
    const dummyData = [
      { id: 1, name: "Inverter A", power: "5kW", voltage: "220V", temp: "35°C", status: "Good" },
      { id: 2, name: "Inverter B", power: "10kW", voltage: "230V", temp: "40°C", status: "About to be bad" },
      { id: 3, name: "Inverter C", power: "15kW", voltage: "240V", temp: "38°C", status: "Good" },
      { id: 4, name: "Inverter D", power: "20kW", voltage: "250V", temp: "42°C", status: "Bad" }
    ];
    setInverters(dummyData);
  }, []);

  const handleClick = (inv) => {
    if (selected?.id === inv.id) {
      setSelected(null); // collapse if clicked again
    } else {
      setSelected(inv);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "Good":
        return "#28a745";
      case "Bad":
        return "#dc3545";
      case "About to be bad":
        return "#ffc107";
      default:
        return "#cccccc";
    }
  };

  return (
    <div>
      <Navbar></Navbar>
    <div style={{ padding: "50px" }}>

      <div
        style={{
          display: "flex",
          gap: "20px",
          flexWrap: "wrap",
          justifyContent: "center",
          paddingTop : "20px"
        }}
      >
        {inverters.map((inv) => (
          <div
            key={inv.id}
            className={`small-info-cards ${selected?.id === inv.id ? "selected" : ""}`}
            onClick={() => handleClick(inv)}
          >
            <h3>{inv.name}</h3>
            <p>Power: {inv.power}</p>
          </div>
        ))}
      </div>


      {selected && (
        <div
          className="status-card"
          style={{
            borderColor: getStatusColor(selected.status),
            "--status-color": getStatusColor(selected.status)
          }}
        >
          <div id="top-slide">
          <h2>{selected.name} - Full Details</h2>

          <div className = "ai-help">
            ASK AI
          </div>

          </div>
          <div className="graph-container">

            <div className="graph-card">
              <div className="graph-placeholder">Dummy Graph 1</div>
              <p className="graph-title">Voltage Trend</p>
            </div>

            <div className="graph-card">
              <div className="graph-placeholder">Dummy Graph 2</div>
              <p className="graph-title">Temperature Trend</p>
            </div>

            <div className="graph-card">
              <div className="graph-placeholder">Dummy Graph 3</div>
              <p className="graph-title">Power Output</p>
            </div>

          </div>
        </div>
      )}

    </div>
    </div>
  );
}

export default Home;