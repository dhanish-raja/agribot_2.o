import { useState, type FormEvent } from "react";
import { X, User, MapPin, Sprout, ShieldCheck, Globe, CheckCircle2, LogOut } from "lucide-react";
import { User as UserType } from "../types";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserType;
  onSaveUser: (user: UserType) => void;
}

export const AuthModal = ({
  isOpen,
  onClose,
  currentUser,
  onSaveUser
}: AuthModalProps) => {
  const [activeTab, setActiveTab] = useState<"profile" | "login">("profile");
  const [formData, setFormData] = useState<UserType>({ ...currentUser });
  const [saveSuccess, setSaveSuccess] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSaveUser(formData);
    setSaveSuccess(true);
    setTimeout(() => {
      setSaveSuccess(false);
      onClose();
    }, 1200);
  };

  const handleQuickGuest = () => {
    const guestUser: UserType = {
      id: `guest_${Date.now()}`,
      name: "Guest Farmer",
      email: "guest.farmer@agribot.in",
      role: "Farmer",
      farmLocation: "Karnataka, India",
      primaryCrop: "all",
      language: "English"
    };
    onSaveUser(guestUser);
    onClose();
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container" onClick={e => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-row">
            <div className="modal-icon-badge">
              <User size={20} />
            </div>
            <div>
              <h3>Enterprise Farmer Profile</h3>
              <p>Personalize crop diagnostics & regional agronomy</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="modal-tabs">
          <button 
            className={`modal-tab ${activeTab === "profile" ? "active" : ""}`}
            onClick={() => setActiveTab("profile")}
          >
            Farmer Details
          </button>
          <button 
            className={`modal-tab ${activeTab === "login" ? "active" : ""}`}
            onClick={() => setActiveTab("login")}
          >
            Account & Sign In
          </button>
        </div>

        {/* Modal Body */}
        {activeTab === "profile" ? (
          <form onSubmit={handleSubmit} className="modal-form">
            <div className="form-grid">
              <div className="form-group">
                <label>Full Name</label>
                <div className="input-with-icon">
                  <User size={16} />
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Ramesh Patel"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Email Address</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={e => setFormData({ ...formData, email: e.target.value })}
                  placeholder="ramesh@agrofarm.in"
                />
              </div>

              <div className="form-group">
                <label>Professional Role</label>
                <select
                  value={formData.role}
                  onChange={e => setFormData({ ...formData, role: e.target.value as any })}
                >
                  <option value="Farmer">Farmer / Cultivator</option>
                  <option value="Agronomist">Agronomist / Consultant</option>
                  <option value="KVK Extension Officer">KVK Extension Officer</option>
                  <option value="Researcher">Agricultural Researcher</option>
                </select>
              </div>

              <div className="form-group">
                <label>Farm Location / District</label>
                <div className="input-with-icon">
                  <MapPin size={16} />
                  <input
                    type="text"
                    value={formData.farmLocation}
                    onChange={e => setFormData({ ...formData, farmLocation: e.target.value })}
                    placeholder="e.g. Guntur, Andhra Pradesh"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Primary Crop of Focus</label>
                <div className="input-with-icon">
                  <Sprout size={16} />
                  <select
                    value={formData.primaryCrop}
                    onChange={e => setFormData({ ...formData, primaryCrop: e.target.value })}
                  >
                    <option value="">🌱 All 5 Supported Crops</option>
                    <option value="mango">🥭 Mango</option>
                    <option value="coconut">🥥 Coconut</option>
                    <option value="sugarcane">🎋 Sugarcane</option>
                    <option value="tobacco">🍂 Tobacco</option>
                    <option value="rice">🌾 Rice</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Preferred Language</label>
                <div className="input-with-icon">
                  <Globe size={16} />
                  <select
                    value={formData.language}
                    onChange={e => setFormData({ ...formData, language: e.target.value })}
                  >
                    <option value="English">English</option>
                    <option value="Hindi">हिंदी (Hindi)</option>
                    <option value="Telugu">తెలుగు (Telugu)</option>
                    <option value="Tamil">தமிழ் (Tamil)</option>
                    <option value="Kannada">ಕನ್ನಡ (Kannada)</option>
                    <option value="Marathi">मराठी (Marathi)</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={handleQuickGuest}>
                Continue as Guest
              </button>
              <button type="submit" className="btn-primary" disabled={saveSuccess}>
                {saveSuccess ? (
                  <>
                    <CheckCircle2 size={16} /> Saved Successfully
                  </>
                ) : (
                  "Save Profile"
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="account-tab-content">
            <div className="auth-account-badge">
              <div className="auth-avatar-large">
                {currentUser.name.charAt(0).toUpperCase()}
              </div>
              <h4>{currentUser.name}</h4>
              <p>{currentUser.email}</p>
              <span className="auth-status-pill">
                <ShieldCheck size={14} /> Active Session Verified
              </span>
            </div>

            <div className="account-details-list">
              <div className="detail-row">
                <span>Account Role:</span>
                <strong>{currentUser.role}</strong>
              </div>
              <div className="detail-row">
                <span>Location:</span>
                <strong>{currentUser.farmLocation}</strong>
              </div>
              <div className="detail-row">
                <span>Language:</span>
                <strong>{currentUser.language}</strong>
              </div>
            </div>

            <div className="modal-actions">
              <button 
                type="button" 
                className="btn-danger" 
                onClick={() => {
                  handleQuickGuest();
                }}
              >
                <LogOut size={16} /> Switch to Guest Account
              </button>
              <button type="button" className="btn-primary" onClick={onClose}>
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
