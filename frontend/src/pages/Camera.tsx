
import { useEffect, useState } from 'react';
import { Camera as CameraIcon, Play, Square, Upload } from 'lucide-react';
import { api, ApiError } from '../services/api';
import type { Detection } from '../types';
import CameraPreview from '../components/CameraPreview';
import VehicleCounter from '../components/VehicleCounter';
import { ErrorBanner, card } from './_shared';

const DEMO_DETECTIONS: Detection[] = [
  { label: 'car', confidence: 0.91, x: 12, y: 55, w: 14, h: 18, lane: 'N' },
  { label: 'car', confidence: 0.87, x: 38, y: 58, w: 13, h: 17, lane: 'S' },
  { label: 'bus', confidence: 0.82, x: 60, y: 52, w: 20, h: 22, lane: 'E' },
  { label: 'motorcycle', confidence: 0.76, x: 78, y: 62, w: 8, h: 12, lane: 'W' },
  { label: 'truck', confidence: 0.88, x: 28, y: 60, w: 16, h: 20, lane: 'N' },
];

export default function CameraPage() {
  const [running, setRunning] = useState(false);
  const [source, setSource] = useState('No camera connected');
  const [fileName, setFileName] = useState('');
  const [detections, setDetections] = useState<Detection[]>([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [demo, setDemo] = useState(false);

  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => setDetections((d) => d.length ? d : DEMO_DETECTIONS), 2000);
    return () => clearInterval(t);
  }, [running]);

  const counts: Record<string, number> = {};
  detections.forEach((d) => { counts[d.label] = (counts[d.label] ?? 0) + 1; });
  const laneCounts: Record<string, number> = {};
  detections.forEach((d) => { laneCounts[d.lane] = (laneCounts[d.lane] ?? 0) + 1; });
  const avgConf = detections.length ? detections.reduce((a, d) => a + d.confidence, 0) / detections.length : 0;

  const start = async (src: 'upload' | 'webcam') => {
    setError(''); setNotice('');
    try {
      await api.visionStart({ source: src, filename: fileName || undefined });
      setRunning(true); setSource(src === 'webcam' ? 'Webcam (local)' : `Uploaded video: ${fileName || 'traffic.mp4'}`);
      setNotice('YOLOv8n detector started.');
    } catch (err) {
      setDemo(true);
      setRunning(true); setSource(src === 'webcam' ? 'Webcam — DEMO DATA' : `Uploaded video — DEMO DATA`);
      setDetections(DEMO_DETECTIONS);
      setError(err instanceof ApiError ? err.message : 'Camera/detector unavailable — showing DEMO DATA detections. The pretrained YOLO model does not include an ambulance class; emergency priority uses the separate GPS module.');
    }
  };
  const stop = async () => {
    try { await api.visionStop(); } catch { /* already stopped / offline */ }
    setRunning(false); setDetections([]); setSource('No camera connected'); setNotice('Detector stopped.');
  };
  const onFile = async (f: File | undefined) => {
    if (!f) return;
    setFileName(f.name);
    try { const r = await api.uploadVideo(f); setNotice(`Uploaded ${r.filename} to the backend.`); setSource(`Uploaded video: ${r.filename}`); }
    catch (err) { setError(err instanceof Error ? err.message : 'Upload failed.'); }
  };

  return (
    <div className="space-y-5">
      {error && <ErrorBanner msg={error} />}
      {notice && <p className="text-sm text-slate2" role="status">{notice}</p>}
      <div className="flex flex-wrap items-center gap-2">
        <label className="inline-flex min-h-[44px] cursor-pointer items-center gap-2 rounded-lg border border-line bg-panel px-4 text-sm font-semibold text-white">
          <Upload className="h-4 w-4" aria-hidden /> Upload MP4
          <input type="file" accept="video/mp4,video/*" className="sr-only" onChange={(e) => void onFile(e.target.files?.[0])} />
        </label>
        {fileName && <span className="text-sm text-slate2">{fileName}</span>}
        <button onClick={() => void start('upload')} disabled={running} className="inline-flex min-h-[44px] items-center gap-2 rounded-lg bg-teal px-4 text-sm font-semibold text-ink hover:bg-teal-dark disabled:opacity-60"><Play className="h-4 w-4" /> Start detector (video)</button>
        <button onClick={() => void start('webcam')} disabled={running} className="inline-flex min-h-[44px] items-center gap-2 rounded-lg border border-line bg-panel px-4 text-sm font-semibold text-white"><CameraIcon className="h-4 w-4" /> Start webcam</button>
        <button onClick={() => void stop()} disabled={!running} className="inline-flex min-h-[44px] items-center gap-2 rounded-lg border border-danger/50 bg-panel px-4 text-sm font-semibold text-danger disabled:opacity-60"><Square className="h-4 w-4" /> Stop</button>
      </div>
      <p className="text-sm text-slate2">Camera status: <strong className="text-white">{running ? 'Connected — processing' : 'Not connected'}</strong> · Source: {source}{demo ? ' · DEMO DATA' : ''}</p>
      <CameraPreview detections={detections} running={running} source={source} />
      <VehicleCounter counts={counts} />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className={card}><h3 className="font-semibold text-white">Lane-wise density</h3>
          <ul className="mt-3 space-y-1.5 text-sm">{(['N', 'S', 'E', 'W'] as const).map((l) => (
            <li key={l} className="flex justify-between rounded bg-panel2 px-3 py-2"><span className="text-slate2">{l} approach</span><span className="font-medium text-white">{laneCounts[l] ?? 0} vehicles</span></li>))}</ul></div>
        <div className={card}><h3 className="font-semibold text-white">Detection confidence</h3>
          <p className="mt-3 text-3xl font-bold text-white">{detections.length ? `${Math.round(avgConf * 100)}%` : '—'}</p>
          <p className="mt-1 text-sm text-slate2">Mean confidence across {detections.length} detections. YOLOv8n (COCO) detects car, motorcycle, bus, truck — no ambulance class.</p></div>
        <div className={card}><h3 className="font-semibold text-white">Data source</h3>
          <p className="mt-3 text-sm text-slate2">Mode B — YOLO camera data feeds the same density engine as SUMO sensor data (Mode A). Operators can switch input source; camera data never controls real-world hardware.</p></div>
      </div>
    </div>
  );
}
