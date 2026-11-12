"""Database setup — SQLite + SQLModel.

DB file: backend/data/smartflow.db (SMARTFLOW_DATABASE_URL overrides).
Tables are created on startup (see app/main.py lifespan).
"""
import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.environ.get(
    "SMARTFLOW_DATABASE_URL", "sqlite:///./data/smartflow.db"
)

# Resolve a relative sqlite path against the backend/ directory.
if DATABASE_URL.startswith("sqlite:///./"):
    _base = Path(__file__).resolve().parent.parent
    DATABASE_URL = f"sqlite:///{_base / DATABASE_URL[len('sqlite:///./'):]}"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_db_and_tables() -> None:
    # Import models so SQLModel registers every table.
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
