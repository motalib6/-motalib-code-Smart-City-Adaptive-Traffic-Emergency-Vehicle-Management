"""Seed the initial admin user.

Run:  python -m app.seed   (from backend/)
Default: admin@smartflow.local / ChangeMe123!  (override with
SMARTFLOW_ADMIN_EMAIL / SMARTFLOW_ADMIN_PASSWORD env vars).
Change the password after first login. Never hardcode a production password.
"""
from __future__ import annotations

from sqlmodel import Session, select

from app.config import settings
from app.core.security import hash_password
from app.database import create_db_and_tables, engine
from app.models import User


def seed_admin() -> User | None:
    create_db_and_tables()
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == settings.admin_email)).first()
        if existing:
            print(f"Admin already exists: {settings.admin_email}")
            return existing
        user = User(
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            role="ADMIN",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"Seeded admin: {settings.admin_email} (change the password after first login)")
        return user


if __name__ == "__main__":
    seed_admin()
