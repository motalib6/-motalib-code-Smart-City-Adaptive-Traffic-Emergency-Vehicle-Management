"""YOLOv8 detector — lazy ultralytics import.

Pretrained COCO YOLOv8n has NO ambulance class. Vehicle classes used:
car, motorcycle, bus, truck (read from the model, never hardcoded as a
claim about ambulance detection). If ultralytics/OpenCV are absent, the
detector reports available=False and the API returns a clear 503-style
status instead of fake detections.
"""
from __future__ import annotations

from pathlib import Path

VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck"}


class Detector:
    def __init__(self, model_name: str = "yolov8n.pt") -> None:
        self.model_name = model_name
        self.model = None
        self.available = False
        self.error: str | None = None
        self._load()

    def _load(self) -> None:
        try:
            from ultralytics import YOLO  # noqa: F401  (lazy)
        except ImportError as e:
            self.error = f"ultralytics not installed: {e}"
            return
        try:
            from ultralytics import YOLO

            self.model = YOLO(self.model_name)  # downloads weights on first use
            self.available = True
        except Exception as e:  # noqa: BLE001 - report, don't crash backend
            self.error = str(e)

    def detect(self, frame) -> list[dict]:
        """Run detection on one OpenCV frame. Returns vehicle detections
        with class, confidence, bbox (fractions) and centre."""
        if not self.available or self.model is None:
            raise RuntimeError(f"detector unavailable: {self.error}")
        results = self.model(frame, verbose=False)[0]
        out: list[dict] = []
        names = results.names
        for box in results.boxes:
            cls = names[int(box.cls[0])]
            if cls not in VEHICLE_CLASSES:
                continue
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            h, w = frame.shape[:2]
            out.append({
                "class": cls,
                "confidence": round(float(box.conf[0]), 3),
                "bbox": [round(x1 / w, 3), round(y1 / h, 3), round(x2 / w, 3), round(y2 / h, 3)],
                "centre": [round((x1 + x2) / 2 / w, 3), round((y1 + y2) / 2 / h, 3)],
            })
        return out
