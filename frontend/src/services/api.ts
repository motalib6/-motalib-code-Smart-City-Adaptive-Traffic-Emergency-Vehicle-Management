
import type { AdminSettings, AppEvent, DashboardSummary, Emergency, ExperimentRun, Junction, User } from '../types';

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000';
export const API_BASE = BASE.replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}

function token(): string | null { return localStorage.getItem('smartflow_token'); }

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...(init.headers as Record<string, string> ?? {}) };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, 'Backend unreachable — is FastAPI running on ' + API_BASE + '?');
  }
  if (res.status === 401) { localStorage.removeItem('smartflow_token'); localStorage.removeItem('smartflow_user'); throw new ApiError(401, 'Session expired — please sign in again.'); }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try { const j = await res.json(); msg = (j as { detail?: string }).detail ?? msg; } catch { /* keep default */ }
    throw new ApiError(res.status, msg);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  health: () => req<{ status: string; sumo_available?: boolean; mode?: string }>('/api/health'),
  // Backend LoginRequest expects { email, password } — the login form's
  // username field holds the user's email address.
  login: async (username: string, password: string) => {
    const res = await req<{ access_token: string; token_type: string; role: string; email: string; user?: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: username, password }),
    });
    const userObj: User = res.user ?? {
      id: 1,
      username: res.email,
      role: (res.role?.toLowerCase() as any) ?? 'admin',
    };
    return {
      access_token: res.access_token,
      token_type: res.token_type,
      user: userObj,
    };
  },
  me: () => req<User>('/api/auth/me'),
  dashboard: async () => {
    const raw = await req<any>('/api/dashboard/summary');
    if (raw && 'active_junctions' in raw) {
      // Map snake_case backend keys to frontend DashboardSummary interface
      const totalVeh = raw.total_vehicles ?? 0;
      const avgWait = raw.avg_wait_s ?? 0;
      return {
        totalVehicles: totalVeh,
        activeIntersections: raw.active_junctions ?? 4,
        avgWaitSec: avgWait,
        congestion: totalVeh > 30 ? 'high' : totalVeh > 10 ? 'moderate' : 'low',
        activeEmergencies: raw.active_emergencies ?? 0,
        throughputPerMin: Math.max(0, Math.round(totalVeh * 1.5)),
        mode: (raw.source === 'sumo' ? 'sumo' : 'yolo') as any,
        sumoRunning: !!raw.simulation_running,
      } as DashboardSummary;
    }
    return raw as DashboardSummary;
  },
  junctions: async () => {
    const raw = await req<any[]>('/api/junctions');
    if (Array.isArray(raw)) {
      return raw.map((j) => {
        const live = j.live ?? {};
        const counts = live.counts ?? { N: 0, S: 0, E: 0, W: 0 };
        const queues = live.queues ?? { N: 0, S: 0, E: 0, W: 0 };
        const approaches = (['N', 'S', 'E', 'W'] as const).map((app) => ({
          approach: app,
          vehicles: counts[app] ?? 0,
          queue: queues[app] ?? 0,
          avgWaitSec: live.avg_wait_s ?? 0,
          demand: Math.round(((counts[app] ?? 0) * 0.3 + (queues[app] ?? 0) * 0.5) * 100) / 100,
        }));
        const totalVeh = live.total ?? 0;
        return {
          id: j.id,
          name: j.name,
          phase: j.phase ?? 'GREEN_NS',
          phaseRemainingSec: 25,
          greenSec: 35,
          yellowSec: 3,
          allRedSec: 2,
          approaches,
          totalVehicles: totalVeh,
          congestion: totalVeh > 15 ? 'high' : totalVeh > 5 ? 'moderate' : 'low',
        } as Junction;
      });
    }
    return raw as Junction[];
  },
  junction: (id: string) => req<Junction>(`/api/junctions/${id}`),
  events: async (params = '') => {
    const raw = await req<any[]>(`/api/events${params}`);
    if (Array.isArray(raw)) {
      return raw.map((e) => ({
        id: e.id,
        timestamp: e.created_at ?? e.timestamp ?? new Date().toISOString(),
        type: e.type,
        junctionId: e.junction_id ?? e.junctionId,
        source: e.source ?? 'system',
        message: e.message,
        severity: (e.type?.includes('EMERGENCY') || e.type?.includes('ALL_RED') ? 'critical' : e.type?.includes('YELLOW') ? 'warning' : 'info') as any,
      } as AppEvent));
    }
    return raw as AppEvent[];
  },
  analyticsSummary: () => req<{ meanWaitSec: number; throughput: number; congestionHistory: { time: string; level: number }[] }>('/api/analytics/summary'),
  experiments: () => req<ExperimentRun[]>('/api/analytics/experiments'),
  emergencies: async () => {
    const raw = await req<any[]>('/api/emergencies');
    if (Array.isArray(raw)) {
      return raw.map((em) => {
        const routeArr = Array.isArray(em.route) ? em.route : typeof em.route === 'string' ? em.route.split(',') : ['J1', 'J2', 'J4'];
        return {
          id: String(em.id),
          ambulanceId: em.ambulance_id ?? em.ambulanceId ?? 'AMB-01',
          fromJunction: em.current_junction ?? em.fromJunction ?? 'J1',
          toJunction: em.destination_junction ?? em.toJunction ?? 'J4',
          route: routeArr,
          status: (em.status?.toLowerCase() as any) ?? 'requested',
          etaSec: Math.round(em.eta_s ?? em.etaSec ?? 30),
          progressPct: Math.round((em.progress ?? 0) * 100),
          currentJunction: em.current_junction ?? 'J1',
          nextJunction: em.next_junction ?? routeArr[1] ?? 'J2',
          speedKmh: em.speed_kmh ?? 45,
        } as Emergency;
      });
    }
    return raw as Emergency[];
  },
  // Backend EmergencyCreateRequest uses snake_case: ambulance_id,
  // current_junction, destination_junction. Location uses x/y/speed_kmh.
  createEmergency: (body: { ambulanceId: string; fromJunction: string; toJunction: string; route: string[] }) =>
    req<Emergency>('/api/emergencies', { method: 'POST', body: JSON.stringify({ ambulance_id: body.ambulanceId, current_junction: body.fromJunction, destination_junction: body.toJunction, route: body.route }) }),
  emergencyLocation: (id: string, body: { lat: number; lng: number; speedKmh: number }) =>
    req<Emergency>(`/api/emergencies/${id}/location`, { method: 'POST', body: JSON.stringify({ x: body.lat, y: body.lng, speed_kmh: body.speedKmh }) }),
  completeEmergency: (id: string) => req<Emergency>(`/api/emergencies/${id}/complete`, { method: 'POST' }),
  // Backend SimulationStartRequest requires a body (scenario + engine,
  // both have defaults server-side but FastAPI still requires the object).
  simStart: (scenario = 'normal') => req<{ status: string }>('/api/simulation/start', { method: 'POST', body: JSON.stringify({ scenario, engine: 'simulated' }) }),
  simPause: () => req<{ status: string }>('/api/simulation/pause', { method: 'POST' }),
  simReset: () => req<{ status: string }>('/api/simulation/reset', { method: 'POST' }),
  simScenario: (scenario: string) => req<{ status: string }>('/api/simulation/scenario', { method: 'POST', body: JSON.stringify({ scenario }) }),
  trafficCurrent: () => req<{ junctions: Junction[]; mode: string }>('/api/traffic/current'),
  // Backend TrafficInjectRequest: junction_id, approach, vehicle_count, queue_length.
  injectTraffic: (body: { junctionId: string; approach: string; vehicles: number; queue: number }) =>
    req<{ ok: boolean }>('/api/traffic/inject', { method: 'POST', body: JSON.stringify({ junction_id: body.junctionId, approach: body.approach, vehicle_count: body.vehicles, queue_length: body.queue }) }),
  visionStart: (body: { source: 'upload' | 'webcam'; filename?: string }) =>
    req<{ status: string }>('/api/vision/start', { method: 'POST', body: JSON.stringify(body) }),
  visionStop: () => req<{ status: string }>('/api/vision/stop', { method: 'POST' }),
  uploadVideo: (file: File) => {
    const fd = new FormData(); fd.append('file', file);
    const t = token();
    return fetch(`${API_BASE}/api/vision/upload`, { method: 'POST', headers: t ? { Authorization: `Bearer ${t}` } : {}, body: fd })
      .then(async (r) => { if (!r.ok) throw new ApiError(r.status, 'Video upload failed'); return (await r.json()) as { filename: string }; });
  },
  adminSettings: () => req<AdminSettings>('/api/admin/settings'),
  saveAdminSettings: (s: AdminSettings) => req<AdminSettings>('/api/admin/settings', { method: 'PUT', body: JSON.stringify(s) }),
  users: () => req<User[]>('/api/admin/users'),
};
