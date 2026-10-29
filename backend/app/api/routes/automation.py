from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.task import Task
from app.models.reminder import Reminder
from app.models.reminder_automation import ReminderPreference, ReminderDelivery
from app.schemas.reminder_automation import (
    ReminderPreferenceUpdate,
    ReminderPreferenceRead,
    ReminderDeliveryRead,
)

router = APIRouter(
    prefix="/reminders/automation",
    tags=["Reminder Automation"],
)


def same_instant(left, right) -> bool:
    if left is None or right is None:
        return left is right
    if left.tzinfo is None:
        left = left.replace(tzinfo=timezone.utc)
    if right.tzinfo is None:
        right = right.replace(tzinfo=timezone.utc)
    return left.astimezone(timezone.utc) == right.astimezone(timezone.utc)


def preference_payload(preference: ReminderPreference | None) -> dict:
    if preference is not None:
        return {
            "enabled": preference.enabled,
            "email_enabled": preference.email_enabled and settings.smtp_configured,
            "minutes_before": preference.minutes_before,
        }

    return {
        "enabled": True,
        "email_enabled": settings.smtp_configured,
        "minutes_before": 30,
    }


@router.get("/preferences", response_model=ReminderPreferenceRead)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preference = db.scalar(
        select(ReminderPreference).where(
            ReminderPreference.user_id == current_user.id
        )
    )
    return preference_payload(preference)


@router.put("/preferences", response_model=ReminderPreferenceRead)
def update_preferences(
    payload: ReminderPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.email_enabled and not settings.smtp_configured:
        raise HTTPException(
            status_code=503,
            detail="Email is not configured. Set SMTP_USERNAME and SMTP_PASSWORD in backend/.env first.",
        )

    preference = db.scalar(
        select(ReminderPreference).where(
            ReminderPreference.user_id == current_user.id
        )
    )

    if preference is None:
        preference = ReminderPreference(
            user_id=current_user.id,
            **payload.model_dump(),
        )
        db.add(preference)
    else:
        for key, value in payload.model_dump().items():
            setattr(preference, key, value)

    db.commit()
    db.refresh(preference)
    return preference


@router.get("/history", response_model=list[ReminderDeliveryRead])
def get_reminder_history(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(ReminderDelivery)
        .where(ReminderDelivery.user_id == current_user.id)
        .order_by(ReminderDelivery.created_at.desc())
        .limit(limit)
    ).all()


@router.post("/history/{delivery_id}/retry", response_model=ReminderDeliveryRead)
def retry_delivery(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delivery = db.scalar(
        select(ReminderDelivery).where(
            ReminderDelivery.id == delivery_id,
            ReminderDelivery.user_id == current_user.id,
        )
    )

    if delivery is None:
        raise HTTPException(status_code=404, detail="Delivery not found.")

    if delivery.status != "failed":
        raise HTTPException(
            status_code=409,
            detail="Only failed deliveries can be retried.",
        )

    if not settings.smtp_configured:
        raise HTTPException(
            status_code=503,
            detail="Email is not configured. Set SMTP_USERNAME and SMTP_PASSWORD first.",
        )

    if delivery.task_id is not None:
        task = db.get(Task, delivery.task_id)
        if (
            task is None
            or task.status not in ("pending", "in_progress")
            or not same_instant(task.due_at, delivery.task_due_at)
        ):
            delivery.status = "cancelled"
            db.commit()
            raise HTTPException(
                status_code=409,
                detail="This task has changed or is no longer active.",
            )
    elif delivery.reminder_id is not None:
        reminder = db.get(Reminder, delivery.reminder_id)
        if (
            reminder is None
            or reminder.status != "pending"
            or not same_instant(reminder.due_at, delivery.reminder_due_at)
        ):
            delivery.status = "cancelled"
            db.commit()
            raise HTTPException(
                status_code=409,
                detail="This reminder has changed or is no longer active.",
            )

    delivery.status = "pending"
    delivery.attempts = 0
    delivery.last_error = None
    db.commit()
    db.refresh(delivery)
    return delivery
