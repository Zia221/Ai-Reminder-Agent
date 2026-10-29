import smtplib
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from app.core.config import settings


def is_email_configured() -> bool:
    return settings.smtp_configured


def send_reminder_email(
    recipient: str,
    task_title: str,
    due_at: datetime | str,
    timezone_name: str = "UTC",
    item_type: str = "task",
) -> None:
    if not settings.smtp_username or not settings.smtp_password:
        raise RuntimeError(
            "Email notifications are not configured. Set SMTP_USERNAME and SMTP_PASSWORD."
        )

    if isinstance(due_at, str):
        due_value = datetime.fromisoformat(due_at)
    else:
        due_value = due_at

    try:
        zone = ZoneInfo(timezone_name)
    except Exception:
        zone = ZoneInfo("UTC")

    if due_value.tzinfo is None:
        due_value = due_value.replace(tzinfo=ZoneInfo("UTC"))

    due_display = due_value.astimezone(zone).strftime("%A, %B %d, %Y at %I:%M %p %Z")
    item_label = "reminder" if item_type == "reminder" else "task"

    message = EmailMessage()
    message["Subject"] = "AI Reminder Agent: " + " ".join(task_title.split())
    message["From"] = settings.smtp_from or settings.smtp_username
    message["To"] = recipient
    message.set_content(
        f"""Hello!

This is your scheduled {item_label} notification from AI Reminder Agent.

{task_title}

Scheduled for:
{due_display}

Open your AI Reminder Agent workspace to review it.

Have a productive day!
"""
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)
