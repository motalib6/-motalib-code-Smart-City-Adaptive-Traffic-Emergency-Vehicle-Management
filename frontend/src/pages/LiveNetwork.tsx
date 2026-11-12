
import { useCallback, useEffect, useState } from 'react';
import { Pause, Play, RotateCcw } from 'lucide-react';
import { api, ApiError } from '../services/api';
import { demoJunctions, demoVehicles } from '../data/demo';
import type { Junction, Scenario, VehiclePos } from '../types';
import TrafficNetworkMap from '../components/TrafficNetworkMap';
import VehicleCounter from '../components/VehicleCounter';
import { DemoBanner, ErrorBanner } from './_shared';

const SCENARIOS: { id: Scenario; label: string }[] = [
  { id: 'normal', label: 'Normal' }, { id: 'medium', label: 'Medium' },
  { id: 'rush', label: 'Rush hour' }, { id: 'heavy', label: 'Heavy' },
  { id: 'unbalanced', label: 'Unbalanced' }, { id: 'emergency', label: 'Emergency' },
];

export default function LiveNetwork() {
  const [junctions, setJunctions] = useState<Junction[]>(demoJunctions);
  const [vehicles] = useState<VehiclePos[]>(demoVehicles);
  const [demo, setDemo] = useState(true);
  const [error, setError] = useState('');
  const [scenario, setScenario] = useState<Scenario>('normal');
  const [running, setRunning] = useState(false);
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    try {
      const j = await api.junctions();
      setJunctions(j); setDemo(false); setError('');
      const t = await api.trafficCurrent().catch(() => null);
      if (t?.junctions) setJunctions(t.junctions);
    } catch (err) { setDemo(true); setError(err instanceof Error ? err.message : 'Backend unavailable.'); }
  }, []);
  useEffect(() => { void load(); const i = setInterval(() => void load(), 5000); return () => clearInterval(i); }, [load]);

  const act = async (fn: () => Promise<unknown>, okMsg: string, run?: boolean) => {
    setNotice('');
    try { await fn(); setNotice(okMsg); if (run !== undefined) setRunning(run); await load(); }
    catch (err) { setNotice(err instanceof ApiError ? err.message : 'Action failed — backend may be disconnected.'); }
  };
  const counts: Record<string, number> = {};
  vehicles.forEach((v) => { counts[v.type] = (counts[v.type] ?? 0) + 1; });
  const totalQueue = junctions.reduce((a, j) => a + j.approaches.reduce((x, ap) => x + ap.queue, 0), 0);

  return (
    <div className="space-y-5">
      {demo && <DemoBanner />}
      {error && <ErrorBanner msg={error} onRetry={() => void load()} />}
      <div className="flex flex-wrap items-center gap-2">
        <button onClick={() => void act(() => api.simStart(), 'Simulation started.', true)} className="inline-flex min-h-[44px] items-center gap-2 rounded-lg bg-teal px-4 text-sm font-semibold text-ink hover:bg-teal-dark"><Play className="h-4 w-4" /> Start</button>
        <button onClick={() => void act(() => api.simPause(), 'Simulation paused.', false)} className="inline-flex min-h-[44px] items-center gap-2 rounded-lg border border-line bg-panel px-4 text-sm font-semibold text-white"><Pause className="h-4 w-4" /> Pause</button>
        <button onClick={() => void act(() => api.simReset(), 'Simulation reset.', false)} className="inline-flex min-h-[44px] items-center gap-2 rounded-lg border border-line bg-panel px-4 text-sm font-semibold text-white"><RotateCcw className="h-4 w-4" /> Reset</button>
        <span className="ml-1 text-sm text-slate2">Status: <strong className="text-white">{running ? 'Running' : 'Paused / stopped'}</strong> · Total queue: <strong className="text-white">{totalQueue} vehicles</strong></span>
      </div>
      {notice && <p className="text-sm text-slate2" role="status">{notice}</p>}
      <div>
        <p className="mb-2 text-sm font-medium text-white">Traffic scenario</p>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Traffic scenario">
          {SCENARIOS.map((s) => (
            <button key={s.id} onClick={() => { setScenario(s.id); void act(() => api.simScenario(s.id), `Scenario switched to ${s.label}.`); }}
              aria-pressed={scenario === s.id}
              className={`min-h-[44px] rounded-lg px-4 text-sm font-medium ${scenario === s.id ? 'bg-teal text-ink' : 'border border-line bg-panel text-slate2 hover:text-white'}`}>{s.label}</button>
          ))}
        </div>
      </div>
      <TrafficNetworkMap junctions={junctions} vehicles={vehicles} demo={demo} />
      <VehicleCounter counts={counts} />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {junctions.map((j) => (
          <div key={j.id} className="rounded-xl border border-line bg-panel p-4">
            <h3 className="font-semibold text-white">{j.id} — per-lane counts</h3>
            <ul className="mt-3 space-y-1.5 text-sm">
              {j.approaches.map((a) => (
                <li key={a.approach} className="flex justify-between rounded bg-panel2 px-3 py-2">
                  <span className="text-slate2">{a.approach} approach</span>
                  <span className="font-medium text-white">{a.vehicles} veh · queue {a.queue} · wait {a.avgWaitSec}s</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate2">Vehicle positions come from SUMO via TraCI through the backend WebSocket when connected; otherwise the map shows labelled DEMO DATA positions.</p>
    </div>
  );
}
