import { useState } from "react"
import "./App.css"

interface Message {
  text: string;
  sender: "user" | "assistant";
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { text: "Hello! I am your agricultural assistant. How can I help you today?", sender: "assistant" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = input;
    setMessages(prev => [...prev, { text: userMessage, sender: "user" }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8080/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, sessionId: "test-session" })
      });
      
      if (!response.ok) throw new Error("Network response was not ok");
      
      const data = await response.json();
      setMessages(prev => [...prev, { text: data.answer, sender: "assistant" }]);
    } catch (err: any) {
      setError(err.message || "Error connecting to the server");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>Agricultural AI Assistant</h1>
      </header>
      
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
        {loading && <div className="message assistant loading">Typing...</div>}
        {error && <div className="error-message">Error: {error}</div>}
      </div>

      <div className="chat-input-area">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask a question about your crops..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  )
}

export default App
