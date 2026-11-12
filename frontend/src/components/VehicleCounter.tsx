
import { Car, Bus, Bike, Truck, Ambulance } from 'lucide-react';
export default function VehicleCounter({ counts }: { counts: Record<string, number> }) {
  const items = [
    { label: 'Cars', n: counts.car ?? 0, Icon: Car },
    { label: 'Buses', n: counts.bus ?? 0, Icon: Bus },
    { label: 'Motorcycles', n: counts.motorcycle ?? 0, Icon: Bike },
    { label: 'Trucks', n: counts.truck ?? 0, Icon: Truck },
    { label: 'Ambulances', n: counts.ambulance ?? 0, Icon: Ambulance },
  ];
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
      {items.map(({ label, n, Icon }) => (
        <div key={label} className="rounded-lg bg-panel2 p-3 text-center">
          <Icon className="mx-auto h-5 w-5 text-teal" aria-hidden />
          <p className="mt-1 text-xl font-bold text-white">{n}</p>
          <p className="text-xs text-slate2">{label}</p>
        </div>
      ))}
    </div>
  );
}
