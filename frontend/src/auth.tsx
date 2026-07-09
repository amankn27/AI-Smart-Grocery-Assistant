import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, setAuthToken, getAuthToken } from "./api";

interface AuthState {
  email: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [email, setEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // On boot, if a token is stored, resolve the current user.
  useEffect(() => {
    if (!getAuthToken()) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then((u) => setEmail(u.email))
      .catch(() => setAuthToken(null))
      .finally(() => setLoading(false));
  }, []);

  async function login(e: string, p: string) {
    const t = await api.login(e, p);
    setAuthToken(t.access_token);
    const u = await api.me();
    setEmail(u.email);
  }

  async function register(e: string, p: string) {
    const t = await api.register(e, p);
    setAuthToken(t.access_token);
    setEmail(e);
  }

  function logout() {
    setAuthToken(null);
    setEmail(null);
  }

  return (
    <AuthContext.Provider value={{ email, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
