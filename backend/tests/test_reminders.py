
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.main import app
from app.models.reminder import Reminder
from app.models.refresh_token import RefreshToken
from app.models.user import User


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def registered_user(client):
    email = f"reminder-{uuid.uuid4().hex}@example.com"
    password = "Strong-Test-Password-123!"

    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Reminder Test User",
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    access_token = login.json()["access_token"]

    yield {
        "email": email,
        "headers": {"Authorization": f"Bearer {access_token}"},
    }

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            db.execute(
                delete(Reminder).where(Reminder.user_id == user.id)
            )
            db.execute(
                delete(RefreshToken).where(
                    RefreshToken.user_id == user.id
                )
            )
            db.delete(user)
            db.commit()
    finally:
        db.close()


def test_create_reminder_and_save_to_database(client, registered_user):
    payload = {
        "title": "Study Python",
        "description": "Practice FastAPI",
        "timezone": "Asia/Karachi",
        "priority": "high",
        "recurrence": "none",
    }

    response = client.post(
        "/api/v1/reminders",
        json=payload,
        headers=registered_user["headers"],
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Study Python"
    assert data["priority"] == "high"
    assert data["timezone"] == "Asia/Karachi"
    assert data["status"] == "pending"

    db = SessionLocal()
    try:
        saved = db.get(Reminder, data["id"])
        assert saved is not None
        assert saved.title == "Study Python"
    finally:
        db.close()


def test_create_reminder_rejects_empty_title(client, registered_user):
    response = client.post(
        "/api/v1/reminders",
        json={
            "title": "   ",
            "timezone": "Asia/Karachi",
        },
        headers=registered_user["headers"],
    )

    assert response.status_code == 422


def test_create_reminder_rejects_invalid_timezone(
    client, registered_user
):
    response = client.post(
        "/api/v1/reminders",
        json={
            "title": "Study Python",
            "timezone": "Invalid/Not_A_Timezone",
        },
        headers=registered_user["headers"],
    )

    assert response.status_code == 422


def test_list_reminders_requires_authentication(client):
    response = client.get("/api/v1/reminders")

    assert response.status_code == 401


def test_create_reminder_rejects_timezone_naive_due_date(
    client, registered_user
):
    response = client.post(
        "/api/v1/reminders",
        json={
            "title": "Study Python",
            "due_at": "2026-10-23T09:00:00",
            "timezone": "Asia/Karachi",
        },
        headers=registered_user["headers"],
    )

    assert response.status_code == 422


def test_recurring_reminder_requires_due_date(client, registered_user):
    response = client.post(
        "/api/v1/reminders",
        headers=registered_user["headers"],
        json={
            "title": "Daily study",
            "timezone": "Asia/Karachi",
            "recurrence": "daily",
        },
    )
    assert response.status_code == 422


def test_user_cannot_read_another_users_reminder(client, registered_user):
    reminder_response = client.post(
        "/api/v1/reminders",
        headers=registered_user["headers"],
        json={"title": "Private reminder"},
    )
    assert reminder_response.status_code == 201
    reminder_id = reminder_response.json()["id"]

    other_email = f"other-{uuid.uuid4().hex}@example.com"
    register = client.post(
        "/api/v1/auth/register",
        json={"email": other_email, "password": "Strong-Test-Password-123!"},
    )
    assert register.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": other_email, "password": "Strong-Test-Password-123!"},
    )
    assert login.status_code == 200
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.get(
        f"/api/v1/reminders/{reminder_id}",
        headers=other_headers,
    )
    assert response.status_code == 404


def test_ai_reminder_parse_reports_missing_configuration(client, registered_user):
    response = client.post(
        "/api/v1/reminders/parse",
        headers=registered_user["headers"],
        json={
            "text": "Remind me tomorrow at 9 to study",
            "timezone": "Asia/Karachi",
        },
    )
    assert response.status_code == 503
