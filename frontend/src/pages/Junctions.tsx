
import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { demoJunctions } from '../data/demo';
import type { Junction } from '../types';
import TrafficSignal from '../components/TrafficSignal';
import { DemoBanner, ErrorBanner, card } from './_shared';

export default function Junctions() {
  const [params, setParams] = useSearchParams();
  const selected = params.get('j') ?? 'J1';
  const [junctions, setJunctions] = useState<Junction[]>(demoJunctions);
  const [demo, setDemo] = useState(true);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<string[]>([
    'GREEN_NS 38s — North demand 0.71, South 0.64 (highest demand served first)',
    'YELLOW_NS 4s — safe clearance before phase change',
    'ALL_RED_TO_EW 2s — intersection cleared',
    'GREEN_EW 42s — East demand 0.78 exceeded North/South',
  ]);
  const load = useCallback(async () => {
    try { const j = await api.junctions(); setJunctions(j); setDemo(false); setError(''); }
    catch (err) { setDemo(true); setError(err instanceof Error ? err.message : 'Backend unavailable.'); }
  }, []);
  useEffect(() => { void load(); const i = setInterval(() => void load(), 8000); return () => clearInterval(i); }, [load]);

  const j = junctions.find((x) => x.id === selected) ?? junctions[0];
  const maxDemand = j.approaches.reduce((a, b) => (b.demand > a.demand ? b : a));
  const recommended = Math.round(Math.min(60, Math.max(15, 15 + 55 * maxDemand.demand)));
  const explanation = `Why this phase? ${maxDemand.approach} approach has the highest demand (${maxDemand.demand.toFixed(2)} = queue ${maxDemand.queue} + ${maxDemand.vehicles} vehicles + ${maxDemand.avgWaitSec}s avg wait). ` +
    `Recommended green ${recommended}s (clipped to 15–60s). ${j.phase.includes('YELLOW') || j.phase.includes('ALL_RED') ? 'Currently in a safety clearance phase — yellow/all-red are never skipped.' : 'Low-demand approaches are still served each cycle (starvation prevention).'}`;

  return (
    <div className="space-y-5">
      {demo && <DemoBanner />}
      {error && <ErrorBanner msg={error} onRetry={() => void load()} />}
      <div className="flex flex-wrap gap-2" role="group" aria-label="Select junction">
        {junctions.map((x) => (
          <button key={x.id} onClick={() => setParams({ j: x.id })} aria-pressed={selected === x.id}
            className={`min-h-[44px] rounded-lg px-5 text-sm font-semibold ${selected === x.id ? 'bg-teal text-ink' : 'border border-line bg-panel text-slate2 hover:text-white'}`}>{x.id}</button>
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className={card}>
          <h2 className="text-lg font-bold text-white">{j.id} — {j.name}</h2>
          <div className="mt-4"><TrafficSignal phase={j.phase} remainingSec={j.phaseRemainingSec} /></div>
          <dl className="mt-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
            <div className="rounded-lg bg-panel2 p-3"><dt className="text-slate2">Recommended green</dt><dd className="mt-1 text-xl font-bold text-teal">{recommended}s</dd></div>
            <div className="rounded-lg bg-panel2 p-3"><dt className="text-slate2">Actual green</dt><dd className="mt-1 text-xl font-bold text-white">{j.greenSec}s</dd></div>
            <div className="rounded-lg bg-panel2 p-3"><dt className="text-slate2">Yellow</dt><dd className="mt-1 text-xl font-bold text-white">{j.yellowSec}s</dd></div>
            <div className="rounded-lg bg-panel2 p-3"><dt className="text-slate2">All-red</dt><dd className="mt-1 text-xl font-bold text-white">{j.allRedSec}s</dd></div>
          </dl>
          <div className="mt-4 rounded-lg border border-teal/40 bg-teal/5 p-4">
            <h3 className="font-semibold text-white">Why was this signal phase selected?</h3>
            <p className="mt-1 text-sm leading-relaxed text-slate2">{explanation}</p>
          </div>
        </div>
        <div className={card}>
          <h3 className="font-semibold text-white">Traffic demand by approach</h3>
          <ul className="mt-3 space-y-3">
            {j.approaches.map((a) => (
              <li key={a.approach}>
                <div className="mb-1 flex justify-between text-sm"><span className="text-slate2">{a.approach} approach</span><span className="font-medium text-white">{a.vehicles} veh · queue {a.queue} · wait {a.avgWaitSec}s · demand {a.demand.toFixed(2)}</span></div>
                <div className="h-2.5 overflow-hidden rounded-full bg-line"><div className="h-full rounded-full bg-teal" style={{ width: `${Math.round(a.demand * 100)}%` }} /></div>
              </li>
            ))}
          </ul>
          <h3 className="mt-6 font-semibold text-white">Signal history</h3>
          <ul className="mt-2 space-y-1.5 text-sm text-slate2">
            {history.map((h, i) => <li key={i} className="rounded bg-panel2 px-3 py-2">{h}</li>)}
          </ul>
          <button onClick={() => setHistory((h) => [`${j.phase} ${j.greenSec}s — demand snapshot at ${new Date().toLocaleTimeString('en-IN')}`, ...h].slice(0, 8))} className="mt-3 min-h-[44px] rounded-lg border border-line px-4 text-sm font-medium text-white">Record current decision</button>
          <p className="mt-3 text-xs text-slate2">State machine: GREEN_NS → YELLOW_NS → ALL_RED_TO_EW → GREEN_EW → YELLOW_EW → ALL_RED_TO_NS. Every transition is validated against the conflict matrix before it is applied.</p>
        </div>
      </div>
    </div>
  );
}
