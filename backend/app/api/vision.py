"""Vision API: upload / start / stop / stream / status.

YOLO is optional: without ultralytics/OpenCV the endpoints report
available=False with the exact reason instead of fake detections.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.core.permissions import get_current_user, require_role
from app.database import get_session
from app.models import User
from app.state import STATE
from app.vision.video_manager import VideoManager

router = APIRouter(prefix="/api/vision", tags=["vision"])
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"

_manager: VideoManager | None = None


def manager() -> VideoManager:
    global _manager
    if _manager is None:
        _manager = VideoManager(UPLOAD_DIR)
    return _manager


@router.get("/status")
def status(user: User = Depends(get_current_user)):
    return manager().status()


@router.post("/upload", status_code=201)
async def upload(
    file: UploadFile = File(...),
    user: User = Depends(require_role("ADMIN", "OPERATOR")),
):
    if not file.filename or not file.filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        raise HTTPException(status_code=422, detail="upload a local MP4/AVI/MOV video file")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / file.filename
    dest.write_bytes(await file.read())
    STATE.vision.update({"filename": file.filename, "source": "file", "status": "uploaded"})
    return {"status": "uploaded", "filename": file.filename, "path": str(dest),
            "note": "Video stays local; nothing is sent to a cloud service."}


@router.post("/start")
def start(
    body: dict | None = None,
    user: User = Depends(require_role("ADMIN", "OPERATOR")),
):
    body = body or {}
    vm = manager()
    if not vm.available:
        raise HTTPException(status_code=503, detail="opencv-python not installed — vision unavailable")
    try:
        if body.get("source") == "webcam":
            result = vm.start_webcam(int(body.get("index", 0)))
        else:
            filename = body.get("filename") or STATE.vision.get("filename")
            if not filename:
                raise HTTPException(status_code=422, detail="no video uploaded; upload an MP4 first")
            result = vm.start_file(UPLOAD_DIR / filename)
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    STATE.vision.update({"status": "running", "source": result["source"]})
    return result


@router.post("/stop")
def stop(user: User = Depends(require_role("ADMIN", "OPERATOR"))):
    result = manager().stop()
    STATE.vision.update({"status": "stopped"})
    return result


@router.get("/stream")
def stream(user: User = Depends(get_current_user)):
    """Detection preview. No MJPEG stream exists without a running video +
    detector, so this returns the live status (counts + availability)
    instead of a fake video feed."""
    vm = manager()
    st = vm.status()
    if not st["running"]:
        return {"stream": "unavailable", "reason": "no video processing running", **st}
    return {"stream": "status-only",
            "note": "MJPEG preview not implemented in this build; use /api/vision/status for live counts.",
            "detections": vm.last_frame_detections, **st}
