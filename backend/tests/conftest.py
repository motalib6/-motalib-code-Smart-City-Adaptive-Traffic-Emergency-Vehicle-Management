"""Test fixtures: isolated temp SQLite DB + TestClient (lifespan runs)."""
import os
import tempfile

import pytest

DB_PATH = os.path.join(tempfile.gettempdir(), "test_smartflow.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
os.environ["SMARTFLOW_DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["SMARTFLOW_JWT_SECRET"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post("/api/auth/login", json={"email": "admin@smartflow.local", "password": "ChangeMe123!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def viewer_token(client):
    # Create a VIEWER user directly via the seeded admin + DB.
    from sqlmodel import Session, select

    from app.core.security import hash_password
    from app.database import engine
    from app.models import User

    with Session(engine) as s:
        if not s.exec(select(User).where(User.email == "viewer@test.local")).first():
            s.add(User(email="viewer@test.local", password_hash=hash_password("Viewer123!"), role="VIEWER"))
            s.commit()
    r = client.post("/api/auth/login", json={"email": "viewer@test.local", "password": "Viewer123!"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
