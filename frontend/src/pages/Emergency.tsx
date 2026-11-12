
import { useEffect, useState, type FormEvent } from 'react';
import { Ambulance, CheckCircle2, Plus } from 'lucide-react';
import { api, ApiError } from '../services/api';
import { demoEmergency } from '../data/demo';
import type { Emergency as EmergencyT } from '../types';
import EmergencyStatus from '../components/EmergencyStatus';
import { DemoBanner, ErrorBanner, card } from './_shared';

const TIMELINE = [
  { label: 'EMERGENCY_REQUESTED', done: true }, { label: 'ROUTE_VALIDATED', done: true },
  { label: 'YELLOW_STARTED', done: true }, { label: 'ALL_RED_STARTED', done: true },
  { label: 'PRIORITY_GRANTED', done: true }, { label: 'NEXT_JUNCTION_PREPARED (J2)', done: true },
  { label: 'AMBULANCE_PASSED', done: false }, { label: 'PRIORITY_RELEASED', done: false },
  { label: 'EMERGENCY_COMPLETED', done: false },
];

export default function EmergencyPage() {
  const [active, setActive] = useState<EmergencyT | null>(demoEmergency);
  const [demo, setDemo] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [ambId, setAmbId] = useState('AMB-02');
  const [from, setFrom] = useState('J1');
  const [to, setTo] = useState('J4');

  useEffect(() => {
    const load = async () => {
      try { const list = await api.emergencies(); if (list.length) { setActive(list[0]); setDemo(false); } }
      catch { setDemo(true); }
    };
    void load();
  }, []);

  const create = async (e: FormEvent) => {
    e.preventDefault(); setError(''); setNotice('');
    const route = from === 'J1' && to === 'J4' ? ['J1', 'J2', 'J4'] : from === 'J1' && to === 'J2' ? ['J1', 'J2'] : [from, to];
    try {
      const em = await api.createEmergency({ ambulanceId: ambId, fromJunction: from, toJunction: to, route });
      setActive(em); setDemo(false); setNotice(`Emergency ${em.id} created — route validated, priority will be granted only after safe yellow + all-red clearance.`);
    } catch (err) {
      setDemo(true);
      setActive({ id: 'EMG-DEMO', ambulanceId: ambId, fromJunction: from, toJunction: to, route, status: 'requested', etaSec: 120, progressPct: 0, currentJunction: from, nextJunction: route[1] ?? to, speedKmh: 0 });
      setError(err instanceof ApiError ? `${err.message} — showing DEMO DATA request instead.` : 'Backend unavailable — showing DEMO DATA request.');
    }
  };
  const complete = async () => {
    if (!active) return;
    try { const em = await api.completeEmergency(active.id); setActive(em); setNotice('Emergency completed — priority released, adaptive control resumed.'); }
    catch { setActive({ ...active, status: 'completed' }); setNotice('Emergency marked complete locally (backend unreachable).'); }
  };

  return (
    <div className="space-y-5">
      {demo && <DemoBanner />}
      {error && <ErrorBanner msg={error} />}
      {notice && <p className="text-sm text-slate2" role="status">{notice}</p>}
      <p className="text-sm text-slate2">GPS positions are <strong className="text-white">SIMULATED GPS</strong> along SUMO routes — never claimed as a live ambulance feed. Priority is granted only after the current green is safely terminated (yellow → all-red).</p>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <form onSubmit={create} className={card} aria-label="Create emergency request">
          <h2 className="flex items-center gap-2 text-lg font-bold text-white"><Ambulance className="h-5 w-5 text-danger" /> Create emergency request</h2>
          <label className="mb-1 mt-4 block text-sm font-medium text-white" htmlFor="amb">Ambulance ID</label>
          <input id="amb" value={ambId} onChange={(e) => setAmbId(e.target.value)} required className="min-h-[44px] w-full rounded-lg border border-line bg-panel2 px-3 text-white" />
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div><label className="mb-1 block text-sm font-medium text-white" htmlFor="from">From junction</label>
              <select id="from" value={from} onChange={(e) => setFrom(e.target.value)} className="min-h-[44px] w-full rounded-lg border border-line bg-panel2 px-3 text-white">
                {['J1', 'J2', 'J3', 'J4'].map((j) => <option key={j} value={j}>{j}</option>)}
              </select></div>
            <div><label className="mb-1 block text-sm font-medium text-white" htmlFor="to">Destination</label>
              <select id="to" value={to} onChange={(e) => setTo(e.target.value)} className="min-h-[44px] w-full rounded-lg border border-line bg-panel2 px-3 text-white">
                {['J1', 'J2', 'J3', 'J4'].map((j) => <option key={j} value={j}>{j}</option>)}
              </select></div>
          </div>
          <p className="mt-3 text-xs text-slate2">Route is validated against the connected network (J1 → J2 → J4). Invalid routes are rejected; conflicting requests are queued and arbitrated.</p>
          <button type="submit" className="mt-4 inline-flex min-h-[48px] items-center gap-2 rounded-lg bg-danger px-5 font-semibold text-white hover:opacity-90"><Plus className="h-4 w-4" /> Request priority</button>
        </form>
        <div className="space-y-4">
          {active ? <EmergencyStatus e={active} /> : <div className={card}><p className="text-slate2">No active emergency.</p></div>}
          {active && active.status !== 'completed' && (
            <button onClick={() => void complete()} className="inline-flex min-h-[48px] items-center gap-2 rounded-lg border border-line bg-panel px-5 font-semibold text-white"><CheckCircle2 className="h-4 w-4" /> Mark emergency complete</button>
          )}
        </div>
      </div>
      <div className={card}>
        <h3 className="font-semibold text-white">Emergency event timeline</h3>
        <ol className="mt-3 space-y-2">
          {TIMELINE.map((t) => (
            <li key={t.label} className="flex items-center gap-3 rounded-lg bg-panel2 px-3 py-2.5 text-sm">
              <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${t.done ? 'bg-teal text-ink' : 'bg-line text-slate2'}`}>{t.done ? '✓' : '·'}</span>
              <span className={t.done ? 'text-white' : 'text-slate2'}>{t.label}</span>
            </li>
          ))}
        </ol>
        <p className="mt-3 text-xs text-slate2">Predictive coordination: when the ambulance approaches J2, the system computes ETA, sends a prepare event to J2, and selects an emergency-compatible safe phase — never a conflicting green.</p>
      </div>
    </div>
  );
}
