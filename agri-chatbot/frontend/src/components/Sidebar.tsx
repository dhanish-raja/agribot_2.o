import { useState, type MouseEvent } from "react";
import { 
  Plus, 
  MessageSquare, 
  Search, 
  Trash2, 
  Edit2, 
  Check, 
  X, 
  Settings, 
  ChevronLeft, 
  ChevronRight, 
  Sprout, 
  ShieldCheck 
} from "lucide-react";
import { ChatSession, User } from "../types";

interface SidebarProps {
  sessions: ChatSession[];
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string) => void;
  onRenameSession: (id: string, newTitle: string) => void;
  user: User;
  onOpenAuth: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onRenameSession,
  user,
  onOpenAuth,
  isCollapsed,
  onToggleCollapse
}: SidebarProps) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const filteredSessions = sessions.filter(s => 
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const startRename = (s: ChatSession, e: MouseEvent) => {
    e.stopPropagation();
    setEditingId(s.id);
    setEditTitle(s.title);
  };

  const saveRename = (id: string, e: MouseEvent) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      onRenameSession(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const cancelRename = (e: MouseEvent) => {
    e.stopPropagation();
    setEditingId(null);
  };

  // Group sessions by date
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;
  const todaySessions = filteredSessions.filter(s => now - s.updatedAt < oneDay);
  const olderSessions = filteredSessions.filter(s => now - s.updatedAt >= oneDay);

  if (isCollapsed) {
    return (
      <aside className="sidebar collapsed">
        <div className="sidebar-top">
          <button 
            className="icon-btn collapse-toggle" 
            onClick={onToggleCollapse} 
            title="Expand Sidebar"
          >
            <ChevronRight size={18} />
          </button>
          <button 
            className="new-chat-btn-mini" 
            onClick={onNewSession} 
            title="Start New Chat"
          >
            <Plus size={20} />
          </button>
        </div>
        <div className="sidebar-bottom">
          <button 
            className="user-avatar-mini" 
            onClick={onOpenAuth} 
            title={`${user.name} (${user.role})`}
          >
            {user.name.charAt(0).toUpperCase()}
          </button>
        </div>
      </aside>
    );
  }

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-badge">
          <div className="brand-logo">
            <Sprout size={22} className="brand-icon" />
          </div>
          <div className="brand-text">
            <h2>AgriBot <span>2.0</span></h2>
            <div className="brand-sub">
              <ShieldCheck size={12} />
              <span>ICAR Verified Enterprise</span>
            </div>
          </div>
        </div>
        <button 
          className="icon-btn collapse-toggle" 
          onClick={onToggleCollapse} 
          title="Collapse Sidebar"
        >
          <ChevronLeft size={18} />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="sidebar-action">
        <button className="new-chat-btn" onClick={onNewSession}>
          <Plus size={18} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="sidebar-search">
        <Search size={15} className="search-icon" />
        <input
          type="text"
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        {searchQuery && (
          <button className="search-clear" onClick={() => setSearchQuery("")}>
            <X size={13} />
          </button>
        )}
      </div>

      {/* Chat Sessions List */}
      <div className="sidebar-sessions">
        {todaySessions.length > 0 && (
          <div className="session-group">
            <span className="group-label">Today</span>
            {todaySessions.map(s => renderSessionItem(s))}
          </div>
        )}

        {olderSessions.length > 0 && (
          <div className="session-group">
            <span className="group-label">Previous 7 Days</span>
            {olderSessions.map(s => renderSessionItem(s))}
          </div>
        )}

        {filteredSessions.length === 0 && (
          <div className="no-sessions">
            <p>No conversations found</p>
          </div>
        )}
      </div>

      {/* User Footer Profile */}
      <div className="sidebar-footer">
        <div className="user-profile-card" onClick={onOpenAuth}>
          <div className="user-avatar">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div className="user-info">
            <div className="user-name">{user.name}</div>
            <div className="user-role">{user.role} • {user.farmLocation.split(",")[0]}</div>
          </div>
          <Settings size={16} className="settings-icon" />
        </div>
      </div>
    </aside>
  );

  function renderSessionItem(s: ChatSession) {
    const isActive = s.id === activeSessionId;
    const isEditing = editingId === s.id;

    return (
      <div
        key={s.id}
        className={`session-item ${isActive ? "active" : ""}`}
        onClick={() => onSelectSession(s.id)}
      >
        <MessageSquare size={16} className="session-icon" />

        {isEditing ? (
          <div className="inline-edit-box">
            <input
              type="text"
              value={editTitle}
              autoFocus
              onChange={e => setEditTitle(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter") saveRename(s.id, e as any);
                if (e.key === "Escape") cancelRename(e as any);
              }}
              onClick={e => e.stopPropagation()}
            />
            <button className="save-btn" onClick={e => saveRename(s.id, e)}>
              <Check size={14} />
            </button>
            <button className="cancel-btn" onClick={cancelRename}>
              <X size={14} />
            </button>
          </div>
        ) : (
          <>
            <span className="session-title" title={s.title}>{s.title}</span>
            <div className="session-actions">
              <button 
                className="action-btn" 
                onClick={e => startRename(s, e)} 
                title="Rename conversation"
              >
                <Edit2 size={13} />
              </button>
              {sessions.length > 1 && (
                <button 
                  className="action-btn delete" 
                  onClick={e => {
                    e.stopPropagation();
                    onDeleteSession(s.id);
                  }} 
                  title="Delete conversation"
                >
                  <Trash2 size={13} />
                </button>
              )}
            </div>
          </>
        )}
      </div>
    );
  }
};
