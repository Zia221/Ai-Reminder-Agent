
def test_automation_preferences_require_auth(client):
    response = client.get(
        "/api/v1/reminders/automation/preferences"
    )

    assert response.status_code == 401


def test_automation_history_requires_auth(client):
    response = client.get(
        "/api/v1/reminders/automation/history"
    )

    assert response.status_code == 401


def test_get_automation_preferences(client, auth_headers):
    response = client.get(
        "/api/v1/reminders/automation/preferences",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["enabled"] is True
    assert data["email_enabled"] is False
    assert data["minutes_before"] == 30


def test_update_automation_preferences(client, auth_headers):
    response = client.put(
        "/api/v1/reminders/automation/preferences",
        headers=auth_headers,
        json={
            "enabled": True,
            "email_enabled": False,
            "minutes_before": 60,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["enabled"] is True
    assert data["email_enabled"] is False
    assert data["minutes_before"] == 60


def test_automation_rejects_invalid_minutes(client, auth_headers):
    response = client.put(
        "/api/v1/reminders/automation/preferences",
        headers=auth_headers,
        json={
            "enabled": True,
            "email_enabled": True,
            "minutes_before": 2,
        },
    )

    assert response.status_code == 422


def test_automation_history_returns_list(client, auth_headers):
    response = client.get(
        "/api/v1/reminders/automation/history",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_enable_email_requires_smtp_configuration(client, auth_headers):
    response = client.put(
        "/api/v1/reminders/automation/preferences",
        headers=auth_headers,
        json={
            "enabled": True,
            "email_enabled": True,
            "minutes_before": 30,
        },
    )

    assert response.status_code == 503
    assert "SMTP_USERNAME" in response.json()["detail"]


def test_failed_delivery_can_be_manually_retried(client, auth_headers, monkeypatch):
    from datetime import datetime
    from sqlalchemy import select
    from app.core.config import settings
    from app.db.session import SessionLocal
    from app.models.reminder_automation import ReminderDelivery
    from app.models.user import User

    monkeypatch.setattr(settings, "smtp_username", "sender@example.com")
    monkeypatch.setattr(settings, "smtp_password", "test-app-password")

    profile = client.get("/api/v1/users/me", headers=auth_headers)
    assert profile.status_code == 200
    user_id = profile.json()["id"]

    task_response = client.post(
        "/api/v1/tasks",
        headers=auth_headers,
        json={
            "title": "Retry notification",
            "due_at": "2026-10-29T09:00:00+00:00",
        },
    )
    assert task_response.status_code == 201
    task = task_response.json()
    due_at = datetime.fromisoformat(task["due_at"])

    db = SessionLocal()
    try:
        delivery = ReminderDelivery(
            user_id=user_id,
            task_id=task["id"],
            reminder_id=None,
            task_due_at=due_at,
            reminder_due_at=None,
            item_title=task["title"],
            recipient_email=profile.json()["email"],
            status="failed",
            attempts=3,
            last_error="Temporary SMTP error",
        )
        db.add(delivery)
        db.commit()
        delivery_id = delivery.id
    finally:
        db.close()

    response = client.post(
        f"/api/v1/reminders/automation/history/{delivery_id}/retry",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["attempts"] == 0
    assert response.json()["last_error"] is None
