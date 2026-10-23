import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { api, refreshSession, setToken } from '../services/api';

export type User = { id: number; name: string; email: string; role: 'graduate' | 'admin' };
const AuthContext = createContext<{ user: User | null; loading: boolean; authenticate: (data: any) => void; logout: () => Promise<void>; updateName: (name: string) => void } | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    refreshSession().then(data => setUser(data.user)).catch(() => setToken(null)).finally(() => setLoading(false));
    const expire = () => setUser(null);
    window.addEventListener('session-expired', expire);
    return () => window.removeEventListener('session-expired', expire);
  }, []);
  function authenticate(data: any) { setToken(data.access_token); setUser(data.user); }
  async function logout() {
    await api('/auth/logout', { method: 'POST' });
    setToken(null); setUser(null);
  }
  function updateName(name: string) { setUser(current => current ? { ...current, name } : current); }
  return <AuthContext.Provider value={{ user, loading, authenticate, logout, updateName }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('AuthProvider is required');
  return context;
}
