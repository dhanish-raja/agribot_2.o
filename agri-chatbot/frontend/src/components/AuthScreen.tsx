import { useState, type FormEvent } from "react";
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
  Volume2
} from "lucide-react";
import { User } from "../types";

interface AuthScreenProps {
  onLogin: (user: User) => void;
}

export const AuthScreen = ({ onLogin }: AuthScreenProps) => {
  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sign In Form State
  const [signInEmail, setSignInEmail] = useState("");
  const [signInPassword, setSignInPassword] = useState("");

  // Register Form State
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<User["role"]>("Farmer");
  const [farmLocation, setFarmLocation] = useState("");
  const [primaryCrop, setPrimaryCrop] = useState("");
  const [language, setLanguage] = useState("English");

  const handleSignIn = (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!signInEmail.trim() || !signInPassword.trim()) {
      setError("Please provide both email and password.");
      return;
    }

    // Authenticate user
    const user: User = {
      id: `usr_${Date.now()}`,
      name: signInEmail.split("@")[0].replace(/[._]/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
      email: signInEmail.trim(),
      role: "Farmer",
      farmLocation: "Andhra Pradesh, India",
      primaryCrop: "rice",
      language: "English"
    };

    onLogin(user);
  };

  const handleRegister = (e: FormEvent) => {
    e.preventDefault();
    setError(null);

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

    const newUser: User = {
      id: `usr_${Date.now()}`,
      name: name.trim(),
      email: email.trim(),
      role: role,
      farmLocation: farmLocation.trim() || "India",
      primaryCrop: primaryCrop,
      language: language
    };

    onLogin(newUser);
  };

  const handleDemoLogin = (demoRole: "Agronomist" | "Farmer") => {
    if (demoRole === "Agronomist") {
      onLogin({
        id: "demo_agronomist",
        name: "Dr. Ananya Sharma",
        email: "ananya.sharma@icar.res.in",
        role: "Agronomist",
        farmLocation: "IARI, New Delhi",
        primaryCrop: "rice",
        language: "English"
      });
    } else {
      onLogin({
        id: "demo_farmer",
        name: "Ramesh Patel",
        email: "ramesh.patel@kisan.in",
        role: "Farmer",
        farmLocation: "Guntur, Andhra Pradesh",
        primaryCrop: "rice",
        language: "English"
      });
    }
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
            {/* Tab Switcher */}
            <div className="auth-switcher">
              <button 
                type="button"
                className={`switch-btn ${!isRegister ? "active" : ""}`}
                onClick={() => { setIsRegister(false); setError(null); }}
              >
                Sign In
              </button>
              <button 
                type="button"
                className={`switch-btn ${isRegister ? "active" : ""}`}
                onClick={() => { setIsRegister(true); setError(null); }}
              >
                Create Account
              </button>
            </div>

            <div className="auth-card-header">
              <h3>{isRegister ? "Create Farmer Account" : "Welcome Back"}</h3>
              <p>
                {isRegister 
                  ? "Enter your details to access certified agronomic advisories." 
                  : "Sign in with your enterprise credentials to access your dashboard."}
              </p>
            </div>

            {error && (
              <div className="auth-error-banner">
                <span>{error}</span>
              </div>
            )}

            {/* Sign In Form */}
            {!isRegister ? (
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
                      onChange={e => setSignInEmail(e.target.value)}
                    />
                  </div>
                </div>

                <div className="field-group">
                  <div className="label-row">
                    <label>Password</label>
                    <a href="#forgot" onClick={(e) => { e.preventDefault(); alert("Please contact your organization administrator or use demo access."); }}>
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
                      onChange={e => setSignInPassword(e.target.value)}
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

                <button type="submit" className="auth-submit-btn">
                  <span>Sign In to AgriBot</span>
                  <ArrowRight size={18} />
                </button>
              </form>
            ) : (
              /* Register Form */
              <form onSubmit={handleRegister} className="auth-form register-form">
                <div className="field-group">
                  <label>Full Name</label>
                  <div className="input-wrap">
                    <UserIcon size={18} className="field-icon" />
                    <input 
                      type="text"
                      required
                      placeholder="e.g. Vikramaditya Reddy"
                      value={name}
                      onChange={e => setName(e.target.value)}
                    />
                  </div>
                </div>

                <div className="field-grid-2">
                  <div className="field-group">
                    <label>Email Address</label>
                    <div className="input-wrap">
                      <Mail size={18} className="field-icon" />
                      <input 
                        type="email"
                        required
                        placeholder="vikram@kisan.in"
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="field-group">
                    <label>Password</label>
                    <div className="input-wrap">
                      <Lock size={18} className="field-icon" />
                      <input 
                        type={showPassword ? "text" : "password"}
                        required
                        placeholder="Min 6 characters"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                      />
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

                <button type="submit" className="auth-submit-btn">
                  <span>Create Account & Start Diagnosing</span>
                  <ArrowRight size={18} />
                </button>
              </form>
            )}

            {/* Quick Demo Access Bar */}
            <div className="auth-divider">
              <span>Or explore with instant demo profile</span>
            </div>

            <div className="demo-accounts-grid">
              <button 
                type="button" 
                className="demo-card-btn"
                onClick={() => handleDemoLogin("Agronomist")}
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
