import { useState, useRef, useEffect, type ChangeEvent, type KeyboardEvent } from "react";
import { 
  Send, 
  Mic, 
  MicOff, 
  Image as ImageIcon, 
  X, 
  Loader2
} from "lucide-react";

interface ChatComposerProps {
  onSendMessage: (text: string, imageBase64?: string) => void;
  loading: boolean;
  selectedCrop: string;
}

export const ChatComposer = ({
  onSendMessage,
  loading,
  selectedCrop
}: ChatComposerProps) => {
  const [input, setInput] = useState("");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  // Voice-to-Text initialization
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-IN"; // Default to Indian English

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(prev => (prev ? `${prev} ${transcript}` : transcript));
        setIsListening(false);
      };

      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognitionRef.current = recognition;
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert("Voice speech recognition is not supported in this browser.");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        setIsListening(false);
      }
    }
  };

  const handleImageSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert("Please upload a valid image file.");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setSelectedImage(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveImage = () => {
    setSelectedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = input.trim();
    if ((!trimmed && !selectedImage) || loading) return;

    onSendMessage(trimmed || "Please analyze this crop leaf image for disease diagnosis.", selectedImage || undefined);
    setInput("");
    setSelectedImage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  return (
    <div className="chat-composer-wrap">
      {/* Attached image preview banner */}
      {selectedImage && (
        <div className="composer-image-preview">
          <div className="preview-img-box">
            <img src={selectedImage} alt="Crop Leaf Upload" />
            <button className="remove-preview-btn" onClick={handleRemoveImage} title="Remove image">
              <X size={14} />
            </button>
          </div>
          <div className="preview-img-meta">
            <span className="preview-tag">Leaf Photo Attached</span>
            <span className="preview-sub">Ready for visual diagnosis</span>
          </div>
        </div>
      )}

      {/* Main Input Box */}
      <div className={`composer-box ${loading ? "disabled" : ""}`}>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            selectedCrop 
              ? `Ask anything about ${selectedCrop.toUpperCase()} management, pests, or fertilizers...` 
              : "Ask AgriBot any crop question (or describe leaf symptoms)..."
          }
          rows={1}
          disabled={loading}
        />

        {/* Action Buttons on right */}
        <div className="composer-actions">
          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageSelect}
            accept="image/*"
            style={{ display: "none" }}
          />

          {/* Upload Image Button */}
          <button
            type="button"
            className={`tool-btn ${selectedImage ? "active" : ""}`}
            onClick={() => fileInputRef.current?.click()}
            title="Upload Crop/Leaf Photo for Diagnosis"
            disabled={loading}
          >
            <ImageIcon size={19} />
          </button>

          {/* Voice Input Button */}
          <button
            type="button"
            className={`tool-btn ${isListening ? "listening" : ""}`}
            onClick={toggleListening}
            title={isListening ? "Listening... click to stop" : "Voice input (Speak your question)"}
            disabled={loading}
          >
            {isListening ? <MicOff size={19} /> : <Mic size={19} />}
          </button>

          {/* Send Button */}
          <button
            type="button"
            className="send-btn"
            onClick={handleSend}
            disabled={loading || (!input.trim() && !selectedImage)}
            title="Send Message (Enter)"
          >
            {loading ? <Loader2 size={18} className="spinner" /> : <Send size={18} />}
          </button>
        </div>
      </div>

      {/* Enterprise Disclaimer Footer */}
      <div className="composer-disclaimer">
        <span>
          AgriBot 2.0 synthesizes verified ICAR & Agricultural University guidance. Always verify chemical spray dosages with local Krishi Vigyan Kendra (KVK) officers.
        </span>
      </div>
    </div>
  );
};
