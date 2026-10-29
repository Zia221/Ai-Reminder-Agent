from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReminderPreferenceUpdate(BaseModel):
    enabled: bool = True
    email_enabled: bool = False
    minutes_before: int = Field(ge=5, le=1440)


class ReminderPreferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enabled: bool
    email_enabled: bool
    minutes_before: int


class ReminderDeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int | None
    reminder_id: int | None
    item_title: str | None
    task_due_at: datetime | None
    reminder_due_at: datetime | None
    recipient_email: str
    status: str
    attempts: int
    last_error: str | None
    sent_at: datetime | None
    created_at: datetime
