import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.reminder import Reminder
from app.models.user import User
from app.schemas.reminder import (
    ReminderCreate,
    ReminderParseRequest,
    ReminderParseResult,
    ReminderRead,
    ReminderUpdate,
)

router = APIRouter(prefix="/reminders", tags=["Reminders"])


def validate_timezone(value: str) -> None:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(
            status_code=422,
            detail="Use a valid IANA timezone, such as Asia/Karachi.",
        )


def normalize_due_at(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise HTTPException(
            status_code=422,
            detail="due_at must include a timezone offset.",
        )
    return value.astimezone(timezone.utc)


def get_owned_reminder(
    db: Session,
    reminder_id: int,
    user_id: int,
) -> Reminder:
    reminder = db.scalar(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        )
    )
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    return reminder


@router.post(
    "",
    response_model=ReminderRead,
    status_code=status.HTTP_201_CREATED,
)
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    validate_timezone(payload.timezone)

    if payload.recurrence != "none" and payload.due_at is None:
        raise HTTPException(
            status_code=422,
            detail="A due date and time are required for recurring reminders.",
        )

    reminder = Reminder(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        due_at=normalize_due_at(payload.due_at),
        timezone=payload.timezone,
        priority=payload.priority,
        recurrence=payload.recurrence,
        natural_language_input=payload.natural_language_input,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("", response_model=list[ReminderRead])
def list_reminders(
    reminder_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Reminder).where(Reminder.user_id == current_user.id)

    if reminder_status is not None:
        allowed = {"pending", "completed", "paused", "cancelled"}
        if reminder_status not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"status must be one of: {', '.join(sorted(allowed))}",
            )
        query = query.where(Reminder.status == reminder_status)

    query = query.order_by(Reminder.due_at.asc().nullslast(), Reminder.id.desc())
    return list(db.scalars(query).all())


@router.get("/{reminder_id}", response_model=ReminderRead)
def read_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_reminder(db, reminder_id, current_user.id)


@router.patch("/{reminder_id}", response_model=ReminderRead)
def update_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = get_owned_reminder(db, reminder_id, current_user.id)
    changes = payload.model_dump(exclude_unset=True)

    for field in ("title", "priority", "recurrence", "timezone", "status"):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=422, detail=f"{field} cannot be null.")

    timezone_name = changes.get("timezone", reminder.timezone)
    recurrence = changes.get("recurrence", reminder.recurrence)
    due_at = changes.get("due_at", reminder.due_at)

    if timezone_name is not None:
        validate_timezone(timezone_name)
    if recurrence != "none" and due_at is None:
        raise HTTPException(
            status_code=422,
            detail="A due date and time are required for recurring reminders.",
        )

    if "due_at" in changes:
        changes["due_at"] = normalize_due_at(changes["due_at"])

    if "status" in changes:
        if changes["status"] == "completed":
            reminder.completed_at = datetime.now(timezone.utc)
        else:
            reminder.completed_at = None

    for field, value in changes.items():
        setattr(reminder, field, value)

    reminder.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = get_owned_reminder(db, reminder_id, current_user.id)
    db.delete(reminder)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{reminder_id}/pause", response_model=ReminderRead)
def pause_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = get_owned_reminder(db, reminder_id, current_user.id)
    if reminder.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="Only pending reminders can be paused.",
        )
    reminder.status = "paused"
    reminder.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.post("/{reminder_id}/resume", response_model=ReminderRead)
def resume_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = get_owned_reminder(db, reminder_id, current_user.id)
    if reminder.status != "paused":
        raise HTTPException(
            status_code=409,
            detail="Only paused reminders can be resumed.",
        )
    reminder.status = "pending"
    reminder.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.post("/{reminder_id}/complete", response_model=ReminderRead)
def complete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = get_owned_reminder(db, reminder_id, current_user.id)
    reminder.status = "completed"
    reminder.completed_at = datetime.now(timezone.utc)
    reminder.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.post("/parse", response_model=ReminderParseResult)
def parse_reminder(
    payload: ReminderParseRequest,
    current_user: User = Depends(get_current_user),
):
    validate_timezone(payload.timezone)

    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="AI parsing is not configured. Set OPENAI_API_KEY in backend/.env.",
        )

    now = datetime.now(ZoneInfo(payload.timezone)).isoformat()
    client = OpenAI(api_key=settings.openai_api_key)

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract reminder details from the user's text. "
                        "Return JSON with keys: title, description, due_at, "
                        "timezone, priority, recurrence. "
                        "title is required. description and due_at may be null. "
                        "due_at must be ISO 8601 with a UTC offset, or null "
                        "if the date/time is ambiguous or absent. "
                        "Use only these priorities: low, medium, high, urgent. "
                        "Use only these recurrences: none, daily, weekly, monthly. "
                        "Do not invent dates or times. Resolve relative dates "
                        "using the supplied current time and timezone. "
                        "A recurring reminder must include a due_at value. "
                        "Return JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Current local time: {now}\n"
                        f"Timezone: {payload.timezone}\n"
                        f"Reminder request: {payload.text}"
                    ),
                },
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("The AI returned an empty response.")

        data = json.loads(content)
        data["natural_language_input"] = payload.text
        data["timezone"] = payload.timezone
        parsed = ReminderParseResult.model_validate(data)

        if parsed.due_at is not None:
            if parsed.due_at.tzinfo is None or parsed.due_at.utcoffset() is None:
                raise ValueError("The AI returned a date without a timezone.")
            parsed.due_at = parsed.due_at.astimezone(ZoneInfo(payload.timezone))

        if parsed.recurrence != "none" and parsed.due_at is None:
            raise ValueError("A recurring reminder requires a due date.")

        return parsed

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="AI could not interpret this request. Try rephrasing it.",
        ) from exc
    finally:
        client.close()
