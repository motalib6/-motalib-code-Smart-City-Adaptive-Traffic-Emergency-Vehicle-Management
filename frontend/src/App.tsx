
import { useCallback, useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { liveSocket, type WsStatus } from './services/websocket';
import { api } from './services/api';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import LiveNetwork from './pages/LiveNetwork';
import CameraPage from './pages/Camera';
import Junctions from './pages/Junctions';
import EmergencyPage from './pages/Emergency';
import Analytics from './pages/Analytics';
import Events from './pages/Events';
import Admin from './pages/Admin';
import type { ReactNode } from 'react';

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex min-h-screen items-center justify-center bg-ink text-slate2">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function Shell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [ws, setWs] = useState<WsStatus>(liveSocket.status);
  const [backend, setBackend] = useState(false);
  const [sumo, setSumo] = useState(false);
  const location = useLocation();

  const refresh = useCallback(async () => {
    try { const h = await api.health(); setBackend(true); setSumo(!!h.sumo_available); }
    catch { setBackend(false); setSumo(false); }
  }, []);
  useEffect(() => { void refresh(); const off = liveSocket.onStatus(setWs); liveSocket.connect(); return () => { off(); liveSocket.disconnect(); }; }, [refresh]);
  useEffect(() => { void refresh(); }, [location.pathname, refresh]);

  return (
    <div className="flex min-h-screen bg-ink">
      <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenu={() => setMenuOpen(true)} ws={ws} backend={backend} sumo={sumo} onRefresh={() => void refresh()} />
        {ws === 'disconnected' && (
          <div className="border-b border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm text-amber-200 sm:px-6" role="status">
            Live feed disconnected — reconnecting automatically. Data may be stale; DEMO DATA is labelled where shown.
          </div>
        )}
        <main className="mx-auto w-full max-w-[1440px] flex-1 px-4 py-5 sm:px-6">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/live-network" element={<LiveNetwork />} />
            <Route path="/camera" element={<CameraPage />} />
            <Route path="/junctions" element={<Junctions />} />
            <Route path="/emergency" element={<EmergencyPage />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/events" element={<Events />} />
            <Route path="/admin" element={<Admin />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
        <footer className="border-t border-line px-4 py-3 text-center text-xs text-slate2 sm:px-6">
          SMARTFLOW ODISHA · GEC Hackathon 2026 · PS-03 · Simulated traffic — this prototype never controls real-world signals.
        </footer>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<RequireAuth><Shell /></RequireAuth>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
