
import { Menu, RefreshCw } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import ConnectionIndicator from './ConnectionIndicator';
import type { WsStatus } from '../services/websocket';

const TITLES: Record<string, string> = {
  '/dashboard': 'Command Dashboard', '/live-network': 'Live Traffic Network', '/camera': 'AI Camera Monitoring',
  '/junctions': 'Adaptive Junction Control', '/emergency': 'Emergency Vehicle Management',
  '/analytics': 'Analytics & Events', '/events': 'Event Log', '/admin': 'Administration',
};
export default function Topbar({ onMenu, ws, backend, sumo, onRefresh }: { onMenu: () => void; ws: WsStatus; backend: boolean; sumo?: boolean; onRefresh?: () => void }) {
  const { pathname } = useLocation();
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-ink/90 backdrop-blur">
      <div className="flex min-h-[60px] flex-wrap items-center gap-3 px-4 py-2 sm:px-6">
        <button onClick={onMenu} className="rounded-lg p-2.5 text-slate2 hover:text-white lg:hidden" aria-label="Open menu"><Menu className="h-5 w-5" /></button>
        <h1 className="text-base font-bold text-white sm:text-lg">{TITLES[pathname] ?? 'SMARTFLOW ODISHA'}</h1>
        <div className="ml-auto flex items-center gap-3">
          <ConnectionIndicator ws={ws} backend={backend} sumo={sumo} />
          {onRefresh && <button onClick={onRefresh} className="inline-flex min-h-[44px] items-center gap-2 rounded-lg border border-line px-3 text-sm text-slate2 hover:text-white" aria-label="Refresh data"><RefreshCw className="h-4 w-4" /> <span className="hidden sm:inline">Refresh</span></button>}
        </div>
      </div>
    </header>
  );
}
