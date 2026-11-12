
import type { AdminSettings, AppEvent, AuthResponse, DashboardSummary, Emergency, ExperimentRun, Junction, User } from '../types';

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
  login: (username: string, password: string) =>
    req<AuthResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email: username, password }) }),
  me: () => req<User>('/api/auth/me'),
  dashboard: () => req<DashboardSummary>('/api/dashboard/summary'),
  junctions: () => req<Junction[]>('/api/junctions'),
  junction: (id: string) => req<Junction>(`/api/junctions/${id}`),
  events: (params = '') => req<AppEvent[]>(`/api/events${params}`),
  analyticsSummary: () => req<{ meanWaitSec: number; throughput: number; congestionHistory: { time: string; level: number }[] }>('/api/analytics/summary'),
  experiments: () => req<ExperimentRun[]>('/api/analytics/experiments'),
  emergencies: () => req<Emergency[]>('/api/emergencies'),
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
