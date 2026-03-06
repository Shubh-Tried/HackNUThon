import React, { useState } from "react";
import "./Chatbot.css";

function Chatbot({ onClose }) {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hello! How can I help with your inverter today?" }
  ]);

  const [input, setInput] = useState("");

  const sendMessage = () => {
    if (!input.trim()) return;

    const newMessages = [
      ...messages,
      { sender: "user", text: input },
      { sender: "bot", text: "This is a demo response for now." }
    ];

    setMessages(newMessages);
    setInput("");
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
        </div>

        <div className="chat-input">
          <input
            type="text"
            placeholder="Ask something..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default Chatbot;