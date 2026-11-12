"""Analytics API: GET /api/analytics/summary, GET /api/analytics/comparison."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.permissions import get_current_user
from app.database import get_session
from app.models import User
from app.services.analytics_service import fixed_vs_adaptive, summary as analytics_summary

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def analytics(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return analytics_summary(session)


@router.get("/comparison")
def comparison(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return fixed_vs_adaptive(session)
