import { User } from "./types";

export interface RegisteredAccount extends User {
  passwordHash: string;
  salt: string;
  createdAt: number;
  lastLoginAt: number;
}

export interface AuthResult {
  success: boolean;
  user?: User;
  error?: string;
  code?: "USER_NOT_FOUND" | "INVALID_PASSWORD" | "ALREADY_EXISTS" | "VALIDATION_ERROR";
}

const ACCOUNTS_KEY = "agribot_registered_accounts_v2";

// Fallback simple SHA-256 for non-crypto contexts
async function computeSha256(text: string): Promise<string> {
  if (typeof window !== "undefined" && window.crypto && window.crypto.subtle) {
    try {
      const encoder = new TextEncoder();
      const data = encoder.encode(text);
      const hashBuffer = await window.crypto.subtle.digest("SHA-256", data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
    } catch {
      // Fallback below
    }
  }
  // Lightweight hash fallback for edge environments
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return `fallback_${Math.abs(hash).toString(16)}_${text.length}`;
}

export async function hashPassword(password: string, salt: string): Promise<string> {
  return computeSha256(`${password}:${salt}:agribot_secure_salt_2026`);
}

// Generate random salt
function generateSalt(): string {
  if (typeof window !== "undefined" && window.crypto && window.crypto.getRandomValues) {
    const array = new Uint8Array(16);
    window.crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, "0")).join("");
  }
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

// Seed production demo accounts (Dr. Ananya Sharma & Ramesh Patel)
const DEMO_ACCOUNTS_SEED: {
  account: Omit<RegisteredAccount, "passwordHash" | "salt" | "createdAt" | "lastLoginAt">;
  defaultPass: string;
}[] = [
  {
    account: {
      id: "demo_agronomist",
      name: "Dr. Ananya Sharma",
      email: "ananya.sharma@icar.res.in",
      role: "Agronomist",
      farmLocation: "IARI, New Delhi",
      primaryCrop: "rice",
      language: "English"
    },
    defaultPass: "agri123"
  },
  {
    account: {
      id: "demo_farmer",
      name: "Ramesh Patel",
      email: "ramesh.patel@kisan.in",
      role: "Farmer",
      farmLocation: "Guntur, Andhra Pradesh",
      primaryCrop: "rice",
      language: "English"
    },
    defaultPass: "kisan123"
  }
];

// Initialize accounts in localStorage with seed demo accounts if empty
export async function initializeAccounts(): Promise<RegisteredAccount[]> {
  try {
    const raw = localStorage.getItem(ACCOUNTS_KEY);
    let accounts: RegisteredAccount[] = [];
    if (raw) {
      accounts = JSON.parse(raw);
    }

    let modified = false;

    // Check if demo accounts are seeded
    for (const seed of DEMO_ACCOUNTS_SEED) {
      const exists = accounts.some(a => a.email.toLowerCase() === seed.account.email.toLowerCase());
      if (!exists) {
        const salt = generateSalt();
        const passwordHash = await hashPassword(seed.defaultPass, salt);
        accounts.push({
          ...seed.account,
          passwordHash,
          salt,
          createdAt: Date.now(),
          lastLoginAt: Date.now()
        });
        modified = true;
      }
    }

    if (modified || !raw) {
      localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
    }

    return accounts;
  } catch (err) {
    console.error("Error initializing accounts:", err);
    return [];
  }
}

