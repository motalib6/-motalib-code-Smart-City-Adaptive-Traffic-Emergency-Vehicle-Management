
import { Download } from 'lucide-react';
import type { AppEvent } from '../types';
export function eventsToCsv(events: AppEvent[]): string {
  const rows = [['id', 'timestamp', 'type', 'junction', 'source', 'severity', 'message'], ...events.map((e) => [String(e.id), e.timestamp, e.type, e.junctionId ?? '', e.source, e.severity, `"${e.message.replaceAll('"', '""')}"`])];
  return rows.map((r) => r.join(',')).join('\n');
}
export default function EventTable({ events, filter, onFilter }: { events: AppEvent[]; filter: string; onFilter: (f: string) => void }) {
  const shown = filter === 'all' ? events : events.filter((e) => e.severity === filter || e.type === filter || e.source === filter);
  const download = () => {
    const blob = new Blob([eventsToCsv(shown)], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'smartflow-events.csv'; a.click();
    URL.revokeObjectURL(a.href);
  };
  const sev = (s: string) => s === 'critical' ? 'bg-red-500/15 text-red-300' : s === 'warning' ? 'bg-amber-500/15 text-amber-300' : 'bg-slate-500/15 text-slate-300';
  return (
    <div className="rounded-xl border border-line bg-panel">
      <div className="flex flex-wrap items-center justify-between gap-3 p-4">
        <h3 className="text-base font-semibold text-white">Event log ({shown.length})</h3>
        <div className="flex flex-wrap items-center gap-2">
          <label className="sr-only" htmlFor="event-filter">Filter events</label>
          <select id="event-filter" value={filter} onChange={(e) => onFilter(e.target.value)} className="min-h-[44px] rounded-lg border border-line bg-panel2 px-3 text-sm text-white">
            <option value="all">All events</option>
            <option value="info">Info</option><option value="warning">Warning</option><option value="critical">Critical</option>
            <option value="emergency">Emergency</option><option value="adaptive">Adaptive</option>
          </select>
          <button onClick={download} className="inline-flex min-h-[44px] items-center gap-2 rounded-lg bg-teal px-4 text-sm font-semibold text-ink hover:bg-teal-dark">
            <Download className="h-4 w-4" aria-hidden /> Export CSV
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead><tr className="border-y border-line text-xs uppercase text-slate2"><th className="px-4 py-3">Time</th><th className="px-4 py-3">Type</th><th className="px-4 py-3">Junction</th><th className="px-4 py-3">Severity</th><th className="px-4 py-3">Message</th></tr></thead>
          <tbody>
            {shown.map((e) => (
              <tr key={e.id} className="border-b border-line/60 last:border-0">
                <td className="whitespace-nowrap px-4 py-3 text-slate2">{new Date(e.timestamp).toLocaleTimeString('en-IN')}</td>
                <td className="px-4 py-3 font-medium text-white">{e.type}</td>
                <td className="px-4 py-3 text-slate2">{e.junctionId ?? '—'}</td>
                <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${sev(e.severity)}`}>{e.severity}</span></td>
                <td className="px-4 py-3 text-slate2">{e.message}</td>
              </tr>
            ))}
            {shown.length === 0 && <tr><td colSpan={5} className="px-4 py-6 text-center text-slate2">No events match this filter.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
