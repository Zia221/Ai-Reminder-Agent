from calendar import monthrange
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.reminder import Reminder
from app.models.reminder_automation import ReminderDelivery, ReminderPreference
from app.models.task import Task
from app.models.user import User
from app.services.email_service import is_email_configured, send_reminder_email


MAX_ATTEMPTS = 3
MISSED_REMINDER_GRACE = timedelta(hours=24)
STALE_SENDING_AFTER = timedelta(minutes=10)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def next_occurrence(
    due_at: datetime,
    recurrence: str,
    timezone_name: str,
) -> datetime:
    """Advance a recurring reminder while preserving its local wall-clock time."""
    zone = ZoneInfo(timezone_name)
    local_due = _as_utc(due_at).astimezone(zone)

    if recurrence == "daily":
        next_day = local_due.date() + timedelta(days=1)
        return datetime.combine(next_day, local_due.timetz().replace(tzinfo=None), tzinfo=zone)
    if recurrence == "weekly":
        next_day = local_due.date() + timedelta(days=7)
        return datetime.combine(next_day, local_due.timetz().replace(tzinfo=None), tzinfo=zone)
    if recurrence == "monthly":
        year = local_due.year + (1 if local_due.month == 12 else 0)
        month = 1 if local_due.month == 12 else local_due.month + 1
        day = min(local_due.day, monthrange(year, month)[1])
        next_day = local_due.date().replace(year=year, month=month, day=day)
        return datetime.combine(next_day, local_due.timetz().replace(tzinfo=None), tzinfo=zone)

    return due_at


def _preference_for(db, user_id: int) -> ReminderPreference | None:
    return db.scalar(
        select(ReminderPreference).where(
            ReminderPreference.user_id == user_id,
        )
    )


def _delivery_exists(
    db,
    *,
    task_id: int | None = None,
    task_due_at: datetime | None = None,
    reminder_id: int | None = None,
    reminder_due_at: datetime | None = None,
) -> bool:
    if task_id is not None:
        return db.scalar(
            select(ReminderDelivery.id).where(
                ReminderDelivery.task_id == task_id,
                ReminderDelivery.task_due_at == task_due_at,
            )
        ) is not None

    return db.scalar(
        select(ReminderDelivery.id).where(
            ReminderDelivery.reminder_id == reminder_id,
            ReminderDelivery.reminder_due_at == reminder_due_at,
        )
    ) is not None


def _create_due_deliveries(db, now: datetime) -> None:
    if not is_email_configured():
        return

    users = db.scalars(
        select(User).where(User.is_active.is_(True))
    ).all()

    for user in users:
        preference = _preference_for(db, user.id)
        enabled = preference.enabled if preference else True
        email_enabled = preference.email_enabled if preference else True
        minutes_before = preference.minutes_before if preference else 30

        if not enabled or not email_enabled:
            continue

        window_start = now - MISSED_REMINDER_GRACE
        window_end = now + timedelta(minutes=minutes_before)

        tasks = db.scalars(
            select(Task).where(
                Task.user_id == user.id,
                Task.status.in_(("pending", "in_progress")),
                Task.due_at.is_not(None),
                Task.due_at >= window_start,
                Task.due_at <= window_end,
            )
        ).all()

        for task in tasks:
            due_at = _as_utc(task.due_at)
            if _delivery_exists(
                db,
                task_id=task.id,
                task_due_at=due_at,
            ):
                continue

            db.add(
                ReminderDelivery(
                    user_id=user.id,
                    task_id=task.id,
                    reminder_id=None,
                    task_due_at=due_at,
                    reminder_due_at=None,
                    item_title=task.title,
                    recipient_email=user.email,
                    status="pending",
                    attempts=0,
                )
            )

        reminders = db.scalars(
            select(Reminder).where(
                Reminder.user_id == user.id,
                Reminder.status == "pending",
                Reminder.due_at.is_not(None),
                Reminder.due_at >= window_start,
                Reminder.due_at <= window_end,
            )
        ).all()

        for reminder in reminders:
            due_at = _as_utc(reminder.due_at)
            if _delivery_exists(
                db,
                reminder_id=reminder.id,
                reminder_due_at=due_at,
            ):
                continue

            db.add(
                ReminderDelivery(
                    user_id=user.id,
                    task_id=None,
                    reminder_id=reminder.id,
                    task_due_at=None,
                    reminder_due_at=due_at,
                    item_title=reminder.title,
                    recipient_email=user.email,
                    status="pending",
                    attempts=0,
                )
            )

    db.commit()


