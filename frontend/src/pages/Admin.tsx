
import { useEffect, useState, type FormEvent } from 'react';
import { ShieldAlert } from 'lucide-react';
import { api, ApiError } from '../services/api';
import { useAuth, hasRole } from '../hooks/useAuth';
import type { AdminSettings, User } from '../types';
import { ErrorBanner, card } from './_shared';

const DEFAULTS: AdminSettings = { minGreenSec: 15, maxGreenSec: 60, yellowSec: 4, allRedSec: 2, demandWQueue: 0.5, demandWCount: 0.3, demandWWait: 0.2 };

export default function Admin() {
  const { user } = useAuth();
  const isAdmin = hasRole(user, ['admin']);
  const [settings, setSettings] = useState<AdminSettings>(DEFAULTS);
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!isAdmin) return;
    (async () => {
      try {
        const [s, u] = await Promise.all([api.adminSettings(), api.users().catch(() => [] as User[])]);
        setSettings(s); setUsers(u); setLoaded(true);
      } catch (err) { setError(err instanceof Error ? err.message : 'Could not load admin settings.'); }
    })();
  }, [isAdmin]);

  const save = async (e: FormEvent) => {
    e.preventDefault(); setError(''); setNotice('');
    if (settings.minGreenSec >= settings.maxGreenSec) { setError('Minimum green must be less than maximum green.'); return; }
    if (settings.yellowSec < 3 || settings.allRedSec < 1) { setError('Yellow must be at least 3s and all-red at least 1s — safety minimums.'); return; }
    try { await api.saveAdminSettings(settings); setNotice('Signal safety configuration saved.'); }
    catch (err) { setError(err instanceof ApiError ? err.message : 'Save failed — backend unreachable. Settings were not saved.'); }
  };
  const num = (k: keyof AdminSettings) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setSettings((s) => ({ ...s, [k]: Number(e.target.value) }));

  if (!isAdmin) {
    return (
      <div className="space-y-5">
        <div className="flex items-start gap-3 rounded-xl border border-red-500/40 bg-red-500/10 p-5" role="alert">
          <ShieldAlert className="h-6 w-6 shrink-0 text-danger" aria-hidden />
          <div>
            <h2 className="font-bold text-white">Permission denied</h2>
            <p className="mt-1 text-sm text-red-200">Administration is admin-only. You are signed in as <strong>{user?.username ?? 'guest'}</strong> ({user?.role ?? 'no role'}). Viewers and operators have read-only or operational access; only admins can change signal safety configuration or manage users.</p>
            <p className="mt-2 text-sm text-slate2">If you need access, ask an administrator to grant the admin role.</p>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-5">
      {error && <ErrorBanner msg={error} />}
      {notice && <p className="rounded-lg bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300" role="status">{notice}</p>}
      {!loaded && <p className="text-sm text-slate2">Loading settings from backend…</p>}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <form onSubmit={save} className={card} aria-label="Signal safety configuration">
          <h2 className="text-lg font-bold text-white">Signal safety configuration</h2>
          <p className="mt-1 text-sm text-slate2">Validated server-side. Yellow and all-red clearance phases can never be set to zero.</p>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {([
              ['minGreenSec', 'Min green (s)'], ['maxGreenSec', 'Max green (s)'],
              ['yellowSec', 'Yellow (s)'], ['allRedSec', 'All-red (s)'],
            ] as [keyof AdminSettings, string][]).map(([k, label]) => (
              <div key={k}>
                <label className="mb-1 block text-sm font-medium text-white" htmlFor={k}>{label}</label>
                <input id={k} type="number" min={k === 'yellowSec' ? 3 : 1} max={120} value={settings[k]} onChange={num(k)}
                  className="min-h-[44px] w-full rounded-lg border border-line bg-panel2 px-3 text-white" />
              </div>
            ))}
          </div>
          <h3 className="mt-5 font-semibold text-white">Demand weights (queue / count / wait)</h3>
          <div className="mt-2 grid grid-cols-3 gap-3">
            {(['demandWQueue', 'demandWCount', 'demandWWait'] as const).map((k) => (
              <div key={k}>
                <label className="mb-1 block text-xs font-medium text-slate2" htmlFor={k}>{k.replace('demandW', '')}</label>
                <input id={k} type="number" step="0.05" min={0} max={1} value={settings[k]} onChange={num(k)} className="min-h-[44px] w-full rounded-lg border border-line bg-panel2 px-3 text-white" />
              </div>
            ))}
          </div>
          <button type="submit" className="mt-5 min-h-[48px] rounded-lg bg-teal px-5 font-semibold text-ink hover:bg-teal-dark">Save configuration</button>
        </form>
        <div className="space-y-4">
          <div className={card}>
            <h2 className="text-lg font-bold text-white">Users &amp; roles</h2>
            {users.length === 0
              ? <p className="mt-2 text-sm text-slate2">No users loaded from the backend yet. User management (create / change role / deactivate) is served by the backend admin API.</p>
              : <ul className="mt-3 space-y-2">{users.map((u) => (
                <li key={u.id} className="flex items-center justify-between rounded-lg bg-panel2 px-3 py-2.5 text-sm">
                  <span className="font-medium text-white">{u.username}</span><span className="rounded-full bg-teal/15 px-2.5 py-1 text-xs font-medium capitalize text-teal">{u.role}</span>
                </li>))}</ul>}
            <p className="mt-3 text-xs text-slate2">Roles: admin (users, signal config, settings), operator (simulation, scenarios, video, emergencies), viewer (read-only).</p>
          </div>
          <div className={card}>
            <h2 className="text-lg font-bold text-white">Junction &amp; simulation configuration</h2>
            <ul className="mt-2 space-y-1.5 text-sm text-slate2">
              <li>Network: 2×2 connected junctions (J1–J4), N/S/E/W approaches.</li>
              <li>Vehicle types: car, motorcycle, bus, truck, emergency ambulance.</li>
              <li>Scenarios: normal, medium, rush hour, heavy, unbalanced, emergency.</li>
              <li>Input modes: SUMO sensor data (Mode A) or YOLO camera data (Mode B).</li>
            </ul>
            <p className="mt-3 text-xs text-slate2">Junction topology is defined by the SUMO network in the backend; editing it requires a network rebuild, not a dashboard toggle.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
