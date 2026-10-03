import { ChatSession, User } from "./types";

const SESSIONS_KEY = "agribot_chat_sessions_v1";
const ACTIVE_SESSION_KEY = "agribot_active_session_id_v1";
const USER_KEY = "agribot_user_profile_v1";
const THEME_KEY = "agribot_theme_v1";

export const DEFAULT_USER: User = {
  id: "farmer-default-1",
  name: "Ramesh Patel",
  email: "ramesh.patel@kisan.in",
  role: "Farmer",
  farmLocation: "Guntur, Andhra Pradesh",
  primaryCrop: "rice",
  language: "English"
};

export function createDefaultSession(): ChatSession {
  const now = Date.now();
  return {
    id: `session_${now}_${Math.random().toString(36).substr(2, 6)}`,
    title: "New Agronomy Chat",
    createdAt: now,
    updatedAt: now,
    cropFilter: "",
    messages: [
      {
        id: `msg_welcome_${now}`,
        text: "Namaste! I am **AgriBot 2.0**, your enterprise agricultural AI assistant backed by ICAR, TNAU, and State Agricultural University knowledge bases.\n\nI can diagnose pests, recommend fertilizer schedules, and guide disease treatment for **Mango, Coconut, Sugarcane, Tobacco, and Rice**.\n\nHow may I assist your farm today?",
        sender: "assistant",
        timestamp: now,
        confidence: "High",
        suggestedQuestions: [
          "How to control bacterial leaf blight in rice?",
          "What is the recommended fertilizer schedule for coconut trees?",
          "How to identify and manage red rot disease in sugarcane?",
          "What are the control measures for mango fruit fly?"
        ]
      }
    ]
  };
}

export function loadSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY);
    if (!raw) {
      const def = createDefaultSession();
      saveSessions([def]);
      return [def];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : [createDefaultSession()];
  } catch {
    return [createDefaultSession()];
  }
}

export function saveSessions(sessions: ChatSession[]): void {
  try {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
  } catch (err) {
    console.error("Failed to save sessions to localStorage:", err);
  }
}

export function loadActiveSessionId(): string | null {
  try {
    return localStorage.getItem(ACTIVE_SESSION_KEY);
  } catch {
    return null;
  }
}

export function saveActiveSessionId(id: string): void {
  try {
    localStorage.setItem(ACTIVE_SESSION_KEY, id);
  } catch (err) {
    console.error("Failed to save active session ID:", err);
  }
}

export function loadUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function saveUser(user: User): void {
  try {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch (err) {
    console.error("Failed to save user profile:", err);
  }
}

export function logoutUser(): void {
  try {
    localStorage.removeItem(USER_KEY);
  } catch (err) {
    console.error("Failed to remove user profile:", err);
  }
}

export function loadTheme(): "dark" | "light" {
  try {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === "dark" || saved === "light") return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  } catch {
    return "light";
  }
}

export function saveTheme(theme: "dark" | "light"): void {
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch (err) {
    console.error("Failed to save theme:", err);
  }
}
