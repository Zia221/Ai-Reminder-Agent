from datetime import datetime, timezone

from app.core.config import settings
from app.services import email_service


def test_email_service_formats_and_sends_message(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            captured["connection"] = (host, port, timeout)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def starttls(self):
            captured["starttls"] = True

        def login(self, username, password):
            captured["login"] = (username, password)

        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_username", "sender@example.com")
    monkeypatch.setattr(settings, "smtp_password", "app-password")
    monkeypatch.setattr(settings, "smtp_from", "sender@example.com")

    email_service.send_reminder_email(
        recipient="recipient@example.com",
        task_title="Study Python",
        due_at=datetime(2026, 10, 29, 9, 0, tzinfo=timezone.utc),
        timezone_name="Asia/Karachi",
        item_type="reminder",
    )

    assert captured["connection"] == ("smtp.example.com", 587, 20)
    assert captured["starttls"] is True
    assert captured["login"] == ("sender@example.com", "app-password")
    message = captured["message"]
    assert message["To"] == "recipient@example.com"
    assert "Reminder" in message["Subject"]
    assert "Study Python" in message.get_content()
