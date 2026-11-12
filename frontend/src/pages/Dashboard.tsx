
import { useCallback, useEffect, useState } from 'react';
import { Ambulance, Car, Clock, Gauge, MapPin, Siren } from 'lucide-react';
import { api } from '../services/api';
import { demoDensity, demoEvents, demoJunctions, demoSummary } from '../data/demo';
import type { AppEvent, DashboardSummary, DensityPoint, Junction } from '../types';
import StatCard from '../components/StatCard';
import AnalyticsChart from '../components/AnalyticsChart';
import JunctionCard from '../components/JunctionCard';
import EventTable from '../components/EventTable';
import { DemoBanner, ErrorBanner } from './_shared';

export default function Dashboard({ onLive }: { onLive?: (ev: { type: string }) => void }) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [junctions, setJunctions] = useState<Junction[]>([]);
  const [events, setEvents] = useState<AppEvent[]>([]);
  const [density, setDensity] = useState<DensityPoint[]>(demoDensity);
  const [demo, setDemo] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [s, j, e] = await Promise.all([api.dashboard(), api.junctions(), api.events('?limit=20')]);
      setSummary(s); setJunctions(j); setEvents(e); setDemo(false); setError('');
    } catch (err) {
      setSummary(demoSummary); setJunctions(demoJunctions); setEvents(demoEvents); setDemo(true);
      setError(err instanceof Error ? err.message : 'Backend unavailable — showing DEMO DATA.');
    }
  }, []);
  useEffect(() => { void load(); const t = setInterval(() => void load(), 15000); return () => clearInterval(t); }, [load]);
  useEffect(() => { if (onLive) { /* live events refresh density via parent ws */ } }, [onLive]);

  const s = summary ?? demoSummary;
  const congestionTone = s.congestion === 'high' ? 'red' : s.congestion === 'moderate' ? 'amber' : 'green';
  return (
    <div className="space-y-5">
      {demo && <DemoBanner />}
      {error && !demo && <ErrorBanner msg={error} onRetry={() => void load()} />}
      {demo && <p className="text-xs text-slate2">{error}</p>}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <StatCard icon={Car} label="Total vehicles" value={String(s.totalVehicles)} sub="Across 4 junctions" tone="cyan" />
        <StatCard icon={MapPin} label="Active intersections" value={String(s.activeIntersections)} sub="J1–J4 connected" />
        <StatCard icon={Clock} label="Avg waiting time" value={`${s.avgWaitSec.toFixed(1)}s`} sub="All approaches" tone="amber" />
        <StatCard icon={Gauge} label="Congestion" value={s.congestion.toUpperCase()} sub={`Throughput ${s.throughputPerMin}/min`} tone={congestionTone} />
        <StatCard icon={Ambulance} label="Active emergencies" value={String(s.activeEmergencies)} sub="Priority requests live" tone="red" />
        <StatCard icon={Siren} label="Input mode" value={s.mode === 'sumo' ? 'SUMO' : 'YOLO camera'} sub={s.sumoRunning ? 'Simulation running' : 'Simulation stopped'} tone="green" />
      </div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2"><AnalyticsChart data={density} title="Live traffic density — vehicles & average wait" /></div>
        <div className="rounded-xl border border-line bg-panel p-4 sm:p-5">
          <h3 className="text-base font-semibold text-white">Connected junction status</h3>
          <ul className="mt-3 space-y-2">
            {junctions.map((j) => (
              <li key={j.id} className="flex items-center justify-between rounded-lg bg-panel2 px-3 py-2.5 text-sm">
                <span className="font-medium text-white">{j.id} · {j.name.split('—')[1]?.trim() ?? ''}</span>
                <span className="text-slate2">{j.totalVehicles} veh · {j.phase.replaceAll('_', ' ')}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-slate2">Green-wave coordination: J1 → J2 → J3 → J4. Ambulance route shown in red on the live network map.</p>
          <button onClick={() => setDensity((d) => [...d.slice(1), { time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }), vehicles: s.totalVehicles, avgWait: s.avgWaitSec }])} className="mt-3 min-h-[44px] rounded-lg border border-line px-4 text-sm font-medium text-white">Append live sample point</button>
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {junctions.map((j) => <JunctionCard key={j.id} j={j} />)}
      </div>
      <EventTable events={events} filter="all" onFilter={() => undefined} />
    </div>
  );
}
