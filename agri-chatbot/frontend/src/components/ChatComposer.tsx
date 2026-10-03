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

  const AI_BASE_URL = import.meta.env.VITE_AI_SERVICE_URL || "https://agribot-2-o.onrender.com";
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  const toggleListening = async () => {
    // If currently listening, stop recording and send to Sarvam AI STT
    if (isListening) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
      setIsListening(false);
      return;
    }

    // Start recording audio for Sarvam AI
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      audioChunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        if (audioBlob.size > 1000) {
          setIsProcessingAudio(true);
          try {
            const formData = new FormData();
            formData.append("file", audioBlob, "recording.wav");
            formData.append("model", "saaras:v3");

            const res = await fetch(`${AI_BASE_URL}/speech/stt`, {
              method: "POST",
              body: formData
            });

            if (res.ok) {
              const data = await res.json();
              const spokenText = data.transcript || data.english_query;
              if (spokenText) {
                setInput(prev => (prev ? `${prev} ${spokenText}` : spokenText));
              }
            }
          } catch (err) {
            console.error("Sarvam STT error:", err);
          } finally {
            setIsProcessingAudio(false);
          }
        }
      };

      mediaRecorder.start();
      setIsListening(true);
    } catch (err) {
      // Fallback to browser Web Speech API if microphone access denied or unsupported
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-IN";
        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setInput(prev => (prev ? `${prev} ${transcript}` : transcript));
          setIsListening(false);
        };
        recognition.onerror = () => setIsListening(false);
        recognition.onend = () => setIsListening(false);
        recognition.start();
        setIsListening(true);
      } else {
        alert("Microphone recording is not available. Please allow microphone permissions.");
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
            className={`tool-btn ${isListening ? "listening" : ""} ${isProcessingAudio ? "processing" : ""}`}
            onClick={toggleListening}
            title={
              isProcessingAudio 
                ? "Transcribing voice via Sarvam AI..." 
                : isListening 
                ? "Recording voice... click to stop and transcribe" 
                : "Voice input via Sarvam AI (Speak in Hindi, Telugu, Tamil, English, etc.)"
            }
            disabled={loading || isProcessingAudio}
          >
            {isProcessingAudio ? (
              <Loader2 size={19} className="spinner" />
            ) : isListening ? (
              <MicOff size={19} />
            ) : (
              <Mic size={19} />
            )}
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
