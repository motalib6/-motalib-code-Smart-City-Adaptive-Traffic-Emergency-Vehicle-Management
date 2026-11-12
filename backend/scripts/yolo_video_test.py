"""YOLO verification on a REAL traffic video (not via the HTTP thread).

Directly runs the codebase Detector (YOLOv8n, COCO classes car/motorcycle/
bus/truck) over sampled frames of backend/data/uploads/<video>, aggregates
class counts + lane-wise counts (app/vision/lane_roi.py), draws boxes on the
first frame with >=1 detection, and writes:
  - screenshots/yolo-detection-summary.json
  - screenshots/yolo-detection-frame.jpg  (real detection output, labelled)
Usage: .venv/bin/python scripts/yolo_video_test.py <video-path> [max_frames] [stride]
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

VIDEO = sys.argv[1] if len(sys.argv) > 1 else "data/uploads/traffic-intersection-pexels-1393755.mp4"
MAX_FRAMES = int(sys.argv[2]) if len(sys.argv) > 2 else 20
STRIDE = int(sys.argv[3]) if len(sys.argv) > 3 else 15


def main() -> int:
    import cv2

    from app.vision.detector import Detector
    from app.vision.lane_roi import approach_for_point

    root = Path(__file__).resolve().parent.parent
    video = root / VIDEO if not Path(VIDEO).is_absolute() else Path(VIDEO)
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        print("FAIL: could not open video", video)
        return 1
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"video: {video.name} {w}x{h} {fps:.1f}fps frames={n_frames}")

    det = Detector()
    print("detector available:", det.available, "error:", det.error)
    if not det.available:
        return 2

    class_counts: Counter = Counter()
    lane_counts: dict[str, Counter] = {}
    confidences: list[float] = []
    frames_done = 0
    annotated_path = root / "screenshots" / "yolo-detection-frame.jpg"
    annotated_saved = False
    idx = 0
    while frames_done < MAX_FRAMES:
        ok, frame = cap.read()
        if not ok:
            break
        idx += 1
        if (idx - 1) % STRIDE != 0:
            continue
        dets = det.detect(frame)
        frames_done += 1
        for d in dets:
            class_counts[d["class"]] += 1
            confidences.append(d["confidence"])
            app = approach_for_point(*d["centre"]) or "unknown"
            lane_counts.setdefault(app, Counter())[d["class"]] += 1
        if dets and not annotated_saved:
            for d in dets:
                x1, y1, x2, y2 = [int(v) for v in (
                    d["bbox"][0] * w, d["bbox"][1] * h, d["bbox"][2] * w, d["bbox"][3] * h)]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(frame, f"{d['class']} {d['confidence']:.2f}",
                            (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 255, 255), 1)
            cv2.putText(frame, "REAL YOLOv8n detection - SMARTFLOW ODISHA (Pexels traffic video)",
                        (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            annotated_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(annotated_path), frame)
            annotated_saved = True
    cap.release()

    summary = {
        "video": str(video),
        "source_url": "https://www.pexels.com/video/traffic-at-urban-intersection-on-sunny-day-34494565/",
        "source_file": "https://videos.pexels.com/video-files/1393755/1393755-sd_640_360_30fps.mp4",
        "licence": "Pexels free to use",
        "model": "yolov8n.pt (COCO; vehicle classes car/motorcycle/bus/truck only — no ambulance class)",
        "frames_in_video": n_frames,
        "frames_sampled": frames_done,
        "sample_stride": STRIDE,
        "total_detections": sum(class_counts.values()),
        "class_counts": dict(class_counts),
        "lane_counts": {k: dict(v) for k, v in lane_counts.items()},
        "mean_confidence": round(sum(confidences) / len(confidences), 3) if confidences else None,
        "annotated_frame": str(annotated_path) if annotated_saved else None,
        "note": "Counts are summed over sampled frames (a vehicle may be counted in more than one sampled frame); they prove detection works, not a unique-vehicle census.",
    }
    out = root / "screenshots" / "yolo-detection-summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    if sum(class_counts.values()) == 0:
        print("WARN: zero detections in sampled frames")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
