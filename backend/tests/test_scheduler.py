from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.reminder import Reminder
from app.models.reminder_automation import ReminderDelivery, ReminderPreference
from app.models.task import Task
from app.models.user import User
from app.services import reminder_scheduler


def make_user(db, email="scheduler@example.com"):
    user = User(
        email=email,
        password_hash="not-used-in-this-test",
        full_name="Scheduler Test",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_recurring_reminder_email_advances_next_occurrence(monkeypatch):
    monkeypatch.setattr(reminder_scheduler, "is_email_configured", lambda: True)
    monkeypatch.setattr(settings, "reminder_scheduler_enabled", True)

    sent = []
    monkeypatch.setattr(
        reminder_scheduler,
        "send_reminder_email",
        lambda **kwargs: sent.append(kwargs),
    )

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    due_at = now + timedelta(minutes=10)

    db = SessionLocal()
    try:
        user = make_user(db)
        db.add(
            ReminderPreference(
                user_id=user.id,
                enabled=True,
                email_enabled=True,
                minutes_before=30,
            )
        )
        reminder = Reminder(
            user_id=user.id,
            title="Study Python",
            due_at=due_at,
            timezone="Asia/Karachi",
            priority="high",
            status="pending",
            recurrence="daily",
        )
        db.add(reminder)
        db.commit()
        reminder_id = reminder.id
    finally:
        db.close()

    reminder_scheduler.run_reminder_job(now)

    db = SessionLocal()
    try:
        reminder = db.get(Reminder, reminder_id)
        delivery = db.scalar(
            select(ReminderDelivery).where(
                ReminderDelivery.reminder_id == reminder_id
            )
        )
        assert len(sent) == 1
        assert sent[0]["item_type"] == "reminder"
        assert delivery is not None
        assert delivery.status == "sent"
        assert reminder.due_at is not None
        assert reminder.due_at.astimezone(ZoneInfo("Asia/Karachi")).date() == (
            due_at.astimezone(ZoneInfo("Asia/Karachi")).date()
            + timedelta(days=1)
        )
    finally:
        db.close()


def test_task_delivery_is_not_sent_twice(monkeypatch):
    monkeypatch.setattr(reminder_scheduler, "is_email_configured", lambda: True)
    monkeypatch.setattr(settings, "reminder_scheduler_enabled", True)

    sent = []
    monkeypatch.setattr(
        reminder_scheduler,
        "send_reminder_email",
        lambda **kwargs: sent.append(kwargs),
    )

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    due_at = now + timedelta(minutes=5)

    db = SessionLocal()
    try:
        user = make_user(db, "task-scheduler@example.com")
        db.add(
            ReminderPreference(
                user_id=user.id,
                enabled=True,
                email_enabled=True,
                minutes_before=30,
            )
        )
        task = Task(
            user_id=user.id,
            title="Finish API tests",
            due_at=due_at,
            priority="high",
            status="pending",
        )
        db.add(task)
        db.commit()
    finally:
        db.close()

    reminder_scheduler.run_reminder_job(now)
    reminder_scheduler.run_reminder_job(now + timedelta(minutes=1))

    db = SessionLocal()
    try:
        deliveries = db.scalars(
            select(ReminderDelivery).where(
                ReminderDelivery.task_id == task.id
            )
        ).all()
        assert len(sent) == 1
        assert len(deliveries) == 1
        assert deliveries[0].status == "sent"
    finally:
        db.close()


def test_disabled_automation_does_not_send(monkeypatch):
    monkeypatch.setattr(reminder_scheduler, "is_email_configured", lambda: True)
    monkeypatch.setattr(settings, "reminder_scheduler_enabled", True)

    sent = []
    monkeypatch.setattr(
        reminder_scheduler,
        "send_reminder_email",
        lambda **kwargs: sent.append(kwargs),
    )

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    db = SessionLocal()
    try:
        user = make_user(db, "disabled-scheduler@example.com")
        db.add(
            ReminderPreference(
                user_id=user.id,
                enabled=False,
                email_enabled=True,
                minutes_before=30,
            )
        )
        db.add(
            Reminder(
                user_id=user.id,
                title="Do not notify",
                due_at=now + timedelta(minutes=5),
                timezone="UTC",
                priority="medium",
                status="pending",
                recurrence="none",
            )
        )
        db.commit()
    finally:
        db.close()

    reminder_scheduler.run_reminder_job(now)
    assert sent == []


def test_failed_email_is_retried_then_marked_sent(monkeypatch):
    monkeypatch.setattr(reminder_scheduler, "is_email_configured", lambda: True)
    monkeypatch.setattr(settings, "reminder_scheduler_enabled", True)

    calls = {"count": 0}

    def send_once_fails(**kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("Temporary SMTP failure")

    monkeypatch.setattr(reminder_scheduler, "send_reminder_email", send_once_fails)

    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    db = SessionLocal()
    try:
        user = make_user(db, "retry-scheduler@example.com")
        db.add(
            ReminderPreference(
                user_id=user.id,
                enabled=True,
                email_enabled=True,
                minutes_before=30,
            )
        )
        reminder = Reminder(
            user_id=user.id,
            title="Retry me",
            due_at=now + timedelta(minutes=5),
            timezone="UTC",
            priority="medium",
            status="pending",
            recurrence="none",
        )
        db.add(reminder)
        db.commit()
        reminder_id = reminder.id
    finally:
        db.close()

    reminder_scheduler.run_reminder_job(now)
    reminder_scheduler.run_reminder_job(now + timedelta(minutes=1))

    db = SessionLocal()
    try:
        delivery = db.scalar(
            select(ReminderDelivery).where(
                ReminderDelivery.reminder_id == reminder_id
            )
        )
        assert delivery.status == "sent"
        assert delivery.attempts == 2
        assert delivery.last_error is None
    finally:
        db.close()


def test_monthly_recurrence_clamps_to_last_day_of_month():
    due_at = datetime(2026, 1, 31, 9, 0, tzinfo=timezone.utc)
    next_due = reminder_scheduler.next_occurrence(
        due_at,
        "monthly",
        "UTC",
    )
    assert next_due.date().isoformat() == "2026-02-28"
    assert next_due.hour == 9
