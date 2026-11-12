
import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import type { WsStatus } from '../services/websocket';

export default function ConnectionIndicator({ ws, backend, sumo }: { ws: WsStatus; backend: boolean; sumo?: boolean }) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs" role="status" aria-label="Connection status">
      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-medium ${backend ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/15 text-red-300'}`}>
        {backend ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
        Backend {backend ? 'connected' : 'disconnected'}
      </span>
      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-medium ${ws === 'connected' ? 'bg-emerald-500/15 text-emerald-300' : ws === 'connecting' ? 'bg-amber-500/15 text-amber-300' : 'bg-red-500/15 text-red-300'}`}>
        {ws === 'connecting' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : ws === 'connected' ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
        Live feed {ws}
      </span>
      {sumo !== undefined && (
        <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-medium ${sumo ? 'bg-cyan-500/15 text-cyan-300' : 'bg-slate-500/15 text-slate-300'}`}>
          <span className={`h-2 w-2 rounded-full ${sumo ? 'bg-cyan-400 anim-pulse-dot' : 'bg-slate-400'}`} />
          SUMO {sumo ? 'running' : 'stopped'}
        </span>
      )}
    </div>
  );
}
