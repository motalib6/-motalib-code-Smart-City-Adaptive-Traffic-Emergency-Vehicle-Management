
import { Link } from 'react-router-dom';
import type { Junction } from '../types';
import TrafficSignal from './TrafficSignal';
export default function JunctionCard({ j }: { j: Junction }) {
  const badge = j.congestion === 'high' ? 'bg-red-500/15 text-red-300' : j.congestion === 'moderate' ? 'bg-amber-500/15 text-amber-300' : 'bg-emerald-500/15 text-emerald-300';
  return (
    <Link to={`/junctions?j=${j.id}`} className="block rounded-xl border border-line bg-panel p-4 transition hover:border-teal/60 focus-visible:outline-2 focus-visible:outline-teal sm:p-5" aria-label={`${j.name}, ${j.totalVehicles} vehicles`}>
      <div className="flex items-start justify-between gap-2">
        <div><h3 className="text-base font-semibold text-white">{j.id}</h3><p className="text-xs text-slate2">{j.name}</p></div>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize ${badge}`}>{j.congestion} congestion</span>
      </div>
      <div className="mt-4"><TrafficSignal phase={j.phase} remainingSec={j.phaseRemainingSec} /></div>
      <dl className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
        <div className="rounded-lg bg-panel2 p-2"><dt className="text-slate2">Vehicles</dt><dd className="mt-0.5 text-base font-bold text-white">{j.totalVehicles}</dd></div>
        <div className="rounded-lg bg-panel2 p-2"><dt className="text-slate2">Green</dt><dd className="mt-0.5 text-base font-bold text-white">{j.greenSec}s</dd></div>
        <div className="rounded-lg bg-panel2 p-2"><dt className="text-slate2">Max queue</dt><dd className="mt-0.5 text-base font-bold text-white">{Math.max(...j.approaches.map((a) => a.queue))}</dd></div>
      </dl>
    </Link>
  );
}
