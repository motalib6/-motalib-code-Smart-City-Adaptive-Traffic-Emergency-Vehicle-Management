
import { Ambulance, Clock, MapPin } from 'lucide-react';
import type { Emergency } from '../types';
export default function EmergencyStatus({ e }: { e: Emergency }) {
  return (
    <div className="rounded-xl border border-red-500/40 bg-red-500/5 p-4 sm:p-5">
      <div className="flex items-center gap-2">
        <Ambulance className="h-5 w-5 text-danger" aria-hidden />
        <h3 className="font-semibold text-white">{e.ambulanceId} — {e.status.replaceAll('_', ' ').toUpperCase()}</h3>
      </div>
      <p className="mt-2 flex items-center gap-1.5 text-sm text-slate2"><MapPin className="h-4 w-4" /> Route {e.route.join(' → ')} · now at {e.currentJunction}, next {e.nextJunction}</p>
      <p className="mt-1 flex items-center gap-1.5 text-sm text-slate2"><Clock className="h-4 w-4" /> ETA {Math.round(e.etaSec / 60)} min {e.etaSec % 60}s · {e.speedKmh} km/h</p>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-line" role="progressbar" aria-valuenow={e.progressPct} aria-valuemin={0} aria-valuemax={100} aria-label="Route progress">
        <div className="h-full bg-danger transition-all" style={{ width: `${e.progressPct}%` }} />
      </div>
      <p className="mt-1 text-right text-xs text-slate2">{e.progressPct}% of route complete</p>
    </div>
  );
}
