
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { DensityPoint } from '../types';
export default function AnalyticsChart({ data, title }: { data: DensityPoint[]; title: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel p-4 sm:p-5">
      <h3 className="text-base font-semibold text-white">{title}</h3>
      <div className="mt-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#1E2C47" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#94A3B8" fontSize={12} />
            <YAxis stroke="#94A3B8" fontSize={12} />
            <Tooltip contentStyle={{ background: '#16223A', border: '1px solid #1E2C47', borderRadius: 8, color: '#F1F5F9' }} />
            <Legend />
            <Line type="monotone" dataKey="vehicles" stroke="#15C6B3" strokeWidth={2} dot={false} name="Vehicles" />
            <Line type="monotone" dataKey="avgWait" stroke="#38BDF8" strokeWidth={2} dot={false} name="Avg wait (s)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
