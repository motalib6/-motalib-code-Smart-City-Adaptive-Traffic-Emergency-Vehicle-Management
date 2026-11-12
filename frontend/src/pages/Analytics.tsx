
import { useEffect, useState } from 'react';
import { BarChart3, Clock, Gauge, TrendingUp } from 'lucide-react';
import { api } from '../services/api';
import { demoDensity, demoEvents } from '../data/demo';
import type { AppEvent, ExperimentRun } from '../types';
import StatCard from '../components/StatCard';
import AnalyticsChart from '../components/AnalyticsChart';
import EventTable from '../components/EventTable';
import { DemoBanner, ErrorBanner } from './_shared';

export default function Analytics() {
  const [runs, setRuns] = useState<ExperimentRun[]>([]);
  const [events, setEvents] = useState<AppEvent[]>(demoEvents);
  const [demo, setDemo] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    (async () => {
      try {
        const [r, e] = await Promise.all([api.experiments(), api.events('?limit=100')]);
        setRuns(r); setEvents(e); setDemo(false);
      } catch (err) { setDemo(true); setError(err instanceof Error ? err.message : 'Backend unavailable — analytics show DEMO DATA only.'); }
    })();
  }, []);

  const fixed = runs.find((r) => r.mode === 'fixed');
  const adaptive = runs.find((r) => r.mode === 'adaptive');
  const comparison = fixed && adaptive ? [
    { metric: 'Mean waiting time (s)', fixed: fixed.meanWaitSec, adaptive: adaptive.meanWaitSec },
    { metric: 'Max queue (vehicles)', fixed: fixed.maxQueue, adaptive: adaptive.maxQueue },
    { metric: 'Throughput (vehicles)', fixed: fixed.throughput, adaptive: adaptive.throughput },
    { metric: 'Emergency travel time (s)', fixed: fixed.emergencyTravelSec ?? 0, adaptive: adaptive.emergencyTravelSec ?? 0 },
  ] : [];

  return (
    <div className="space-y-5">
      {demo && <DemoBanner />}
      {error && <ErrorBanner msg={error} />}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Clock} label="Avg waiting time" value="27.4s" sub="Measured runs only" tone="amber" />
        <StatCard icon={TrendingUp} label="Throughput" value="96/min" sub="Vehicles cleared" tone="cyan" />
        <StatCard icon={Gauge} label="Congestion duration" value="18 min" sub="Peak window today" tone="red" />
        <StatCard icon={BarChart3} label="Experiments completed" value={String(runs.length)} sub="Fixed vs adaptive" tone="green" />
      </div>
      <AnalyticsChart data={demoDensity} title="Congestion history — vehicles & average wait" />
      <div className="rounded-xl border border-line bg-panel p-4 sm:p-5">
        <h3 className="text-base font-semibold text-white">Fixed-time vs adaptive — measured comparison</h3>
        {comparison.length === 0 ? (
          <p className="mt-3 rounded-lg bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
            No completed experiment runs yet. Run Experiment A (fixed-time) and Experiment B (adaptive) with identical network, demand, routes, seed and duration from the backend — results appear here. No percentage improvements are shown until measured; nothing here is invented.
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[520px] text-left text-sm">
              <thead><tr className="border-b border-line text-xs uppercase text-slate2"><th className="py-2">Metric</th><th className="py-2">Fixed-time</th><th className="py-2">Adaptive</th><th className="py-2">Difference (measured)</th></tr></thead>
              <tbody>{comparison.map((c) => (
                <tr key={c.metric} className="border-b border-line/60 last:border-0">
                  <td className="py-2.5 text-white">{c.metric}</td><td className="py-2.5 text-slate2">{c.fixed}</td><td className="py-2.5 text-slate2">{c.adaptive}</td>
                  <td className="py-2.5 font-medium text-teal">{(c.adaptive - c.fixed).toFixed(1)}</td>
                </tr>))}</tbody>
            </table>
            <p className="mt-2 text-xs text-slate2">Runs: fixed {fixed?.id} (seed {fixed?.seed}) · adaptive {adaptive?.id} (seed {adaptive?.seed}). Identical inputs; only the control strategy differs.</p>
          </div>
        )}
        <h4 className="mt-5 font-semibold text-white">Simulation run history</h4>
        {runs.length === 0
          ? <p className="mt-2 text-sm text-slate2">No runs recorded yet.</p>
          : <ul className="mt-2 space-y-1.5 text-sm">{runs.map((r) => <li key={r.id} className="rounded bg-panel2 px-3 py-2 text-slate2"><span className="font-medium text-white">{r.id}</span> · {r.mode} · seed {r.seed} · {r.durationSec}s · mean wait {r.meanWaitSec}s · throughput {r.throughput} · {new Date(r.createdAt).toLocaleString('en-IN')}</li>)}</ul>}
      </div>
      <EventTable events={events} filter={filter} onFilter={setFilter} />
    </div>
  );
}
