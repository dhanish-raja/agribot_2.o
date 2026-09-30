import { useState, useEffect, useRef } from "react"
import "./App.css"

interface SourceItem {
  crop?: string;
  topic?: string;
  similarity_score?: number;
  source?: string;
}

interface Message {
  text: string;
  sender: "user" | "assistant";
  crop?: string;
  sources?: (SourceItem | string)[];
  suggestedQuestions?: string[];
  confidence?: string;
}

const CROPS = [
  { id: "", label: "🌱 All Crops", emoji: "🌱" },
  { id: "mango", label: "🥭 Mango", emoji: "🥭" },
  { id: "coconut", label: "🥥 Coconut", emoji: "🥥" },
  { id: "sugarcane", label: "🎋 Sugarcane", emoji: "🎋" },
  { id: "tobacco", label: "🍂 Tobacco", emoji: "🍂" },
  { id: "rice", label: "🌾 Rice", emoji: "🌾" }
];

function formatMarkdown(text: string) {
  // Convert markdown-like headers, bold, and bullet points into styled elements
  const lines = text.split("\n");
  return lines.map((line, idx) => {
    let trimmed = line.trim();
    if (!trimmed) return <div key={idx} className="line-break" />;

    // Headers
    if (trimmed.startsWith("### ")) {
      return <h4 key={idx} className="msg-h4">{trimmed.replace("### ", "")}</h4>;
    }
    if (trimmed.startsWith("## ")) {
      return <h3 key={idx} className="msg-h3">{trimmed.replace("## ", "")}</h3>;
    }
    if (trimmed.startsWith("# ")) {
      return <h2 key={idx} className="msg-h2">{trimmed.replace("# ", "")}</h2>;
    }

    // Bullet points
    if (trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
      const content = trimmed.substring(2);
      return (
        <li key={idx} className="msg-bullet" dangerouslySetInnerHTML={{ __html: renderInline(content) }} />
      );
    }

    // Numbered list
    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
    if (numMatch) {
      return (
        <div key={idx} className="msg-num-item">
          <strong>{numMatch[1]}.</strong> <span dangerouslySetInnerHTML={{ __html: renderInline(numMatch[2]) }} />
        </div>
      );
    }

    return (
      <p key={idx} className="msg-p" dangerouslySetInnerHTML={{ __html: renderInline(trimmed) }} />
    );
  });
}

