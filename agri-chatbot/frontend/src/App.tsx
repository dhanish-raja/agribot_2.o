import { useState, useEffect, useRef } from "react";
import "./App.css";
import { 
  ChatSession, 
  Message, 
  User as UserType 
} from "./types";
import { 
  loadSessions, 
  saveSessions, 
  createDefaultSession, 
  loadActiveSessionId, 
  saveActiveSessionId, 
  loadUser, 
  saveUser, 
  logoutUser,
  loadTheme, 
  saveTheme 
} from "./storage";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { ChatMessage } from "./components/ChatMessage";
import { ChatComposer } from "./components/ChatComposer";
import { WelcomeHero } from "./components/WelcomeHero";
import { AuthModal } from "./components/AuthModal";
import { AuthScreen } from "./components/AuthScreen";

export default function App() {
  // Persistence state
  const [sessions, setSessions] = useState<ChatSession[]>(loadSessions);
  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    const saved = loadActiveSessionId();
    const existing = sessions.find(s => s.id === saved);
    return existing ? existing.id : sessions[0].id;
  });
  const [user, setUser] = useState<UserType | null>(loadUser);
  const [theme, setTheme] = useState<"dark" | "light">(loadTheme);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Runtime state
  const [loading, setLoading] = useState(false);
  const [activeBackend, setActiveBackend] = useState<string>("Connecting...");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const AI_BASE_URL = import.meta.env.VITE_AI_SERVICE_URL || "http://localhost:8000";

  // Active Session helper
  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];
  const selectedCrop = activeSession?.cropFilter || "";

  // Apply theme to document element
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    saveTheme(theme);
  }, [theme]);

  // Persist sessions whenever they change
  useEffect(() => {
    saveSessions(sessions);
  }, [sessions]);

  // Persist active session ID
  useEffect(() => {
    saveActiveSessionId(activeSessionId);
  }, [activeSessionId]);

  // Auto-scroll to bottom of message list
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeSession?.messages, loading]);

  // Backend Health Check
  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      // 1. Try local Spring Boot Gateway first
      try {
        const res = await fetch("http://localhost:8080/api/health");
        if (res.ok && isMounted) {
          setActiveBackend("Spring Boot Gateway (:8080)");
          return;
        }
      } catch {}

      // 2. Try FastAPI Cloud AI Engine
      try {
        const res = await fetch(`${AI_BASE_URL}/health`);
        if (res.ok && isMounted) {
          const data = await res.json();
          const count = data.total_vectors || 1515;
          setActiveBackend(`AI Engine Online (${count} vectors)`);
          return;
        }
      } catch {}

      if (isMounted) setActiveBackend("AI Engine / Gateway Offline");
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [AI_BASE_URL]);

  // Toggle Theme
  const handleToggleTheme = () => {
    setTheme(prev => (prev === "dark" ? "light" : "dark"));
  };

  // User Profile & Auth
  const handleLogin = (authenticatedUser: UserType) => {
    setUser(authenticatedUser);
    saveUser(authenticatedUser);
  };

  const handleLogout = () => {
    logoutUser();
    setUser(null);
  };

  const handleSaveUser = (updatedUser: UserType) => {
    setUser(updatedUser);
    saveUser(updatedUser);
  };

  // Crop Filter Selection
  const handleSelectCrop = (cropId: string) => {
    setSessions(prev =>
      prev.map(s => (s.id === activeSessionId ? { ...s, cropFilter: cropId } : s))
    );
  };

  // Session Handlers
  const handleNewSession = () => {
    const newSession = createDefaultSession();
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
  };

  const handleDeleteSession = (id: string) => {
    if (sessions.length <= 1) return;
    const filtered = sessions.filter(s => s.id !== id);
    setSessions(filtered);
    if (activeSessionId === id) {
      setActiveSessionId(filtered[0].id);
    }
  };

  const handleRenameSession = (id: string, newTitle: string) => {
    setSessions(prev =>
      prev.map(s => (s.id === id ? { ...s, title: newTitle, updatedAt: Date.now() } : s))
    );
  };

  const handleClearChat = () => {
    if (!confirm("Are you sure you want to clear this conversation?")) return;
    setSessions(prev =>
      prev.map(s => {
        if (s.id === activeSessionId) {
          return {
            ...s,
            messages: [
              {
                id: `msg_welcome_${Date.now()}`,
                text: "Conversation cleared. How can I help with your crops now?",
                sender: "assistant",
                timestamp: Date.now(),
                suggestedQuestions: [
                  "What are the 5 major crops supported by AgriBot?",
                  "How to manage blast disease in Rice?",
                  "What is the fertilizer schedule for Coconut?"
                ]
              }
            ],
            updatedAt: Date.now()
          };
        }
        return s;
      })
    );
  };

  // Export Conversation as Markdown
  const handleExportChat = () => {
    if (!activeSession || !user) return;
    const dateStr = new Date(activeSession.createdAt).toLocaleDateString();
    let md = `# AgriBot 2.0 Advisory Transcript\n\n`;
    md += `**Date:** ${dateStr}\n`;
    md += `**Farmer / User:** ${user.name} (${user.role})\n`;
    md += `**Farm Location:** ${user.farmLocation}\n`;
    md += `**Topic:** ${activeSession.title}\n`;
    md += `**Crop Focus:** ${activeSession.cropFilter || "All Supported Crops"}\n\n`;
    md += `---\n\n`;

    activeSession.messages.forEach(m => {
      const time = new Date(m.timestamp).toLocaleTimeString();
      if (m.sender === "user") {
        md += `### 🧑‍🌾 Farmer (${time})\n${m.text}\n\n`;
      } else {
        md += `### 🤖 AgriBot Advisory (${time})\n${m.text}\n\n`;
        if (m.sources && m.sources.length > 0) {
          md += `*Sources & Citations:*\n`;
          m.sources.forEach(src => {
            if (typeof src === "string") md += `- ${src}\n`;
            else md += `- **${src.crop || "General"}**: ${src.topic} (${src.source})\n`;
          });
          md += `\n`;
        }
      }
    });

    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `AgriBot_${activeSession.title.replace(/\s+/g, "_")}_${Date.now()}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Message Feedback (Thumbs Up / Down)
  const handleMessageFeedback = (messageId: string, feedback: "up" | "down") => {
    setSessions(prev =>
      prev.map(s => {
        if (s.id !== activeSessionId) return s;
        return {
          ...s,
          messages: s.messages.map(m =>
            m.id === messageId ? { ...m, feedback: m.feedback === feedback ? null : feedback } : m
          )
        };
      })
    );
  };

  // Send Message Logic
  const handleSendMessage = async (textToSend: string, imageBase64?: string) => {
    const query = textToSend.trim();
    if (!query && !imageBase64) return;

    const userMsgId = `msg_user_${Date.now()}`;
    const userMessage: Message = {
      id: userMsgId,
      text: query,
      sender: "user",
      timestamp: Date.now(),
      crop: selectedCrop,
      imageUrl: imageBase64
    };

    // Auto-update session title if it's the default title
    const isFirstQuestion = activeSession.messages.length <= 1;
    const newTitle = isFirstQuestion ? query.slice(0, 32) + (query.length > 32 ? "..." : "") : activeSession.title;

    // Append user message immediately
    setSessions(prev =>
      prev.map(s => {
        if (s.id !== activeSessionId) return s;
        return {
          ...s,
          title: newTitle,
          updatedAt: Date.now(),
          messages: [...s.messages, userMessage]
        };
      })
    );

    setLoading(true);

    // Map user language to Sarvam AI language code
    const langCodeMap: Record<string, string> = {
      "Telugu": "te-IN",
      "Hindi": "hi-IN",
      "Tamil": "ta-IN",
      "Kannada": "kn-IN",
      "Marathi": "mr-IN",
      "English": "en-IN"
    };
    const preferredLangCode = user?.language ? langCodeMap[user.language] || undefined : undefined;

    const payload = {
      message: query,
      query: query,
      crop: selectedCrop || undefined,
      sessionId: activeSessionId,
      language: preferredLangCode,
      enable_audio: false
    };

    try {
      let data: any = null;

      // 1. Try Spring Boot Gateway (:8080)
      try {
        const springRes = await fetch("http://localhost:8080/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (springRes.ok) {
          data = await springRes.json();
          setActiveBackend("Spring Boot Gateway (:8080)");
        }
      } catch {}

      // 2. Direct FastAPI AI Cloud Service
      if (!data) {
        const aiRes = await fetch(`${AI_BASE_URL}/rag/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!aiRes.ok) throw new Error(`AI service responded with HTTP ${aiRes.status}`);
        data = await aiRes.json();
      }

      const botMessage: Message = {
        id: `msg_bot_${Date.now()}`,
        text: data.answer || "No response received.",
        sender: "assistant",
        timestamp: Date.now(),
        crop: data.crop || selectedCrop,
        confidence: data.confidence || "Medium",
        sources: data.sources || [],
        suggestedQuestions: data.suggested_questions || data.suggestedQuestions || [],
        audioBase64: data.audio_base64 || undefined,
        detectedLanguage: data.detected_language || preferredLangCode || "en-IN"
      };

      setSessions(prev =>
        prev.map(s => {
          if (s.id !== activeSessionId) return s;
          return {
            ...s,
            updatedAt: Date.now(),
            messages: [...s.messages, botMessage]
          };
        })
      );
    } catch (err: any) {
      const errorMsg: Message = {
        id: `msg_err_${Date.now()}`,
        text: `⚠️ **Connection Error**: Unable to reach AI cloud engine (${err.message}). Please ensure your network is active or backend services are up.`,
        sender: "assistant",
        timestamp: Date.now(),
        confidence: "Low"
      };
      setSessions(prev =>
        prev.map(s => (s.id === activeSessionId ? { ...s, messages: [...s.messages, errorMsg] } : s))
      );
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <AuthScreen onLogin={handleLogin} />;
  }

  const showWelcomeHero = activeSession.messages.length <= 1;

  return (
    <div className={`app-layout ${isSidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={id => setActiveSessionId(id)}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
        user={user}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* Main Chat Workspace */}
      <main className="main-content">
        <Header
          onToggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          title={activeSession.title}
          selectedCrop={selectedCrop}
          onSelectCrop={handleSelectCrop}
          theme={theme}
          onToggleTheme={handleToggleTheme}
          backendStatus={activeBackend}
          onExportChat={handleExportChat}
          onClearChat={handleClearChat}
          user={user}
          onOpenAuth={() => setIsAuthModalOpen(true)}
        />

        {/* Scrollable Conversation Area */}
        <div className="chat-messages-area">
          {showWelcomeHero ? (
            <WelcomeHero
              user={user}
              onSelectPrompt={(prompt, crop) => {
                if (crop) handleSelectCrop(crop);
                handleSendMessage(prompt);
              }}
            />
          ) : (
            <div className="messages-stream">
              {activeSession.messages.map(msg => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onSelectSuggestedQuestion={q => handleSendMessage(q)}
                  onFeedback={handleMessageFeedback}
                />
              ))}

              {loading && (
                <div className="message-row assistant">
                  <div className="message-container">
                    <div className="message-avatar bot-avatar pulsing">
                      🌾
                    </div>
                    <div className="message-bubble typing-bubble">
                      <div className="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                      <span className="typing-label">Consulting ICAR knowledge base & synthesizing advisory...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Floating Chat Composer */}
        <div className="composer-footer-container">
          <ChatComposer
            onSendMessage={handleSendMessage}
            loading={loading}
            selectedCrop={selectedCrop}
          />
        </div>
      </main>

      {/* Enterprise Farmer Profile / Auth Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        currentUser={user}
        onSaveUser={handleSaveUser}
      />
    </div>
  );
}
