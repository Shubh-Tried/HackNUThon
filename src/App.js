import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Home from "./section/Home/Home.js";
import About from "./section/About/About.js";
import Navbar from "./components/Navbar.js";
import Chatbot from "./pages/Chatbot/Chatbot.js";

function App() {
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);

  return (
    <Router>
      <div style={{ backgroundColor: "#F5F7FB" }}>
        <Navbar onOpenChatbot={() => setIsChatbotOpen(true)} />

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
        </Routes>

        {/* Chatbot Modal Overlay */}
        {isChatbotOpen && <Chatbot onClose={() => setIsChatbotOpen(false)} />}
      </div>
    </Router>
  );
}

export default App;