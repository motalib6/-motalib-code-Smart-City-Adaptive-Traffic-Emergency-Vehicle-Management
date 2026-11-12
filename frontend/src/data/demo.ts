
import type { AppEvent, DashboardSummary, DensityPoint, Emergency, Junction, Phase } from '../types';

export const DEMO_LABEL = 'DEMO DATA — backend not connected; preview values only, not real traffic.';

function approaches(base: number): Junction['approaches'] {
  return (['N', 'S', 'E', 'W'] as const).map((a, i) => ({
    approach: a,
    vehicles: base + i * 3,
    queue: Math.max(0, base - 6 + i * 2),
    avgWaitSec: 18 + i * 6,
    demand: Math.round((0.35 + i * 0.12) * 100) / 100,
  }));
}
export const demoJunctions: Junction[] = (['J1', 'J2', 'J3', 'J4'] as const).map((id, i) => ({
  id, name: `Junction ${id.slice(1)} — ${['Patia', 'KIIT Square', 'Vani Vihar', 'Rasulgarh'][i]}`,
  phase: (['GREEN_NS', 'GREEN_EW', 'YELLOW_NS', 'GREEN_NS'] as Phase[])[i],
  phaseRemainingSec: [22, 31, 4, 18][i],
  greenSec: [38, 42, 35, 40][i], yellowSec: 4, allRedSec: 2,
  approaches: approaches(14 + i * 4),
  totalVehicles: 62 + i * 11,
  congestion: (['moderate', 'high', 'low', 'moderate'] as const)[i],
}));
export const demoSummary: DashboardSummary = {
  totalVehicles: 284, activeIntersections: 4, avgWaitSec: 27.4,
  congestion: 'moderate', activeEmergencies: 1, throughputPerMin: 96, mode: 'sumo', sumoRunning: true,
};
export const demoDensity: DensityPoint[] = Array.from({ length: 12 }, (_, i) => ({
  time: `${8 + Math.floor(i / 2)}:${i % 2 === 0 ? '00' : '30'}`,
  vehicles: 180 + Math.round(60 * Math.sin(i / 2) + i * 4),
  avgWait: 18 + Math.round(10 * Math.sin(i / 3) + i),
}));
export const demoEvents: AppEvent[] = [
  { id: 1, timestamp: new Date().toISOString(), type: 'PRIORITY_GRANTED', junctionId: 'J1', source: 'emergency', message: 'Priority green granted to AMB-01 at J1 (safe transition via yellow + all-red).', severity: 'critical' },
  { id: 2, timestamp: new Date().toISOString(), type: 'PHASE_CHANGE', junctionId: 'J2', source: 'adaptive', message: 'J2 green extended to 42s — East approach demand 0.78.', severity: 'info' },
  { id: 3, timestamp: new Date().toISOString(), type: 'CONGESTION', junctionId: 'J3', source: 'sumo', message: 'J3 East queue exceeded 12 vehicles.', severity: 'warning' },
  { id: 4, timestamp: new Date().toISOString(), type: 'SIMULATION_STARTED', source: 'system', message: 'SUMO simulation started — scenario: rush hour.', severity: 'info' },
];
export const demoEmergency: Emergency = {
  id: 'EMG-1042', ambulanceId: 'AMB-01', fromJunction: 'J1', toJunction: 'J4',
  route: ['J1', 'J2', 'J4'], status: 'priority_granted', etaSec: 96, progressPct: 34,
  currentJunction: 'J1', nextJunction: 'J2', speedKmh: 42,
};
export const demoVehicles = [
  { id: 'v1', type: 'car' as const, x: 12, y: 46, junction: 'J1', speedKmh: 28 },
  { id: 'v2', type: 'bus' as const, x: 38, y: 52, junction: 'J1', speedKmh: 22 },
  { id: 'v3', type: 'motorcycle' as const, x: 62, y: 44, junction: 'J2', speedKmh: 35 },
  { id: 'v4', type: 'ambulance' as const, x: 26, y: 48, junction: 'J1', speedKmh: 42 },
  { id: 'v5', type: 'truck' as const, x: 78, y: 55, junction: 'J3', speedKmh: 18 },
  { id: 'v6', type: 'car' as const, x: 50, y: 82, junction: 'J4', speedKmh: 30 },
];
