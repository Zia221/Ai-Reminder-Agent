import os
import uuid

# API tests use an isolated in-memory SQLite database and never touch a developer's
# PostgreSQL database. These defaults are set before importing the app/settings.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-only-secret-key-that-is-long-enough"
os.environ["REMINDER_SCHEDULER_ENABLED"] = "false"
os.environ["OPENAI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

import app.models  # noqa: F401 - registers every model on Base.metadata
from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    email = f"testuser-{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 201, response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
