
import type { LiveEvent } from '../types';

const WS_URL = (import.meta.env.VITE_WS_URL as string | undefined) ?? 'ws://127.0.0.1:8000/ws/telemetry';

export type WsStatus = 'connected' | 'connecting' | 'disconnected';
export type WsHandler = (ev: LiveEvent) => void;
export type StatusHandler = (s: WsStatus) => void;

export class LiveSocket {
  private ws: WebSocket | null = null;
  private handlers = new Set<WsHandler>();
  private statusHandlers = new Set<StatusHandler>();
  private timer: ReturnType<typeof setTimeout> | null = null;
  private closed = false;
  private attempt = 0;
  private lastMsgHash = '';
  status: WsStatus = 'disconnected';

  connect() {
    this.closed = false;
    this.setStatus('connecting');
    const token = localStorage.getItem('smartflow_token');
    const url = token ? `${WS_URL}?token=${encodeURIComponent(token)}` : WS_URL;
    let ws: WebSocket;
    try { ws = new WebSocket(url); } catch { this.scheduleReconnect(); return; }
    this.ws = ws;
    ws.onopen = () => { this.attempt = 0; this.setStatus('connected'); };
    ws.onmessage = (m) => {
      try {
        if (m.data === this.lastMsgHash) return; // duplicate suppression
        this.lastMsgHash = m.data;
        const ev = JSON.parse(m.data) as LiveEvent;
        this.handlers.forEach((h) => h(ev));
      } catch { /* ignore malformed frames */ }
    };
    ws.onclose = () => { this.setStatus('disconnected'); if (!this.closed) this.scheduleReconnect(); };
    ws.onerror = () => { try { ws.close(); } catch { /* noop */ } };
  }
  private scheduleReconnect() {
    if (this.closed) return;
    this.attempt += 1;
    const delay = Math.min(30000, 2000 * this.attempt);
    this.timer = setTimeout(() => this.connect(), delay);
  }
  private setStatus(s: WsStatus) { this.status = s; this.statusHandlers.forEach((h) => h(s)); }
  onEvent(h: WsHandler) { this.handlers.add(h); return () => { this.handlers.delete(h); }; }
  onStatus(h: StatusHandler) { this.statusHandlers.add(h); return () => { this.statusHandlers.delete(h); }; }
  disconnect() { this.closed = true; if (this.timer) clearTimeout(this.timer); this.ws?.close(); this.ws = null; this.setStatus('disconnected'); }
}
export const liveSocket = new LiveSocket();
