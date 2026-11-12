
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { demoEvents } from '../data/demo';
import type { AppEvent } from '../types';
import EventTable from '../components/EventTable';
import { DemoBanner, ErrorBanner } from './_shared';

export default function Events() {
  const [events, setEvents] = useState<AppEvent[]>(demoEvents);
  const [filter, setFilter] = useState('all');
  const [demo, setDemo] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    (async () => {
      try { const e = await api.events('?limit=100'); setEvents(e); setDemo(false); }
      catch (err) { setDemo(true); setError(err instanceof Error ? err.message : 'Backend unavailable.'); }
    })();
  }, []);
  return (
    <div className="space-y-5">
      {demo && <DemoBanner />}
      {error && <ErrorBanner msg={error} />}
      <p className="text-sm text-slate2">All signal transitions, emergency events and safety blocks are persisted to SQLite with timestamps and source — history survives backend restarts.</p>
      <EventTable events={events} filter={filter} onFilter={setFilter} />
    </div>
  );
}
