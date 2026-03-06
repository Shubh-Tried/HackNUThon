import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import "./Navbar.css";

function Navbar({ onOpenChatbot }) {

  const [menuOpen, setMenuOpen] = useState(false);
  const [show, setShow] = useState(true);
  const [lastScroll, setLastScroll] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScroll = window.pageYOffset;

      if (currentScroll > lastScroll) {
        setShow(false);
      } else {
        setShow(true);
      }

      setLastScroll(currentScroll);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [lastScroll]);

  return (
    <nav className={`navbar ${show ? "show" : "hide"}`}>
      <div className="nav-container">
        <div className="logo">
          <a href="#home">Team Confidential</a>
        </div>

        <div
          className={`burger ${menuOpen ? "active" : ""}`}
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <span></span>
          <span></span>
          <span></span>
        </div>

        <ul className={`nav-links ${menuOpen ? "open" : ""}`}>
          <li><Link to="/">Home</Link></li>
          <li><a href="#about">About</a></li>
          <li>
            <button className="nav-service-btn" onClick={onOpenChatbot}>
              Services
            </button>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;