
import type { Junction, VehiclePos } from '../types';
import TrafficSignal from './TrafficSignal';

const POS: Record<string, { x: number; y: number }> = { J1: { x: 25, y: 28 }, J2: { x: 72, y: 28 }, J3: { x: 25, y: 72 }, J4: { x: 72, y: 72 } };
const VCOLOR: Record<string, string> = { car: '#38BDF8', bus: '#FBBF24', motorcycle: '#A78BFA', truck: '#94A3B8', ambulance: '#F87171' };

export default function TrafficNetworkMap({ junctions, vehicles, demo }: { junctions: Junction[]; vehicles: VehiclePos[]; demo: boolean }) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-line bg-panel">
      {demo && <span className="absolute right-3 top-3 z-10 rounded-full bg-amber-500/20 px-2.5 py-1 text-xs font-semibold text-amber-300">DEMO DATA</span>}
      <svg viewBox="0 0 100 100" className="h-auto w-full" role="img" aria-label="Connected 2 by 2 traffic network, junctions J1 to J4">
        <rect x="0" y="0" width="100" height="100" fill="#0E1729" />
        {/* roads */}
        <rect x="20" y="0" width="10" height="100" fill="#1E2C47" />
        <rect x="67" y="0" width="10" height="100" fill="#1E2C47" />
        <rect x="0" y="23" width="100" height="10" fill="#1E2C47" />
        <rect x="0" y="67" width="100" height="10" fill="#1E2C47" />
        {/* lane dashes */}
        <line x1="25" y1="0" x2="25" y2="100" stroke="#38BDF8" strokeWidth="0.4" strokeDasharray="2 2" opacity="0.5" />
        <line x1="72" y1="0" x2="72" y2="100" stroke="#38BDF8" strokeWidth="0.4" strokeDasharray="2 2" opacity="0.5" />
        <line x1="0" y1="28" x2="100" y2="28" stroke="#38BDF8" strokeWidth="0.4" strokeDasharray="2 2" opacity="0.5" />
        <line x1="0" y1="72" x2="100" y2="72" stroke="#38BDF8" strokeWidth="0.4" strokeDasharray="2 2" opacity="0.5" />
        {/* emergency route J1->J2->J4 */}
        <polyline points="25,28 72,28 72,72" fill="none" stroke="#F87171" strokeWidth="1" strokeDasharray="3 2" opacity="0.9" />
        {Object.entries(POS).map(([id, p]) => (
          <g key={id}>
            <rect x={p.x - 6} y={p.y - 6} width="12" height="12" rx="2" fill="#16223A" stroke="#15C6B3" strokeWidth="0.6" />
            <text x={p.x} y={p.y + 1.2} textAnchor="middle" fill="#fff" fontSize="4" fontWeight="700">{id}</text>
          </g>
        ))}
        {vehicles.map((v) => (
          <g key={v.id}>
            <circle cx={v.x} cy={v.y} r={v.type === 'ambulance' ? 2.4 : 1.8} fill={VCOLOR[v.type] ?? '#38BDF8'} stroke="#0B1220" strokeWidth="0.5" />
            {v.type === 'ambulance' && <circle cx={v.x} cy={v.y} r="3.6" fill="none" stroke="#F87171" strokeWidth="0.5" opacity="0.7" />}
          </g>
        ))}
      </svg>
      <div className="grid grid-cols-2 gap-3 border-t border-line p-4 lg:grid-cols-4">
        {junctions.map((j) => (
          <div key={j.id} className="rounded-lg bg-panel2 p-3">
            <p className="text-sm font-semibold text-white">{j.id} · {j.totalVehicles} veh</p>
            <div className="mt-2"><TrafficSignal phase={j.phase} remainingSec={j.phaseRemainingSec} compact /></div>
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-4 border-t border-line px-4 py-3 text-xs text-slate2">
        <span><i className="mr-1 inline-block h-2.5 w-2.5 rounded-full bg-[#38BDF8]" />Car</span>
        <span><i className="mr-1 inline-block h-2.5 w-2.5 rounded-full bg-[#FBBF24]" />Bus</span>
        <span><i className="mr-1 inline-block h-2.5 w-2.5 rounded-full bg-[#A78BFA]" />Motorcycle</span>
        <span><i className="mr-1 inline-block h-2.5 w-2.5 rounded-full bg-[#94A3B8]" />Truck</span>
        <span><i className="mr-1 inline-block h-2.5 w-2.5 rounded-full bg-[#F87171]" />Ambulance (dashed red = emergency route)</span>
      </div>
    </div>
  );
}
