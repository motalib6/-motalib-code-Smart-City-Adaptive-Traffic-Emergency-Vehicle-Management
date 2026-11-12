
import { AlertTriangle } from 'lucide-react';
export function DemoBanner() {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-200" role="status">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <span><strong>DEMO DATA</strong> — backend not connected. These are preview values only, not real traffic. Start the FastAPI backend (port 8000) to see live SUMO data.</span>
    </div>
  );
}
export function ErrorBanner({ msg, onRetry }: { msg: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-200" role="alert">
      <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden /><span className="flex-1">{msg}</span>
      {onRetry && <button onClick={onRetry} className="min-h-[44px] rounded-lg bg-red-500/20 px-4 font-semibold">Retry</button>}
    </div>
  );
}
export const card = 'rounded-xl border border-line bg-panel p-4 sm:p-5';
