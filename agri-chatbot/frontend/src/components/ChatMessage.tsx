import { useState, useRef } from "react";
import { 
  Copy, 
  Check, 
  Volume2, 
  VolumeX, 
  Loader2,
  ThumbsUp, 
  ThumbsDown, 
  ChevronDown, 
  ChevronUp, 
  ShieldCheck, 
  FileText, 
  Sparkles, 
  Bot, 
  User as UserIcon 
} from "lucide-react";
import { Message, SourceItem } from "../types";

interface ChatMessageProps {
  message: Message;
  onSelectSuggestedQuestion: (q: string) => void;
  onFeedback: (messageId: string, feedback: "up" | "down") => void;
}

export const ChatMessage = ({
  message,
  onSelectSuggestedQuestion,
  onFeedback
}: ChatMessageProps) => {
  const [copied, setCopied] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const audioInstanceRef = useRef<HTMLAudioElement | null>(null);

  const AI_BASE_URL = import.meta.env.VITE_AI_SERVICE_URL || "https://agribot-2-o.onrender.com";
  const isAssistant = message.sender === "assistant";

  // Copy message text
  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Sarvam AI Text-to-Speech (Indian Regional Voice)
  const handleSpeak = async () => {
    // If currently playing, stop audio
    if (isPlayingAudio) {
      if (audioInstanceRef.current) {
        audioInstanceRef.current.pause();
        audioInstanceRef.current.currentTime = 0;
      }
      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      setIsPlayingAudio(false);
      return;
    }

    // 1. If audio base64 is already cached on the message, play directly
    if (message.audioBase64) {
      playBase64Audio(message.audioBase64);
      return;
    }

    // 2. Fetch Sarvam AI TTS audio from backend
    setIsLoadingAudio(true);
    try {
      const res = await fetch(`${AI_BASE_URL}/speech/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: message.text,
          language_code: message.detectedLanguage || "en-IN",
          speaker: "kavya"
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.audio_base64) {
          playBase64Audio(data.audio_base64);
          setIsLoadingAudio(false);
          return;
        }
      }
      throw new Error("Sarvam TTS unavailable");
    } catch (err) {
      setIsLoadingAudio(false);
      // Fallback to browser Web Speech API
      if ("speechSynthesis" in window) {
        const cleanText = message.text.replace(/[*#_`>-]/g, "").replace(/\n+/g, ". ");
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 0.95;
        utterance.onend = () => setIsPlayingAudio(false);
        utterance.onerror = () => setIsPlayingAudio(false);
        window.speechSynthesis.speak(utterance);
        setIsPlayingAudio(true);
      }
    }
  };

  const playBase64Audio = (b64: string) => {
    try {
      const audio = new Audio(`data:audio/wav;base64,${b64}`);
      audioInstanceRef.current = audio;
      audio.onended = () => setIsPlayingAudio(false);
      audio.onerror = () => setIsPlayingAudio(false);
      audio.play();
      setIsPlayingAudio(true);
    } catch {
      setIsPlayingAudio(false);
    }
  };

  // Format markdown content
  const renderFormattedContent = (content: string) => {
    const lines = content.split("\n");
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) return <div key={idx} className="md-spacer" />;

      // Header 4
      if (trimmed.startsWith("#### ")) {
        return <h5 key={idx} className="md-h4">{trimmed.replace("#### ", "")}</h5>;
      }
      // Header 3
      if (trimmed.startsWith("### ")) {
        return <h4 key={idx} className="md-h3">{trimmed.replace("### ", "")}</h4>;
      }
      // Header 2
      if (trimmed.startsWith("## ")) {
        return <h3 key={idx} className="md-h2">{trimmed.replace("## ", "")}</h3>;
      }
      // Header 1
      if (trimmed.startsWith("# ")) {
        return <h2 key={idx} className="md-h1">{trimmed.replace("# ", "")}</h2>;
      }

      // Bullet items
      if (trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
        const textPart = trimmed.substring(2);
        return (
          <div key={idx} className="md-bullet-item">
            <span className="bullet-dot">•</span>
            <span dangerouslySetInnerHTML={{ __html: inlineMarkdown(textPart) }} />
          </div>
        );
      }

      // Numbered items
      const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
      if (numMatch) {
        return (
          <div key={idx} className="md-num-item">
            <span className="num-badge">{numMatch[1]}</span>
            <span dangerouslySetInnerHTML={{ __html: inlineMarkdown(numMatch[2]) }} />
          </div>
        );
      }

      // Callout box / Warning Advisory
      if (trimmed.toLowerCase().includes("safety advisory") || trimmed.toLowerCase().includes("caution:") || trimmed.toLowerCase().includes("warning:")) {
        return (
          <div key={idx} className="advisory-callout">
            <ShieldCheck size={18} className="advisory-icon" />
            <div dangerouslySetInnerHTML={{ __html: inlineMarkdown(trimmed) }} />
          </div>
        );
      }

      // Regular paragraph
      return (
        <p key={idx} className="md-paragraph" dangerouslySetInnerHTML={{ __html: inlineMarkdown(trimmed) }} />
      );
    });
  };

  const inlineMarkdown = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
  };

  return (
    <div className={`message-row ${isAssistant ? "assistant" : "user"}`}>
      <div className="message-container">
        {/* Avatar */}
        <div className={`message-avatar ${isAssistant ? "bot-avatar" : "user-avatar"}`}>
          {isAssistant ? <Bot size={20} /> : <UserIcon size={18} />}
        </div>

        {/* Bubble */}
        <div className="message-bubble">
          {/* Header Metadata (for assistant) */}
          {isAssistant && (
            <div className="assistant-meta-bar">
              <div className="meta-left">
                <span className="assistant-name">AgriBot Advisory</span>
                {message.confidence && (
                  <span className={`confidence-badge ${message.confidence.toLowerCase()}`}>
                    <ShieldCheck size={12} />
                    {message.confidence} Confidence
                  </span>
                )}
                {message.crop && (
                  <span className="crop-tag">
                    {message.crop.toUpperCase()}
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Attached image if any */}
          {message.imageUrl && (
            <div className="message-image-preview">
              <img src={message.imageUrl} alt="Uploaded Crop Leaf" />
            </div>
          )}

          {/* Text Content */}
          <div className="message-body">
            {isAssistant ? renderFormattedContent(message.text) : (
              <p className="user-text">{message.text}</p>
            )}
          </div>

          {/* Verified Sources Accordion */}
          {isAssistant && message.sources && message.sources.length > 0 && (
            <div className="sources-container">
              <button 
                className="sources-toggle-btn"
                onClick={() => setShowSources(!showSources)}
              >
                <div className="sources-btn-label">
                  <FileText size={14} />
                  <span>Verified Knowledge Sources ({message.sources.length})</span>
                </div>
                {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              {showSources && (
                <div className="sources-list">
                  {message.sources.map((src, i) => {
                    if (typeof src === "string") {
                      return (
                        <div key={i} className="source-card">
                          <span className="source-name">{src}</span>
                        </div>
                      );
                    }
                    const item = src as SourceItem;
                    const scorePct = item.similarity_score 
                      ? Math.round(item.similarity_score * 100) 
                      : null;

                    return (
                      <div key={i} className="source-card">
                        <div className="source-card-header">
                          <span className="source-crop-tag">{item.crop || "General"}</span>
                          {scorePct && (
                            <span className="source-score-pill">
                              {scorePct}% match
                            </span>
                          )}
                        </div>
                        <div className="source-title">
                          {item.topic || "Agricultural Extension Manual"}
                        </div>
                        <div className="source-doc">
                          {item.source || "ICAR / SAU Standard Package"}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Action Toolbar for Assistant */}
          {isAssistant && (
            <div className="message-actions-bar">
              <button 
                className="action-icon-btn" 
                onClick={handleCopy} 
                title="Copy advisory"
              >
                {copied ? <Check size={14} className="copied-icon" /> : <Copy size={14} />}
                <span className="action-label">{copied ? "Copied" : "Copy"}</span>
              </button>

              <button 
                className={`action-icon-btn ${isPlayingAudio ? "playing" : ""}`} 
                onClick={handleSpeak} 
                disabled={isLoadingAudio}
                title={isPlayingAudio ? "Stop audio" : "Listen via Sarvam AI Indian Voice"}
              >
                {isLoadingAudio ? (
                  <Loader2 size={14} className="spinner" />
                ) : isPlayingAudio ? (
                  <VolumeX size={14} />
                ) : (
                  <Volume2 size={14} />
                )}
                <span className="action-label">
                  {isLoadingAudio ? "Loading Voice..." : isPlayingAudio ? "Stop" : "Listen (Sarvam AI)"}
                </span>
              </button>

              <div className="feedback-group">
                <button 
                  className={`feedback-btn ${message.feedback === "up" ? "active-up" : ""}`}
                  onClick={() => onFeedback(message.id, "up")}
                  title="Helpful recommendation"
                >
                  <ThumbsUp size={13} />
                </button>
                <button 
                  className={`feedback-btn ${message.feedback === "down" ? "active-down" : ""}`}
                  onClick={() => onFeedback(message.id, "down")}
                  title="Not helpful"
                >
                  <ThumbsDown size={13} />
                </button>
              </div>
            </div>
          )}

          {/* Suggested Follow-up Questions */}
          {isAssistant && message.suggestedQuestions && message.suggestedQuestions.length > 0 && (
            <div className="suggested-prompts-section">
              <div className="suggested-header">
                <Sparkles size={13} />
                <span>Suggested Follow-Ups:</span>
              </div>
              <div className="suggested-chips-container">
                {message.suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    className="suggested-chip"
                    onClick={() => onSelectSuggestedQuestion(q)}
                  >
                    <span>{q}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
