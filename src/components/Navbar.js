import React, { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Navbar.css";
import NotificationBell from "./NotificationBell";

function Navbar() {

  const [menuOpen, setMenuOpen] = useState(false);
  const [show, setShow] = useState(true);
  const [lastScroll, setLastScroll] = useState(0);
  const location = useLocation();
  const navigate = useNavigate();

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

  const handleAboutClick = (e) => {
    e.preventDefault();
    if (location.pathname === "/") {
      // Already on home page, just scroll to #about
      const el = document.getElementById("about");
      if (el) el.scrollIntoView({ behavior: "smooth" });
    } else {
      // Navigate to home page then scroll to about
      navigate("/");
      setTimeout(() => {
        const el = document.getElementById("about");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 300);
    }
    setMenuOpen(false);
  };

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
          <li><Link to="/" onClick={() => setMenuOpen(false)}>Home</Link></li>
          <li><Link to="/inverters" onClick={() => setMenuOpen(false)}>Inverters</Link></li>
          <li><a href="#about" onClick={handleAboutClick}>About</a></li>
          <li><NotificationBell /></li>
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;