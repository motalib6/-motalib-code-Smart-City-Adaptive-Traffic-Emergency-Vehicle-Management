
import { NavLink, useNavigate } from 'react-router-dom';
import { Activity, BarChart3, Camera, LayoutDashboard, LogOut, Map, Settings, Siren, SlidersHorizontal, TrafficCone, X } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const NAV = [
  { to: '/dashboard', label: 'Command Dashboard', Icon: LayoutDashboard },
  { to: '/live-network', label: 'Live Traffic Network', Icon: Map },
  { to: '/camera', label: 'AI Camera Monitoring', Icon: Camera },
  { to: '/junctions', label: 'Adaptive Junction Control', Icon: SlidersHorizontal },
  { to: '/emergency', label: 'Emergency Vehicles', Icon: Siren },
  { to: '/analytics', label: 'Analytics', Icon: BarChart3 },
  { to: '/events', label: 'Events', Icon: Activity },
  { to: '/admin', label: 'Administration', Icon: Settings },
];

export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const cls = ({ isActive }: { isActive: boolean }) =>
    `flex min-h-[44px] items-center gap-3 rounded-lg px-3 text-sm font-medium transition ${isActive ? 'bg-teal/15 text-teal' : 'text-slate2 hover:bg-panel2 hover:text-white'}`;
  return (
    <>
      {open && <button aria-label="Close menu" onClick={onClose} className="fixed inset-0 z-30 bg-black/60 lg:hidden" />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-line bg-panel transition-transform lg:static lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between border-b border-line px-4 py-4">
          <div className="flex items-center gap-2.5">
            <span className="rounded-lg bg-teal p-2 text-ink"><TrafficCone className="h-5 w-5" aria-hidden /></span>
            <div><p className="text-sm font-bold leading-tight text-white">SMARTFLOW</p><p className="text-[11px] font-semibold tracking-widest text-teal">ODISHA</p></div>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 text-slate2 hover:text-white lg:hidden" aria-label="Close sidebar"><X className="h-5 w-5" /></button>
        </div>
        <p className="px-4 pb-1 pt-4 text-[11px] font-semibold uppercase tracking-wider text-slate2">Smart City · Adaptive Traffic &amp; Emergency</p>
        <p className="px-4 text-[11px] text-slate2">GEC Hackathon 2026 · PS-03</p>
        <nav className="mt-4 flex-1 space-y-1 overflow-y-auto px-3 scrollbar-thin" aria-label="Main navigation">
          {NAV.map(({ to, label, Icon }) => (
            <NavLink key={to} to={to} className={cls} onClick={onClose}>
              <Icon className="h-5 w-5 shrink-0" aria-hidden /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-line p-4">
          <p className="text-sm font-medium text-white">{user?.username ?? 'Guest'}</p>
          <p className="text-xs capitalize text-slate2">{user?.role ?? 'not signed in'}</p>
          <button onClick={() => { logout(); navigate('/login'); }} className="mt-3 flex min-h-[44px] w-full items-center justify-center gap-2 rounded-lg border border-line px-3 text-sm font-medium text-slate2 hover:text-white">
            <LogOut className="h-4 w-4" aria-hidden /> Sign out
          </button>
        </div>
      </aside>
    </>
  );
}