def _delivery_is_current(db, delivery: ReminderDelivery) -> tuple[bool, str, datetime, str]:
    if delivery.task_id is not None:
        task = db.get(Task, delivery.task_id)
        if (
            task is None
            or task.status not in ("pending", "in_progress")
            or _as_utc(task.due_at) != _as_utc(delivery.task_due_at)
        ):
            return False, "", delivery.task_due_at or datetime.now(timezone.utc), "task"
        return True, task.title, _as_utc(task.due_at), "task"

    reminder = db.get(Reminder, delivery.reminder_id)
    if (
        reminder is None
        or reminder.status != "pending"
        or _as_utc(reminder.due_at) != _as_utc(delivery.reminder_due_at)
    ):
        return False, "", delivery.reminder_due_at or datetime.now(timezone.utc), "reminder"

    return True, reminder.title, _as_utc(reminder.due_at), "reminder"


def _process_deliveries(db, now: datetime) -> None:
    stale_before = now - STALE_SENDING_AFTER

    stale = db.scalars(
        select(ReminderDelivery).where(
            ReminderDelivery.status == "sending",
            ReminderDelivery.created_at < stale_before,
            ReminderDelivery.attempts < MAX_ATTEMPTS,
        )
    ).all()
    for delivery in stale:
        delivery.status = "failed"
        delivery.last_error = "A previous delivery attempt did not finish."
    if stale:
        db.commit()

    deliveries = db.scalars(
        select(ReminderDelivery).where(
            ReminderDelivery.status.in_(("pending", "failed")),
            ReminderDelivery.attempts < MAX_ATTEMPTS,
        ).order_by(ReminderDelivery.created_at.asc())
    ).all()

    for delivery in deliveries:
        user = db.get(User, delivery.user_id)
        if user is None or not user.is_active:
            delivery.status = "cancelled"
            db.commit()
            continue

        preference = _preference_for(db, user.id)
        if preference is not None and (
            not preference.enabled or not preference.email_enabled
        ):
            continue

        if not is_email_configured():
            continue

        is_current, title, due_at, item_type = _delivery_is_current(db, delivery)
        if not is_current:
            delivery.status = "cancelled"
            db.commit()
            continue

        timezone_name = "UTC"
        if delivery.reminder_id is not None:
            reminder = db.get(Reminder, delivery.reminder_id)
            if reminder is None:
                delivery.status = "cancelled"
                db.commit()
                continue
            timezone_name = reminder.timezone

        delivery.item_title = title
        delivery.status = "sending"
        delivery.attempts += 1
        delivery.last_error = None
        db.commit()

        try:
            send_reminder_email(
                recipient=delivery.recipient_email,
                task_title=title,
                due_at=due_at,
                timezone_name=timezone_name,
                item_type=item_type,
            )
            delivery.status = "sent"
            delivery.sent_at = datetime.now(timezone.utc)

            if delivery.reminder_id is not None:
                reminder = db.get(Reminder, delivery.reminder_id)
                if (
                    reminder is not None
                    and reminder.status == "pending"
                    and reminder.recurrence != "none"
                    and _as_utc(reminder.due_at) == _as_utc(delivery.reminder_due_at)
                ):
                    reminder.due_at = next_occurrence(
                        reminder.due_at,
                        reminder.recurrence,
                        reminder.timezone,
                    )
                    reminder.updated_at = datetime.now(timezone.utc)

        except Exception as exc:
            delivery.status = "failed"
            delivery.last_error = str(exc)[:2000]

        db.commit()


def run_reminder_job(now: datetime | None = None) -> None:
    """Run one scheduling pass. Safe to call from the scheduler or tests."""
    db = SessionLocal()
    try:
        current_time = _as_utc(now or datetime.now(timezone.utc))
        _create_due_deliveries(db, current_time)
        _process_deliveries(db, current_time)
    finally:
        db.close()
