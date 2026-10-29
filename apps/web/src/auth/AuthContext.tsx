import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { api, type User } from "../lib/api";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    fullName: string,
  ) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const ACCESS_KEY = "reminder_access_token";
const REFRESH_KEY = "reminder_refresh_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function restoreSession() {
      const accessToken = localStorage.getItem(ACCESS_KEY);
      const refreshToken = localStorage.getItem(REFRESH_KEY);

      if (!accessToken) {
        if (active) setLoading(false);
        return;
      }

      try {
        const currentUser = await api.me(accessToken);

        if (active) setUser(currentUser);
      } catch {
        if (refreshToken) {
          try {
            const tokens = await api.refresh(refreshToken);

            localStorage.setItem(ACCESS_KEY, tokens.access_token);
            localStorage.setItem(REFRESH_KEY, tokens.refresh_token);

            const currentUser = await api.me(tokens.access_token);

            if (active) setUser(currentUser);
          } catch {
            localStorage.removeItem(ACCESS_KEY);
            localStorage.removeItem(REFRESH_KEY);
          }
        } else {
          localStorage.removeItem(ACCESS_KEY);
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void restoreSession();

    return () => {
      active = false;
    };
  }, []);

  async function login(email: string, password: string) {
    const tokens = await api.login({ email, password });

    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);

    try {
      const currentUser = await api.me(tokens.access_token);
      setUser(currentUser);
    } catch (error) {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
      throw error;
    }
  }

  async function register(
    email: string,
    password: string,
    fullName: string,
  ) {
    await api.register({
      email,
      password,
      full_name: fullName.trim() || undefined,
    });
  }

  async function logout() {
    const refreshToken = localStorage.getItem(REFRESH_KEY);

    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    setUser(null);

    if (refreshToken) {
      try {
        await api.logout(refreshToken);
      } catch {
        // Local logout still succeeds if the server is unavailable.
      }
    }
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
