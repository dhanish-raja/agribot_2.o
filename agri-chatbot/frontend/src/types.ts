export interface User {
  id: string;
  name: string;
  email: string;
  role: "Farmer" | "Agronomist" | "KVK Extension Officer" | "Researcher";
  farmLocation: string;
  primaryCrop: string;
  language: string;
}

export interface SourceItem {
  crop?: string;
  topic?: string;
  similarity_score?: number;
  source?: string;
  source_url?: string;
}

export interface Message {
  id: string;
  text: string;
  sender: "user" | "assistant";
  timestamp: number;
  crop?: string;
  sources?: (SourceItem | string)[];
  suggestedQuestions?: string[];
  confidence?: "High" | "Medium" | "Low" | string;
  imageUrl?: string;
  feedback?: "up" | "down" | null;
  audioBase64?: string;
  detectedLanguage?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  cropFilter?: string;
  messages: Message[];
}

export interface CropOption {
  id: string;
  label: string;
  emoji: string;
  color: string;
}

export const CROPS: CropOption[] = [
  { id: "", label: "All Crops", emoji: "🌱", color: "#16a34a" },
  { id: "mango", label: "Mango", emoji: "🥭", color: "#ea580c" },
  { id: "coconut", label: "Coconut", emoji: "🥥", color: "#854d0e" },
  { id: "sugarcane", label: "Sugarcane", emoji: "🎋", color: "#15803d" },
  { id: "tobacco", label: "Tobacco", emoji: "🍂", color: "#b45309" },
  { id: "rice", label: "Rice", emoji: "🌾", color: "#0284c7" }
];
