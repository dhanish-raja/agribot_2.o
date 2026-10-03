import { 
  Menu, 
  Sun, 
  Moon, 
  Download, 
  RotateCcw
} from "lucide-react";
import { CROPS, User } from "../types";

interface HeaderProps {
  onToggleSidebar: () => void;
  title: string;
  selectedCrop: string;
  onSelectCrop: (cropId: string) => void;
  theme: "dark" | "light";
  onToggleTheme: () => void;
  backendStatus: string;
  onExportChat: () => void;
  onClearChat: () => void;
  user: User;
  onOpenAuth: () => void;
}

export const Header = ({
  onToggleSidebar,
  title,
  selectedCrop,
  onSelectCrop,
  theme,
  onToggleTheme,
  backendStatus,
  onExportChat,
  onClearChat,
  user,
  onOpenAuth
}: HeaderProps) => {
  const isOnline = !backendStatus.toLowerCase().includes("offline");

  return (
    <header className="main-header">
      {/* Left section: Hamburger & Chat Title */}
      <div className="header-left">
        <button 
          className="icon-btn mobile-menu-btn" 
          onClick={onToggleSidebar} 
          title="Toggle Navigation"
        >
          <Menu size={20} />
        </button>
        <div className="active-chat-meta">
          <h1 className="active-chat-title">{title}</h1>
          <div className="system-status-pill">
            <span className={`status-dot ${isOnline ? "online" : "offline"}`} />
            <span className="status-text">{backendStatus}</span>
          </div>
        </div>
      </div>

      {/* Middle section: Crop Filter Chips */}
      <div className="header-crops">
        {CROPS.map(c => {
          const isSelected = selectedCrop === c.id;
          return (
            <button
              key={c.id}
              className={`crop-chip ${isSelected ? "selected" : ""}`}
              onClick={() => onSelectCrop(c.id)}
            >
              <span className="crop-emoji">{c.emoji}</span>
              <span className="crop-name">{c.label}</span>
            </button>
          );
        })}
      </div>

      {/* Right section: Actions (Theme, Export, Clear, Profile) */}
      <div className="header-actions">
        <button 
          className="icon-btn" 
          onClick={onExportChat} 
          title="Export Conversation (.md)"
        >
          <Download size={18} />
        </button>

        <button 
          className="icon-btn" 
          onClick={onClearChat} 
          title="Reset Active Conversation"
        >
          <RotateCcw size={18} />
        </button>

        <button 
          className="icon-btn theme-toggle" 
          onClick={onToggleTheme} 
          title={`Switch to ${theme === "dark" ? "Light" : "Dark"} Mode`}
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <button 
          className="user-pill-btn" 
          onClick={onOpenAuth} 
          title={`Signed in as ${user.name}`}
        >
          <span className="avatar-letter">{user.name.charAt(0).toUpperCase()}</span>
          <span className="user-short-name">{user.name.split(" ")[0]}</span>
        </button>
      </div>
    </header>
  );
};
