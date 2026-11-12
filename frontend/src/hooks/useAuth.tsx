
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { api } from '../services/api';
import type { Role, User } from '../types';

interface AuthCtx { user: User | null; login: (u: string, p: string) => Promise<void>; logout: () => void; loading: boolean; }
const Ctx = createContext<AuthCtx>({ user: null, login: async () => undefined, logout: () => undefined, loading: true });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const raw = localStorage.getItem('smartflow_user');
    if (raw) { try { setUser(JSON.parse(raw) as User); } catch { localStorage.removeItem('smartflow_user'); } }
    setLoading(false);
  }, []);
  const login = async (username: string, password: string) => {
    const res = await api.login(username, password);
    localStorage.setItem('smartflow_token', res.access_token);
    localStorage.setItem('smartflow_user', JSON.stringify(res.user));
    setUser(res.user);
  };
  const logout = () => { localStorage.removeItem('smartflow_token'); localStorage.removeItem('smartflow_user'); setUser(null); };
  const value = useMemo(() => ({ user, login, logout, loading }), [user, loading]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
export function useAuth() { return useContext(Ctx); }
export function hasRole(user: User | null, roles: Role[]) { return !!user && roles.includes(user.role); }
