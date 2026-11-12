
import type { Phase, SignalColor } from '../types';

export function phaseColors(phase: Phase): { ns: SignalColor; ew: SignalColor } {
  if (phase === 'GREEN_NS') return { ns: 'green', ew: 'red' };
  if (phase === 'GREEN_EW') return { ns: 'red', ew: 'green' };
  if (phase === 'YELLOW_NS' || phase === 'ALL_RED_TO_EW') return { ns: phase === 'YELLOW_NS' ? 'yellow' : 'red', ew: 'red' };
  return { ns: 'red', ew: phase === 'YELLOW_EW' ? 'yellow' : 'red' };
}
function Lamp({ color, active, label }: { color: SignalColor; active: boolean; label: string }) {
  const bg = color === 'green' ? 'bg-emerald-400' : color === 'yellow' ? 'bg-amber-400' : 'bg-red-500';
  return <span title={label} aria-label={label} className={`block h-3.5 w-3.5 rounded-full ${active ? bg + ' shadow-[0_0_10px_currentColor]' : 'bg-slate-700'}`} />;
}
export default function TrafficSignal({ phase, remainingSec, compact = false }: { phase: Phase; remainingSec: number; compact?: boolean }) {
  const c = phaseColors(phase);
  const label = phase.replaceAll('_', ' ');
  return (
    <div className="flex items-center gap-3" role="img" aria-label={`Signal phase ${label}, ${remainingSec} seconds remaining`}>
      <div className="flex items-center gap-2 rounded-lg bg-ink px-2.5 py-2" title="North–South">
        <Lamp color="red" active={c.ns === 'red'} label="NS red" />
        <Lamp color="yellow" active={c.ns === 'yellow'} label="NS yellow" />
        <Lamp color="green" active={c.ns === 'green'} label="NS green" />
        {!compact && <span className="ml-1 text-[10px] font-semibold text-slate2">N–S</span>}
      </div>
      <div className="flex items-center gap-2 rounded-lg bg-ink px-2.5 py-2" title="East–West">
        <Lamp color="red" active={c.ew === 'red'} label="EW red" />
        <Lamp color="yellow" active={c.ew === 'yellow'} label="EW yellow" />
        <Lamp color="green" active={c.ew === 'green'} label="EW green" />
        {!compact && <span className="ml-1 text-[10px] font-semibold text-slate2">E–W</span>}
      </div>
      <div className="text-left">
        <p className="text-xs font-semibold text-white">{label}</p>
        <p className="text-lg font-bold tabular-nums text-teal">{remainingSec}s</p>
      </div>
    </div>
  );
}
