import React, { useState } from "react";
import "./Chatbot.css";

const API_BASE = "http://localhost:8000";

function Chatbot({ onClose }) {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hello! How can I help with your inverter today?" }
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setMessages(prev => [...prev, { sender: "user", text: userMessage }]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage }),
      });

      if (res.ok) {
        const data = await res.json();
        setMessages(prev => [
          ...prev,
          { sender: "bot", text: data.answer || "I couldn't find an answer." }
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          { sender: "bot", text: "Sorry, the AI service is temporarily unavailable." }
        ]);
      }
    } catch (error) {
      console.error("Chatbot error:", error);
      setMessages(prev => [
        ...prev,
        { sender: "bot", text: "Error connecting to the AI service. Is the backend running?" }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chatbot-modal-overlay">
      <div className="chatbot-page">
        <div className="chatbot-header">
          <h2>Service Assistant</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="chat-window">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              {msg.text}
            </div>
          ))}
          {isLoading && (
            <div className="message bot" style={{ fontStyle: "italic", opacity: 0.7 }}>
              Thinking...
            </div>
          )}
        </div>

        <div className="chat-input">
          <input
            type="text"
            placeholder="Ask something..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            disabled={isLoading}
          />
          <button onClick={sendMessage} disabled={isLoading}>
            {isLoading ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Chatbot;