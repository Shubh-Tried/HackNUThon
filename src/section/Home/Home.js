import React, { useState, useEffect, useRef } from "react";
import "./Home.css";
import InverterPopUp from "../../components/InverterPopUp";



function Home() {

  const [inverters, setInverters] = useState([]);
  const [selected, setSelected] = useState(null);
  const detailRef = useRef(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [activeInverter, setActiveInverter] = useState(null);

  useEffect(() => {
    const dummyData = [
      { id: 1, name: "Inverter A", power: "5kW", voltage: "220V", temp: "35°C",status:"Running", gridStatus: "Good" },
      { id: 2, name: "Inverter B", power: "10kW", voltage: "230V", temp: "40°C",status:"Idle", gridStatus: "Warning" },
      { id: 3, name: "Inverter C", power: "15kW", voltage: "240V", temp: "38°C",status:"Running", gridStatus: "Good" },
      { id: 4, name: "Inverter D", power: "20kW", voltage: "250V", temp: "42°C",status:"Fault", gridStatus: "Bad" },
      { id: 5, name: "Inverter E", power: "18kW", voltage: "240V", temp: "40°C",status:"Fault", gridStatus: "Bad" },
      { id: 6, name: "Inverter F", power: "45kW", voltage: "240V", temp: "28°C",status:"Running", gridStatus: "Good" },
      { id: 7, name: "Inverter G", power: "20kW", voltage: "250V", temp: "42°C",status:"Fault", gridStatus: "Bad" }
    ];

    setInverters(dummyData);

  }, []);


  useEffect(() => {
    if (selected && detailRef.current) {
      detailRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    }
  }, [selected]);


//   const handleClick = (inv) => {
//     if (selected?.id === inv.id) {
//       setSelected(null);
//     } else {
//       setSelected(inv);
//     }
//   };

    const handleClick = (inv) => {
    setActiveInverter(inv);
    setModalOpen(true);
    };

  const getStatusColor = (status) => {
    switch (status) {
      case "Good":
        return "#28a745";
      case "Bad":
        return "#dc3545";
      case "Warning":
        return "#ffc107";
      default:
        return "#cccccc";
    }
  };


  return (
    <div className="home">


        <div
          style={{
            display: "flex",
            gap: "20px",
            flexWrap: "wrap",
            justifyContent: "center",
            paddingTop: "20px"
          }}
        >

          {inverters.map((inv) => (
            <div
                key={inv.id}
                className={`small-info-cards ${selected?.id === inv.id ? "selected" : ""}`}
                onClick={() => handleClick(inv)}
                style={{
                borderColor: getStatusColor(inv.gridStatus)
                }}
            >
                <h3>{inv.name}</h3>
                <p>Power: {inv.power}</p>
                <p>Status: {inv.gridStatus}</p>
            </div>
            ))}

        </div>


        {selected && (

          <div
            className={`status-card ${selected.gridStatus}`}
            ref={detailRef}
            style={{
              borderColor: getStatusColor(selected.status),
              "--status-color": getStatusColor(selected.status)
            }}
          >

            <div id="top-slide">

              <h2>{selected.name} - Full Details</h2>

              <div className="ai-help">
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