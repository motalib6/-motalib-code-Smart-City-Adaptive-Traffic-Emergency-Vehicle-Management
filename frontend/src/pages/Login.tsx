
import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ShieldCheck, TrafficCone } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { api, ApiError } from '../services/api';
import ConnectionIndicator from '../components/ConnectionIndicator';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  // Default must be the seeded admin EMAIL — the backend looks users up by
  // email, so plain "admin" always fails with "Invalid credentials".
  const [username, setUsername] = useState('admin@smartflow.local');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('admin');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [backend, setBackend] = useState(false);
  const [demoMode, setDemoMode] = useState(false);

  const checkBackend = async () => { try { await api.health(); setBackend(true); } catch { setBackend(false); } };
  useState(() => { void checkBackend(); });

  const submit = async (e: FormEvent) => {
    e.preventDefault(); setError(''); setBusy(true);
    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      if (err instanceof ApiError && err.status === 0) {
        setError('Backend unreachable at http://127.0.0.1:8000. Start FastAPI first, or continue in demo preview mode.');
        setDemoMode(true);
      } else setError(err instanceof Error ? err.message : 'Sign-in failed.');
    } finally { setBusy(false); }
  };
  const enterDemo = () => {
    localStorage.setItem('smartflow_user', JSON.stringify({ id: 0, username: 'demo-viewer', role: 'viewer' }));
    navigate('/dashboard');
    window.location.reload();
  };
  return (
    <div className="flex min-h-screen items-center justify-center bg-ink px-4 py-8">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <span className="mx-auto inline-flex rounded-2xl bg-teal p-3 text-ink"><TrafficCone className="h-8 w-8" aria-hidden /></span>
          <h1 className="mt-4 text-2xl font-bold text-white">SMARTFLOW ODISHA</h1>
          <p className="mt-1 text-sm text-slate2">Smart City — Adaptive Traffic &amp; Emergency Vehicle Management</p>
          <p className="mt-1 text-xs text-slate2">GEC Hackathon 2026 · Problem Statement 03</p>
        </div>
        <form onSubmit={submit} className="rounded-2xl border border-line bg-panel p-6 shadow-xl" aria-label="Sign in">
          <div className="mb-4 flex justify-center"><ConnectionIndicator ws="disconnected" backend={backend} /></div>
          <label className="mb-1 block text-sm font-medium text-white" htmlFor="username">Username</label>
          <input id="username" value={username} onChange={(e) => setUsername(e.target.value)} required autoComplete="username"
            className="mb-4 min-h-[44px] w-full rounded-lg border border-line bg-panel2 px-3 text-white placeholder:text-slate2" placeholder="admin@smartflow.local" />
          <label className="mb-1 block text-sm font-medium text-white" htmlFor="password">Password</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password"
            className="mb-4 min-h-[44px] w-full rounded-lg border border-line bg-panel2 px-3 text-white placeholder:text-slate2" placeholder="••••••••" />
          <label className="mb-1 block text-sm font-medium text-white" htmlFor="role">Role</label>
          <select id="role" value={role} onChange={(e) => setRole(e.target.value)}
            className="mb-5 min-h-[44px] w-full rounded-lg border border-line bg-panel2 px-3 text-white">
            <option value="admin">Admin — full control</option>
            <option value="operator">Operator — run simulation &amp; emergencies</option>
            <option value="viewer">Viewer — read-only</option>
          </select>
          {error && <p className="mb-4 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">{error}</p>}
          <button type="submit" disabled={busy} className="flex min-h-[48px] w-full items-center justify-center gap-2 rounded-lg bg-teal px-4 font-semibold text-ink hover:bg-teal-dark disabled:opacity-60">
            {busy ? <Loader2 className="h-5 w-5 animate-spin" aria-hidden /> : <ShieldCheck className="h-5 w-5" aria-hidden />}
            {busy ? 'Signing in…' : 'Sign in securely'}
          </button>
          {demoMode && (
            <button type="button" onClick={enterDemo} className="mt-3 min-h-[48px] w-full rounded-lg border border-line px-4 font-semibold text-slate2 hover:text-white">
              Continue in demo preview (DEMO DATA)
            </button>
          )}
          <p className="mt-4 text-center text-xs text-slate2">Passwords are Argon2-hashed server-side. Demo accounts are seeded by the backend; ask an admin for credentials.</p>
        </form>
      </div>
    </div>
  );
}
