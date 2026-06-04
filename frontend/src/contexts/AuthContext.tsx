import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { LoginRequest, SignupRequest, UserResponse } from '../types';
import { login as apiLogin, signup as apiSignup, getMe, logout as apiLogout } from '../api/client';

interface AuthContextValue {
  user: UserResponse | null;
  loading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  signup: (data: SignupRequest) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  setUser: (user: UserResponse | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then((res) => setUser(res))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (data: LoginRequest) => {
    const res = await apiLogin(data);
    setUser({ user_id: res.user_id, email: res.email, full_name: res.full_name, created_at: '' });
  }, []);

  const signup = useCallback(async (data: SignupRequest) => {
    const res = await apiSignup(data);
    setUser({ user_id: res.user_id, email: res.email, full_name: res.full_name, created_at: '' });
  }, []);

  const logout = useCallback(async () => {
    try { await apiLogout(); } catch { /* ignore */ }
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, isAuthenticated: !!user, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
