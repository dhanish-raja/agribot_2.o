import { useState, type FormEvent } from "react";
import { 
  X, 
  User, 
  MapPin, 
  Sprout, 
  ShieldCheck, 
  Globe, 
  CheckCircle2, 
  LogOut, 
  KeyRound, 
  AlertCircle,
  Eye,
  EyeOff
} from "lucide-react";
import { User as UserType } from "../types";
import { changeAccountPassword } from "../auth";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserType;
  onSaveUser: (user: UserType) => void;
  onLogout?: () => void;
}

export const AuthModal = ({
  isOpen,
  onClose,
  currentUser,
  onSaveUser,
  onLogout
}: AuthModalProps) => {
  const [activeTab, setActiveTab] = useState<"profile" | "account" | "password">("profile");
  const [formData, setFormData] = useState<UserType>({ ...currentUser });
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Change Password State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [pwdError, setPwdError] = useState<string | null>(null);
  const [pwdSuccess, setPwdSuccess] = useState<string | null>(null);
  const [pwdLoading, setPwdLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSaveUser(formData);
    setSaveSuccess(true);
    setTimeout(() => {
      setSaveSuccess(false);
      onClose();
    }, 1000);
  };

  const handleChangePassword = async (e: FormEvent) => {
    e.preventDefault();
    setPwdError(null);
    setPwdSuccess(null);

    if (!currentPassword) {
      setPwdError("Please enter your current password.");
      return;
    }
    if (newPassword.length < 6) {
      setPwdError("New password must be at least 6 characters long.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwdError("New passwords do not match.");
      return;
    }

    setPwdLoading(true);
    try {
      const result = await changeAccountPassword(currentUser.email, currentPassword, newPassword);
      if (!result.success) {
        setPwdError(result.error || "Failed to change password.");
      } else {
        setPwdSuccess("Password updated successfully!");
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
      }
    } catch {
      setPwdError("An error occurred while changing your password.");
    } finally {
      setPwdLoading(false);
    }
  };

  const handleLogoutAction = () => {
    onClose();
    if (onLogout) {
      onLogout();
    }
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
            className={`modal-tab ${activeTab === "account" ? "active" : ""}`}
            onClick={() => setActiveTab("account")}
          >
            Account Status
          </button>
          <button 
            className={`modal-tab ${activeTab === "password" ? "active" : ""}`}
            onClick={() => setActiveTab("password")}
          >
            Change Password
          </button>
        </div>

        {/* Tab 1: Farmer Details Form */}
        {activeTab === "profile" && (
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
                <label>Email Address (Account Identifier)</label>
                <input
                  type="email"
                  disabled
                  value={formData.email}
                  title="Email cannot be changed once registered"
                  style={{ opacity: 0.75, cursor: "not-allowed" }}
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
                <label>Preferred Advisory Language</label>
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
              <button type="button" className="btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="btn-primary" disabled={saveSuccess}>
                {saveSuccess ? (
                  <>
                    <CheckCircle2 size={16} /> Saved Successfully
                  </>
                ) : (
                  "Save Changes"
                )}
              </button>
            </div>
          </form>
        )}

        {/* Tab 2: Account Status & Logout */}
        {activeTab === "account" && (
          <div className="account-tab-content">
            <div className="auth-account-badge">
              <div className="auth-avatar-large">
                {currentUser.name.charAt(0).toUpperCase()}
              </div>
              <h4>{currentUser.name}</h4>
              <p>{currentUser.email}</p>
              <span className="auth-status-pill">
                <ShieldCheck size={14} /> Registered Enterprise Session Active
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
                <span>Crop Focus:</span>
                <strong>{currentUser.primaryCrop ? currentUser.primaryCrop.toUpperCase() : "All Crops"}</strong>
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
                onClick={handleLogoutAction}
              >
                <LogOut size={16} /> Sign Out of Account
              </button>
              <button type="button" className="btn-primary" onClick={onClose}>
                Done
              </button>
            </div>
          </div>
        )}

        {/* Tab 3: Security & Change Password */}
        {activeTab === "password" && (
          <form onSubmit={handleChangePassword} className="modal-form">
            {pwdError && (
              <div className="modal-error-banner">
                <AlertCircle size={16} />
                <span>{pwdError}</span>
              </div>
            )}
            {pwdSuccess && (
              <div className="modal-success-banner">
                <CheckCircle2 size={16} />
                <span>{pwdSuccess}</span>
              </div>
            )}

            <div className="form-group" style={{ marginBottom: "14px" }}>
              <label>Current Password</label>
              <div className="input-with-icon">
                <KeyRound size={16} />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="Enter current password"
                  value={currentPassword}
                  onChange={e => { setCurrentPassword(e.target.value); setPwdError(null); }}
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: "14px" }}>
              <label>New Password (Min 6 characters)</label>
              <div className="input-with-icon">
                <KeyRound size={16} />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="Enter new password"
                  value={newPassword}
                  onChange={e => { setNewPassword(e.target.value); setPwdError(null); }}
                />
                <button
                  type="button"
                  className="eye-inline-btn"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: "14px" }}>
              <label>Confirm New Password</label>
              <div className="input-with-icon">
                <KeyRound size={16} />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="Re-enter new password"
                  value={confirmPassword}
                  onChange={e => { setConfirmPassword(e.target.value); setPwdError(null); }}
                />
              </div>
            </div>

            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={onClose}>
                Close
              </button>
              <button type="submit" className="btn-primary" disabled={pwdLoading}>
                {pwdLoading ? "Updating..." : "Update Password"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
