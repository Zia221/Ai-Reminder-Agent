
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Priority = Literal["low", "medium", "high", "urgent"]
ReminderStatus = Literal["pending", "completed", "paused", "cancelled"]
Recurrence = Literal["none", "daily", "weekly", "monthly"]


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_at: datetime | None = None
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    priority: Priority = "medium"
    recurrence: Recurrence = "none"
    natural_language_input: str | None = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty.")
        return value

    @field_validator("due_at")
    @classmethod
    def require_aware_datetime(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and (
            value.tzinfo is None or value.utcoffset() is None
        ):
            raise ValueError(
                "due_at must include a timezone offset."
            )
        return value


class ReminderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    due_at: datetime | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    priority: Priority | None = None
    recurrence: Recurrence | None = None
    status: ReminderStatus | None = None

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Title cannot be empty.")
        return value

    @field_validator("due_at")
    @classmethod
    def require_aware_datetime(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and (
            value.tzinfo is None or value.utcoffset() is None
        ):
            raise ValueError(
                "due_at must include a timezone offset."
            )
        return value


class ReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    description: str | None
    due_at: datetime | None
    timezone: str
    priority: Priority
    status: ReminderStatus
    recurrence: Recurrence
    natural_language_input: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReminderParseRequest(BaseModel):
    text: str = Field(min_length=3, max_length=1000)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)


class ReminderParseResult(BaseModel):
    title: str
    description: str | None = None
    due_at: datetime | None = None
    timezone: str
    priority: Priority = "medium"
    recurrence: Recurrence = "none"
    natural_language_input: str
