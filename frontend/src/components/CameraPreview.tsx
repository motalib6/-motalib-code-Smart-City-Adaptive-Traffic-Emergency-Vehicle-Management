
import type { Detection } from '../types';
const COLORS: Record<string, string> = { car: '#38BDF8', bus: '#FBBF24', motorcycle: '#A78BFA', truck: '#94A3B8' };
export default function CameraPreview({ detections, running, source }: { detections: Detection[]; running: boolean; source: string }) {
  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-xl border border-line bg-black" role="img" aria-label={`Camera preview, ${detections.length} vehicles detected`}>
      <div className="absolute inset-0 bg-[linear-gradient(180deg,#16223A,#0B1220)]" />
      <div className="absolute inset-x-0 bottom-0 h-16 bg-slate-800/60" />
      <p className="absolute left-3 top-3 rounded bg-black/60 px-2 py-1 text-xs text-white">{source} · {running ? 'LIVE — YOLOv8n' : 'Detector stopped'}</p>
      <p className="absolute right-3 top-3 rounded bg-black/60 px-2 py-1 text-xs text-white">{detections.length} detections</p>
      {detections.map((d, i) => (
        <div key={i} className="absolute rounded-sm border-2" style={{ left: `${d.x}%`, top: `${d.y}%`, width: `${d.w}%`, height: `${d.h}%`, borderColor: COLORS[d.label] ?? '#38BDF8' }}>
          <span className="absolute -top-5 left-0 whitespace-nowrap rounded px-1 py-0.5 text-[10px] font-semibold text-white" style={{ background: COLORS[d.label] ?? '#38BDF8' }}>
            {d.label} {Math.round(d.confidence * 100)}% · {d.lane}
          </span>
        </div>
      ))}
      {!running && <p className="absolute inset-0 flex items-center justify-center text-sm text-slate2">Upload an MP4 or start the webcam to begin detection.</p>}
    </div>
  );
}