function renderInline(str: string): string {
  // Parse **bold** and *italic*
  return str
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>");
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      text: "Hello farmer! I am your AgriBot AI Assistant, powered by verified RAG knowledge bases for Mango, Coconut, Sugarcane, Tobacco, and Rice. How can I help your crop today?",
      sender: "assistant",
      suggestedQuestions: [
        "How to control bacterial blight in rice?",
        "What is the fertilizer schedule for coconut trees?",
        "How to manage red rot disease in sugarcane?",
        "What are the control measures for mango fruit fly?"
      ]
    }
  ]);
  const [input, setInput] = useState("");
  const [selectedCrop, setSelectedCrop] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeBackend, setActiveBackend] = useState<string>("Checking...");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    // Health check check both backend (8080) and AI service (8000)
    fetch("http://localhost:8080/api/health")
      .then(res => {
        if (res.ok) setActiveBackend("Spring Boot Gateway (:8080)");
        else throw new Error();
      })
      .catch(() => {
        fetch("http://localhost:8000/health")
          .then(res => {
            if (res.ok) setActiveBackend("FastAPI AI Engine (:8000)");
            else setActiveBackend("Offline");
          })
          .catch(() => setActiveBackend("AI Engine / Gateway Offline"));
      });
  }, []);

  const sendMessage = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query) return;

    setMessages(prev => [...prev, { text: query, sender: "user", crop: selectedCrop }]);
    if (!textToSend) setInput("");
    setLoading(true);
    setError(null);

    const payload = {
      message: query,
      query: query,
      crop: selectedCrop || undefined,
      sessionId: "farmer-session-1"
    };

    try {
      let data: any = null;
      // Try Spring Boot gateway first
      try {
        const res = await fetch("http://localhost:8080/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          data = await res.json();
          setActiveBackend("Spring Boot Gateway (:8080)");
        }
      } catch (err) {
        // Fallback directly to FastAPI AI service
      }

      if (!data) {
        const aiRes = await fetch("http://localhost:8000/rag/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!aiRes.ok) throw new Error(`AI service returned HTTP ${aiRes.status}`);
        data = await aiRes.json();
        setActiveBackend("FastAPI AI Engine (:8000)");
      }

      setMessages(prev => [
        ...prev,
        {
          text: data.answer || "No response received.",
          sender: "assistant",
          crop: data.crop || selectedCrop,
          confidence: data.confidence,
          sources: data.sources || [],
          suggestedQuestions: data.suggested_questions || data.suggestedQuestions || []
        }
      ]);
    } catch (err: any) {
      setError(err.message || "Failed to reach AI service. Please ensure FastAPI or Spring Boot is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <header className="chat-header">
        <div className="header-title">
          <h1>🌾 AgriBot 2.0 Assistant</h1>
          <span className="backend-badge">● {activeBackend}</span>
        </div>
        <p className="header-subtitle">
          Grounded Agronomy & Pest Diagnostics for 5 Major Crops
        </p>

        {/* Crop Selector Bar */}
        <div className="crop-selector">
          {CROPS.map(c => (
            <button
              key={c.id}
              className={`crop-pill ${selectedCrop === c.id ? "active" : ""}`}
              onClick={() => setSelectedCrop(c.id)}
            >
              {c.label}
            </button>
          ))}
        </div>
      </header>

      {/* Messages */}
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-wrapper ${msg.sender}`}>
            <div className={`message ${msg.sender}`}>
              {msg.sender === "assistant" && (
                <div className="msg-meta-header">
                  <span className="bot-tag">AgriBot RAG</span>
                  {msg.crop && <span className="crop-tag">{msg.crop.toUpperCase()}</span>}
                  {msg.confidence && (
                    <span className={`confidence-tag ${msg.confidence.toLowerCase()}`}>
                      {msg.confidence} Confidence
                    </span>
                  )}
                </div>
              )}

              <div className="msg-body">
                {formatMarkdown(msg.text)}
              </div>

              {/* Verified Sources / Citations */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources-container">
                  <div className="sources-label">📚 Verified Citations:</div>
                  <div className="sources-list">
                    {msg.sources.map((s: any, sIdx: number) => {
                      const label = typeof s === "string" 
                        ? s 
                        : `${s.crop ? s.crop.toUpperCase() : "Crop"} | ${s.topic || "Agronomy"} (Match: ${(s.similarity_score * 100).toFixed(1)}%)`;
                      return (
                        <span key={sIdx} className="source-chip" title={s.source || "Knowledge Base"}>
                          {label}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Suggested Follow-up Questions */}
            {msg.suggestedQuestions && msg.suggestedQuestions.length > 0 && (
              <div className="suggested-questions">
                <span className="suggested-title">💡 Suggested questions:</span>
                <div className="suggested-chips">
                  {msg.suggestedQuestions.map((q, qIdx) => (
                    <button
                      key={qIdx}
                      className="suggested-chip"
                      onClick={() => sendMessage(q)}
                      disabled={loading}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message assistant loading-bubble">
            <span className="dot-pulse">● ● ●</span> Consulting verified agricultural vector database...
          </div>
        )}

        {error && <div className="error-message">⚠️ {error}</div>}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="chat-input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !loading && sendMessage()}
          placeholder={
            selectedCrop 
              ? `Ask a question about ${selectedCrop.toUpperCase()}...` 
              : "Ask about Mango, Coconut, Sugarcane, Tobacco, or Rice..."
          }
          disabled={loading}
        />
        <button onClick={() => sendMessage()} disabled={loading || !input.trim()}>
          Send Query
        </button>
      </div>
    </div>
  )
}

export default App
