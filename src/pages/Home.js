import React, { useEffect, useState } from "react";
import InverterCard from "../components/InverterCard";

function Home() {
  const [inverters, setInverters] = useState([]);

  useEffect(() => {
    // Replace this with your real API call
    const dummyData = [
      { id: 1, name: "Inverter A", power: "5kW" },
      { id: 2, name: "Inverter B", power: "10kW" },
      { id: 3, name: "Inverter C", power: "15kW" }
    ];
    setInverters(dummyData);
  }, []);

  return (
    <div style={{ display: "flex", gap: "20px", padding: "20px", flexWrap: "wrap" }}>
      {inverters.map(inv => (
        <InverterCard key={inv.id} inverter={inv} />
      ))}
    </div>
  );
}

export default Home;