
import type { LucideIcon } from 'lucide-react';
export default function StatCard({ icon: Icon, label, value, sub, tone = 'teal' }: { icon: LucideIcon; label: string; value: string; sub?: string; tone?: 'teal' | 'cyan' | 'amber' | 'red' | 'green' }) {
  const tones: Record<string, string> = { teal: 'bg-teal/15 text-teal', cyan: 'bg-cyanx/15 text-cyanx', amber: 'bg-amberx/15 text-amberx', red: 'bg-danger/15 text-danger', green: 'bg-ok/15 text-ok' };
  return (
    <div className="rounded-xl border border-line bg-panel p-4 sm:p-5">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-slate2">{label}</p>
        <span className={`rounded-lg p-2 ${tones[tone]}`}><Icon className="h-4 w-4" aria-hidden /></span>
      </div>
      <p className="mt-2 text-2xl font-bold text-white sm:text-3xl">{value}</p>
      {sub && <p className="mt-1 text-xs text-slate2">{sub}</p>}
    </div>
  );
}
