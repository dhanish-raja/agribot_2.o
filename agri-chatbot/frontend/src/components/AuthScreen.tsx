import { useState, useEffect, type FormEvent } from "react";
import { 
  Sprout, 
  ShieldCheck, 
  Lock, 
  Mail, 
  User as UserIcon, 
  MapPin, 
  Globe, 
  ArrowRight, 
  Eye, 
  EyeOff, 
  CheckCircle2, 
  Sparkles,
  Database,
  Volume2,
  AlertCircle,
  KeyRound,
  ArrowLeft,
  Loader2
} from "lucide-react";
import { User } from "../types";
import { 
  authenticateUser, 
  registerAccount, 
  authenticateDemoUser, 
  resetAccountPassword,
  findAccountByEmail,
  initializeAccounts
} from "../auth";

interface AuthScreenProps {
  onLogin: (user: User) => void;
}

type AuthMode = "login" | "register" | "forgot";

export const AuthScreen = ({ onLogin }: AuthScreenProps) => {
  const [mode, setMode] = useState<AuthMode>("login");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [suggestRegisterEmail, setSuggestRegisterEmail] = useState<string | null>(null);

  // Sign In Form State
  const [signInEmail, setSignInEmail] = useState("");
  const [signInPassword, setSignInPassword] = useState("");

  // Register Form State
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<User["role"]>("Farmer");
  const [farmLocation, setFarmLocation] = useState("");
  const [primaryCrop, setPrimaryCrop] = useState("");
  const [language, setLanguage] = useState("English");

  // Forgot Password State
  const [resetEmail, setResetEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [resetStep, setResetStep] = useState<1 | 2>(1);

  // Initialize demo accounts on mount
  useEffect(() => {
    initializeAccounts();
  }, []);

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
    setSuggestRegisterEmail(null);
  };

  const switchToMode = (newMode: AuthMode) => {
    clearMessages();
    setMode(newMode);
    setShowPassword(false);
    setShowConfirmPassword(false);
  };

  // Sign In Handler with Strict Verification
  const handleSignIn = async (e: FormEvent) => {
    e.preventDefault();
    clearMessages();

    if (!signInEmail.trim() || !signInPassword.trim()) {
      setError("Please provide both email and password.");
      return;
    }

    setLoading(true);
    try {
      const result = await authenticateUser(signInEmail, signInPassword);

      if (!result.success || !result.user) {
        if (result.code === "USER_NOT_FOUND") {
          setError(result.error || "No registered account found with this email.");
          setSuggestRegisterEmail(signInEmail.trim());
        } else {
          setError(result.error || "Authentication failed. Please verify your credentials.");
        }
        return;
      }

      setSuccess("✓ Login verified! Redirecting to your agricultural workspace...");
      setTimeout(() => {
        onLogin(result.user!);
      }, 500);
    } catch (err: any) {
      setError(err?.message || "An unexpected error occurred during login.");
    } finally {
      setLoading(false);
    }
  };

  // Registration Handler with Full Account Storage
  const handleRegister = async (e: FormEvent) => {
    e.preventDefault();
    clearMessages();

    if (!name.trim()) {
      setError("Please enter your full name.");
      return;
    }
    if (!email.trim()) {
      setError("Please enter your email address.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match. Please re-enter identical passwords.");
      return;
    }

    setLoading(true);
    try {
      const result = await registerAccount({
        name: name.trim(),
        email: email.trim(),
        password: password,
        role: role,
        farmLocation: farmLocation.trim() || "India",
        primaryCrop: primaryCrop,
        language: language
      });

      if (!result.success || !result.user) {
        setError(result.error || "Registration failed. Please check your information.");
        return;
      }

      setSuccess("✓ Account successfully created! Logging you into AgriBot 2.0...");
      setTimeout(() => {
        onLogin(result.user!);
      }, 700);
    } catch (err: any) {
      setError(err?.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Password Reset Handler
  const handleCheckResetEmail = (e: FormEvent) => {
    e.preventDefault();
    clearMessages();

    if (!resetEmail.trim()) {
      setError("Please enter your registered email address.");
      return;
    }

    const account = findAccountByEmail(resetEmail.trim());
    if (!account) {
      setError(`No account registered with "${resetEmail.trim()}". Please create an account first.`);
      setSuggestRegisterEmail(resetEmail.trim());
      return;
    }

    setResetStep(2);
    setSuccess(`Account located for ${account.name}. Please enter your new password.`);
  };

  const handleCompleteReset = async (e: FormEvent) => {
    e.preventDefault();
    clearMessages();

    if (newPassword.length < 6) {
      setError("New password must be at least 6 characters long.");
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setError("Passwords do not match. Please verify.");
      return;
    }

    setLoading(true);
    try {
      const result = await resetAccountPassword(resetEmail, newPassword);
      if (!result.success) {
        setError(result.error || "Failed to reset password.");
        return;
      }

      setSuccess("✓ Password successfully updated! Please sign in with your new password.");
      setSignInEmail(resetEmail);
      setSignInPassword("");
      setTimeout(() => {
        switchToMode("login");
        setResetStep(1);
        setNewPassword("");
        setConfirmNewPassword("");
      }, 1400);
    } catch (err: any) {
      setError(err?.message || "Password reset failed.");
    } finally {
      setLoading(false);
    }
  };

  // Demo Profile Login
  const handleDemoLogin = async (demoRole: "Agronomist" | "Farmer") => {
    clearMessages();
    setLoading(true);
    try {
      const demoId = demoRole === "Agronomist" ? "demo_agronomist" : "demo_farmer";
      const result = await authenticateDemoUser(demoId);
      if (result.success && result.user) {
        setSuccess(`✓ Signing in as ${result.user.name}...`);
        setTimeout(() => {
          onLogin(result.user!);
        }, 400);
      } else {
        setError("Unable to authenticate demo account.");
      }
    } catch (err: any) {
      setError("Failed to authenticate demo account.");
    } finally {
      setLoading(false);
    }
  };

  // Quick switch from "No account found" to Registration
  const handleTransferToRegister = () => {
    if (suggestRegisterEmail) {
      setEmail(suggestRegisterEmail);
    }
    switchToMode("register");
  };

  return (
    <div className="auth-portal-wrapper">
      <div className="auth-portal-container">
        {/* Left Side: Enterprise Feature Showcase & Branding */}
        <div className="auth-brand-pane">
          <div className="brand-pane-header">
            <div className="brand-logo-large">
              <Sprout size={32} />
            </div>
            <div>
              <h1>AgriBot <span>2.0</span></h1>
              <p className="brand-tagline">Enterprise Agricultural AI Platform</p>
            </div>
          </div>

          <div className="brand-mission">
            <h2>Grounded Agronomy & Pest Intelligence for Modern Farms</h2>
            <p>
              AgriBot bridges certified agricultural science with high-throughput generative AI, powering diagnostics for Rice, Coconut, Sugarcane, Mango, and Tobacco.
            </p>
          </div>

          <div className="features-list">
            <div className="feature-item">
              <div className="feature-icon"><ShieldCheck size={20} /></div>
              <div>
                <h4>Zero Chemical Hallucination</h4>
                <p>Strict grounding against ICAR, TNAU & SAU standard packages of practices.</p>
              </div>
            </div>

            <div className="feature-item">
              <div className="feature-icon"><Database size={20} /></div>
              <div>
                <h4>1,515+ Pre-Indexed Vectors</h4>
                <p>Instant sub-100ms vector retrieval with dynamic live knowledge auto-ingestion.</p>
              </div>
            </div>

            <div className="feature-item">
              <div className="feature-icon"><Volume2 size={20} /></div>
              <div>
                <h4>Hands-Free Multilingual Voice</h4>
                <p>Text-to-speech and microphone audio recognition tailored for field conditions.</p>
              </div>
            </div>
          </div>

          <div className="brand-trust-footer">
            <div className="trust-pill">
              <CheckCircle2 size={15} />
              <span>ICAR & SAU Aligned</span>
            </div>
            <div className="trust-pill">
              <Sparkles size={15} />
              <span>Gemini 2.5 Multi-Modal RAG</span>
            </div>
          </div>
        </div>

        {/* Right Side: Authentication Card */}
        <div className="auth-card-pane">
          <div className="auth-card">
            {/* Tab Switcher (Visible in login & register modes) */}
            {mode !== "forgot" ? (
              <div className="auth-switcher">
                <button 
                  type="button"
                  className={`switch-btn ${mode === "login" ? "active" : ""}`}
                  onClick={() => switchToMode("login")}
                >
                  Sign In
                </button>
                <button 
                  type="button"
                  className={`switch-btn ${mode === "register" ? "active" : ""}`}
                  onClick={() => switchToMode("register")}
                >
                  Create Account
                </button>
              </div>
            ) : (
              <div className="auth-switcher">
                <button 
                  type="button" 
                  className="switch-btn back-btn"
                  onClick={() => switchToMode("login")}
                >
                  <ArrowLeft size={16} /> Back to Sign In
                </button>
              </div>
            )}

            <div className="auth-card-header">
              <h3>
                {mode === "login" && "Welcome Back"}
                {mode === "register" && "Create Farmer Account"}
                {mode === "forgot" && "Reset Enterprise Password"}
              </h3>
              <p>
                {mode === "login" && "Enter your registered credentials to access your agricultural dashboard."}
                {mode === "register" && "Register your profile to access ICAR-certified agronomic advisories."}
                {mode === "forgot" && (resetStep === 1 ? "Enter your registered email to find your account." : "Create a new secure password for your account.")}
              </p>
            </div>

            {/* Error Notification */}
            {error && (
              <div className="auth-error-banner">
                <div className="banner-content">
                  <AlertCircle size={18} className="banner-icon" />
                  <span>{error}</span>
                </div>
                {suggestRegisterEmail && mode === "login" && (
                  <button 
                    type="button" 
                    className="banner-action-btn"
                    onClick={handleTransferToRegister}
                  >
                    Register as new user →
                  </button>
                )}
              </div>
            )}

            {/* Success Notification */}
            {success && (
              <div className="auth-success-banner">
                <CheckCircle2 size={18} className="banner-icon" />
                <span>{success}</span>
              </div>
            )}

            {/* SIGN IN FORM */}
            {mode === "login" && (
              <form onSubmit={handleSignIn} className="auth-form">
                <div className="field-group">
                  <label>Email Address</label>
                  <div className="input-wrap">
                    <Mail size={18} className="field-icon" />
                    <input 
                      type="email"
                      required
                      placeholder="farmer@agrofarm.in"
                      value={signInEmail}
                      onChange={e => { setSignInEmail(e.target.value); clearMessages(); }}
                      autoComplete="email"
                    />
                  </div>
                </div>

                <div className="field-group">
                  <div className="label-row">
                    <label>Password</label>
                    <a 
                      href="#forgot" 
                      onClick={(e) => { 
                        e.preventDefault(); 
                        setResetEmail(signInEmail);
                        switchToMode("forgot");
                      }}
                    >
                      Forgot password?
                    </a>
                  </div>
                  <div className="input-wrap">
                    <Lock size={18} className="field-icon" />
                    <input 
                      type={showPassword ? "text" : "password"}
                      required
                      placeholder="Enter your password"
                      value={signInPassword}
                      onChange={e => { setSignInPassword(e.target.value); clearMessages(); }}
                      autoComplete="current-password"
                    />
                    <button 
                      type="button" 
                      className="eye-btn" 
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label="Toggle password visibility"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                <button 
                  type="submit" 
                  className="auth-submit-btn"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      <span>Verifying Credentials...</span>
                    </>
                  ) : (
                    <>
                      <span>Sign In to AgriBot</span>
                      <ArrowRight size={18} />
                    </>
                  )}
                </button>
              </form>
            )}

            {/* REGISTER FORM */}
            {mode === "register" && (
              <form onSubmit={handleRegister} className="auth-form register-form">
                <div className="field-group">
                  <label>Full Name *</label>
                  <div className="input-wrap">
                    <UserIcon size={18} className="field-icon" />
                    <input 
                      type="text"
                      required
                      placeholder="e.g. Vikramaditya Reddy"
                      value={name}
                      onChange={e => { setName(e.target.value); clearMessages(); }}
                    />
                  </div>
                </div>

                <div className="field-group">
                  <label>Email Address *</label>
                  <div className="input-wrap">
                    <Mail size={18} className="field-icon" />
                    <input 
                      type="email"
                      required
                      placeholder="vikram@kisan.in"
                      value={email}
                      onChange={e => { setEmail(e.target.value); clearMessages(); }}
                      autoComplete="email"
                    />
                  </div>
                </div>

                <div className="field-grid-2">
                  <div className="field-group">
                    <label>Password (Min 6 chars) *</label>
                    <div className="input-wrap">
                      <Lock size={18} className="field-icon" />
                      <input 
                        type={showPassword ? "text" : "password"}
                        required
                        placeholder="Create password"
                        value={password}
                        onChange={e => { setPassword(e.target.value); clearMessages(); }}
                        autoComplete="new-password"
                      />
                      <button 
                        type="button" 
                        className="eye-btn" 
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <div className="field-group">
                    <label>Confirm Password *</label>
                    <div className="input-wrap">
                      <Lock size={18} className="field-icon" />
                      <input 
                        type={showConfirmPassword ? "text" : "password"}
                        required
                        placeholder="Re-enter password"
                        value={confirmPassword}
                        onChange={e => { setConfirmPassword(e.target.value); clearMessages(); }}
                        autoComplete="new-password"
                      />
                      <button 
                        type="button" 
                        className="eye-btn" 
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      >
                        {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="field-grid-2">
                  <div className="field-group">
                    <label>Professional Role</label>
                    <select 
                      value={role}
                      onChange={e => setRole(e.target.value as any)}
                    >
                      <option value="Farmer">Farmer / Cultivator</option>
                      <option value="Agronomist">Agronomist / Consultant</option>
                      <option value="KVK Extension Officer">KVK Extension Officer</option>
                      <option value="Researcher">Agricultural Researcher</option>
                    </select>
                  </div>

                  <div className="field-group">
                    <label>Farm / District Location</label>
                    <div className="input-wrap">
                      <MapPin size={18} className="field-icon" />
                      <input 
                        type="text"
                        placeholder="e.g. Coimbatore, Tamil Nadu"
                        value={farmLocation}
                        onChange={e => setFarmLocation(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                <div className="field-grid-2">
                  <div className="field-group">
                    <label>Primary Crop Focus</label>
                    <select 
                      value={primaryCrop}
                      onChange={e => setPrimaryCrop(e.target.value)}
                    >
                      <option value="">🌱 All 5 Supported Crops</option>
                      <option value="rice">🌾 Rice</option>
                      <option value="coconut">🥥 Coconut</option>
                      <option value="sugarcane">🎋 Sugarcane</option>
                      <option value="mango">🥭 Mango</option>
                      <option value="tobacco">🍂 Tobacco</option>
                    </select>
                  </div>

                  <div className="field-group">
                    <label>Advisory Language</label>
                    <div className="input-wrap">
                      <Globe size={18} className="field-icon" />
                      <select 
                        value={language}
                        onChange={e => setLanguage(e.target.value)}
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

                <button 
                  type="submit" 
                  className="auth-submit-btn"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 size={18} className="animate-spin" />
                      <span>Creating Account...</span>
                    </>
                  ) : (
                    <>
                      <span>Register & Start Diagnosing</span>
                      <ArrowRight size={18} />
                    </>
                  )}
                </button>
              </form>
            )}

            {/* FORGOT PASSWORD FORM */}
            {mode === "forgot" && (
              <div className="forgot-password-card">
                {resetStep === 1 ? (
                  <form onSubmit={handleCheckResetEmail} className="auth-form">
                    <div className="field-group">
                      <label>Registered Account Email</label>
                      <div className="input-wrap">
                        <Mail size={18} className="field-icon" />
                        <input 
                          type="email"
                          required
                          placeholder="Enter your registered email"
                          value={resetEmail}
                          onChange={e => { setResetEmail(e.target.value); clearMessages(); }}
                        />
                      </div>
                    </div>

                    <button type="submit" className="auth-submit-btn" disabled={loading}>
                      <span>Find Account</span>
                      <ArrowRight size={18} />
                    </button>
                  </form>
                ) : (
                  <form onSubmit={handleCompleteReset} className="auth-form">
                    <div className="field-group">
                      <label>New Password (Min 6 chars)</label>
                      <div className="input-wrap">
                        <KeyRound size={18} className="field-icon" />
                        <input 
                          type={showPassword ? "text" : "password"}
                          required
                          placeholder="Enter new password"
                          value={newPassword}
                          onChange={e => { setNewPassword(e.target.value); clearMessages(); }}
                        />
                        <button 
                          type="button" 
                          className="eye-btn" 
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                      </div>
                    </div>

                    <div className="field-group">
                      <label>Confirm New Password</label>
                      <div className="input-wrap">
                        <Lock size={18} className="field-icon" />
                        <input 
                          type={showConfirmPassword ? "text" : "password"}
                          required
                          placeholder="Re-enter new password"
                          value={confirmNewPassword}
                          onChange={e => { setConfirmNewPassword(e.target.value); clearMessages(); }}
                        />
                        <button 
                          type="button" 
                          className="eye-btn" 
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        >
                          {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                      </div>
                    </div>

                    <button type="submit" className="auth-submit-btn" disabled={loading}>
                      {loading ? (
                        <>
                          <Loader2 size={18} className="animate-spin" />
                          <span>Updating Password...</span>
                        </>
                      ) : (
                        <>
                          <span>Save New Password & Sign In</span>
                          <ArrowRight size={18} />
                        </>
                      )}
                    </button>
                  </form>
                )}
              </div>
            )}

            {/* Quick Demo Access Bar */}
            <div className="auth-divider">
              <span>Or explore with verified demo credentials</span>
            </div>

            <div className="demo-accounts-grid">
              <button 
                type="button" 
                className="demo-card-btn"
                onClick={() => handleDemoLogin("Agronomist")}
                title="Sign in as ICAR Agronomist (ananya.sharma@icar.res.in)"
                disabled={loading}
              >
                <div className="demo-avatar agro">AS</div>
                <div className="demo-info">
                  <div className="demo-name">Dr. Ananya Sharma</div>
                  <div className="demo-meta">Agronomist • IARI New Delhi</div>
                </div>
              </button>

              <button 
                type="button" 
                className="demo-card-btn"
                onClick={() => handleDemoLogin("Farmer")}
                title="Sign in as Certified Farmer (ramesh.patel@kisan.in)"
                disabled={loading}
              >
                <div className="demo-avatar farm">RP</div>
                <div className="demo-info">
                  <div className="demo-name">Ramesh Patel</div>
                  <div className="demo-meta">Farmer • Guntur AP</div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
