"""Video manager — local MP4 / webcam handling for the vision module.

Video stays local by default; nothing is sent to a cloud service.
If OpenCV is absent, status reports unavailable with the exact reason.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from app.vision.detector import Detector
from app.vision.lane_roi import approach_for_point


class VideoManager:
    def __init__(self, upload_dir: Path) -> None:
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.cap = None
        self.running = False
        self.source: str | None = None
        self.filename: str | None = None
        self.detector = Detector()
        self.last_counts: dict[str, Any] = {}
        self.last_frame_detections: list[dict] = []
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    @property
    def available(self) -> bool:
        try:
            import cv2  # noqa: F401
            return True
        except ImportError:
            return False

    def status(self) -> dict:
        return {
            "available": self.available,
            "detector_available": self.detector.available,
            "detector_error": self.detector.error,
            "running": self.running,
            "source": self.source,
            "filename": self.filename,
            "last_counts": self.last_counts,
        }

    def start_file(self, path: str | Path) -> dict:
        if not self.available:
            raise RuntimeError("opencv-python is not installed — vision unavailable")
        import cv2

        self.stop()
        self.cap = cv2.VideoCapture(str(path))
        if not self.cap.isOpened():
            raise RuntimeError(f"could not open video: {path}")
        self.source, self.filename = "file", Path(path).name
        self.running = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self.status()

    def start_webcam(self, index: int = 0) -> dict:
        if not self.available:
            raise RuntimeError("opencv-python is not installed — vision unavailable")
        import cv2

        self.stop()
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise RuntimeError("could not open webcam")
        self.source, self.filename = "webcam", None
        self.running = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self.status()

    def stop(self) -> dict:
        self._stop.set()
        self.running = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        return self.status()

    def _loop(self) -> None:
        import cv2

        while not self._stop.is_set() and self.cap is not None:
            ok, frame = self.cap.read()
            if not ok:
                break
            if self.detector.available:
                try:
                    detections = self.detector.detect(frame)
                except Exception:
                    detections = []
                self.last_frame_detections = detections
                counts: dict[str, dict[str, int]] = {}
                for d in detections:
                    app = approach_for_point(*d["centre"]) or "unknown"
                    counts.setdefault(app, {}).setdefault(d["class"], 0)
                    counts[app][d["class"]] += 1
                self.last_counts = counts
            # ~10 fps processing cap
            self._stop.wait(0.1)
        self.running = False
