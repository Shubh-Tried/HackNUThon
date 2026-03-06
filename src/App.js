import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Home from "./section/Home/Home.js";
import About from "./section/About/About.js";
import Navbar from "./components/Navbar.js";
import Chatbot from "./pages/Chatbot/Chatbot.js";
import Inverters from "./pages/Inverters/Inverters.js";

function App() {
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);

  return (
    <Router>
      <div style={{ backgroundColor: "#F5F7FB" }}>
        <Navbar />

        <Routes>
          {/* Main landing page */}
          <Route
            path="/"
            element={
              <>
                <section id="home">
                  <Home />
                </section>

                <section id="about">
                  <About />
                </section>
              </>
            }
          />
          <Route path="/inverters" element={<Inverters />} />
        </Routes>

        {/* Floating AI Chatbot Button */}
        <div
          className="floating-ai-btn"
          onClick={() => setIsChatbotOpen(true)}
          title="Ask AI"
        >
          <span className="ai-btn-icon">🤖</span>
          <span className="ai-btn-pulse" />
        </div>

        {/* Chatbot Modal Overlay */}
        {isChatbotOpen && <Chatbot onClose={() => setIsChatbotOpen(false)} />}
      </div>
    </Router>
  );
}

export default App;