// Get all registered accounts
export function getRegisteredAccounts(): RegisteredAccount[] {
  try {
    const raw = localStorage.getItem(ACCOUNTS_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as RegisteredAccount[];
  } catch {
    return [];
  }
}

// Save accounts array
function saveAccounts(accounts: RegisteredAccount[]): void {
  try {
    localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
  } catch (err) {
    console.error("Failed to save registered accounts:", err);
  }
}

// Find account by email (case-insensitive)
export function findAccountByEmail(email: string): RegisteredAccount | undefined {
  const norm = email.trim().toLowerCase();
  return getRegisteredAccounts().find(a => a.email.toLowerCase() === norm);
}

// Register new user account
export async function registerAccount(params: {
  name: string;
  email: string;
  password: string;
  role: User["role"];
  farmLocation: string;
  primaryCrop: string;
  language: string;
}): Promise<AuthResult> {
  const trimmedName = params.name.trim();
  const trimmedEmail = params.email.trim().toLowerCase();

  // 1. Validation
  if (!trimmedName || trimmedName.length < 2) {
    return {
      success: false,
      error: "Please enter your full name (minimum 2 characters).",
      code: "VALIDATION_ERROR"
    };
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!trimmedEmail || !emailRegex.test(trimmedEmail)) {
    return {
      success: false,
      error: "Please enter a valid email address.",
      code: "VALIDATION_ERROR"
    };
  }

  if (!params.password || params.password.length < 6) {
    return {
      success: false,
      error: "Password must be at least 6 characters long.",
      code: "VALIDATION_ERROR"
    };
  }

  // 2. Ensure accounts list is loaded
  await initializeAccounts();
  const accounts = getRegisteredAccounts();

  // 3. Check duplicate
  const existing = accounts.find(a => a.email.toLowerCase() === trimmedEmail);
  if (existing) {
    return {
      success: false,
      error: `An account with ${trimmedEmail} is already registered. Please sign in instead.`,
      code: "ALREADY_EXISTS"
    };
  }

  // 4. Create new registered account
  const salt = generateSalt();
  const passwordHash = await hashPassword(params.password, salt);
  const now = Date.now();

  const newAccount: RegisteredAccount = {
    id: `usr_${now}_${Math.random().toString(36).substring(2, 7)}`,
    name: trimmedName,
    email: trimmedEmail,
    role: params.role || "Farmer",
    farmLocation: params.farmLocation.trim() || "India",
    primaryCrop: params.primaryCrop || "rice",
    language: params.language || "English",
    passwordHash,
    salt,
    createdAt: now,
    lastLoginAt: now
  };

  accounts.push(newAccount);
  saveAccounts(accounts);

  const cleanUser: User = {
    id: newAccount.id,
    name: newAccount.name,
    email: newAccount.email,
    role: newAccount.role,
    farmLocation: newAccount.farmLocation,
    primaryCrop: newAccount.primaryCrop,
    language: newAccount.language
  };

  return {
    success: true,
    user: cleanUser
  };
}

// Authenticate user credentials
export async function authenticateUser(
  email: string,
  password: string
): Promise<AuthResult> {
  const trimmedEmail = email.trim().toLowerCase();
  const trimmedPass = password.trim();

  if (!trimmedEmail) {
    return {
      success: false,
      error: "Please enter your registered email address.",
      code: "VALIDATION_ERROR"
    };
  }

  if (!trimmedPass) {
    return {
      success: false,
      error: "Please enter your password.",
      code: "VALIDATION_ERROR"
    };
  }

  await initializeAccounts();
  const accounts = getRegisteredAccounts();
  const account = accounts.find(a => a.email.toLowerCase() === trimmedEmail);

  // STRICT CHECK: User MUST be registered
  if (!account) {
    return {
      success: false,
      error: `No account found for "${trimmedEmail}". Please register an account first.`,
      code: "USER_NOT_FOUND"
    };
  }

  // Verify password hash
  const computedHash = await hashPassword(trimmedPass, account.salt);
  if (computedHash !== account.passwordHash) {
    return {
      success: false,
      error: "Incorrect password. Please verify your credentials or reset your password.",
      code: "INVALID_PASSWORD"
    };
  }

  // Update last login
  account.lastLoginAt = Date.now();
  saveAccounts(accounts);

  const cleanUser: User = {
    id: account.id,
    name: account.name,
    email: account.email,
    role: account.role,
    farmLocation: account.farmLocation,
    primaryCrop: account.primaryCrop,
    language: account.language
  };

  return {
    success: true,
    user: cleanUser
  };
}

// Authenticate demo account directly
export async function authenticateDemoUser(demoId: "demo_agronomist" | "demo_farmer"): Promise<AuthResult> {
  await initializeAccounts();
  const accounts = getRegisteredAccounts();
  const account = accounts.find(a => a.id === demoId);

  if (!account) {
    return {
      success: false,
      error: "Demo account not found in system.",
      code: "USER_NOT_FOUND"
    };
  }

  account.lastLoginAt = Date.now();
  saveAccounts(accounts);

  const cleanUser: User = {
    id: account.id,
    name: account.name,
    email: account.email,
    role: account.role,
    farmLocation: account.farmLocation,
    primaryCrop: account.primaryCrop,
    language: account.language
  };

  return {
    success: true,
    user: cleanUser
  };
}

// Update profile details of a registered account
export function updateRegisteredProfile(updatedUser: User): boolean {
  try {
    const accounts = getRegisteredAccounts();
    const index = accounts.findIndex(
      a => a.id === updatedUser.id || a.email.toLowerCase() === updatedUser.email.toLowerCase()
    );

    if (index === -1) return false;

    accounts[index] = {
      ...accounts[index],
      name: updatedUser.name,
      role: updatedUser.role,
      farmLocation: updatedUser.farmLocation,
      primaryCrop: updatedUser.primaryCrop,
      language: updatedUser.language
    };

    saveAccounts(accounts);
    return true;
  } catch (err) {
    console.error("Failed to update registered profile:", err);
    return false;
  }
}

// Reset password for an account (by email)
export async function resetAccountPassword(email: string, newPassword: string): Promise<AuthResult> {
  const normEmail = email.trim().toLowerCase();
  if (!normEmail) {
    return {
      success: false,
      error: "Please enter your registered email address.",
      code: "VALIDATION_ERROR"
    };
  }

  if (!newPassword || newPassword.length < 6) {
    return {
      success: false,
      error: "New password must be at least 6 characters long.",
      code: "VALIDATION_ERROR"
    };
  }

  await initializeAccounts();
  const accounts = getRegisteredAccounts();
  const account = accounts.find(a => a.email.toLowerCase() === normEmail);

  if (!account) {
    return {
      success: false,
      error: `No registered account found with email "${normEmail}". Please register first.`,
      code: "USER_NOT_FOUND"
    };
  }

  const salt = generateSalt();
  const passwordHash = await hashPassword(newPassword, salt);
  account.passwordHash = passwordHash;
  account.salt = salt;

  saveAccounts(accounts);

  return {
    success: true
  };
}

// Change password (verifying current password)
export async function changeAccountPassword(
  email: string,
  currentPassword: string,
  newPassword: string
): Promise<AuthResult> {
  const normEmail = email.trim().toLowerCase();
  const accounts = getRegisteredAccounts();
  const account = accounts.find(a => a.email.toLowerCase() === normEmail);

  if (!account) {
    return {
      success: false,
      error: "Account not found.",
      code: "USER_NOT_FOUND"
    };
  }

  const currentComputed = await hashPassword(currentPassword, account.salt);
  if (currentComputed !== account.passwordHash) {
    return {
      success: false,
      error: "Current password does not match.",
      code: "INVALID_PASSWORD"
    };
  }

  if (!newPassword || newPassword.length < 6) {
    return {
      success: false,
      error: "New password must be at least 6 characters long.",
      code: "VALIDATION_ERROR"
    };
  }

  const salt = generateSalt();
  account.passwordHash = await hashPassword(newPassword, salt);
  account.salt = salt;
  saveAccounts(accounts);

  return {
    success: true
  };
}
