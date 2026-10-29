
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Reminder(Base):
    __tablename__ = "reminders"

    __table_args__ = (
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="ck_reminders_priority",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'paused', 'cancelled')",
            name="ck_reminders_status",
        ),
        CheckConstraint(
            "recurrence IN ('none', 'daily', 'weekly', 'monthly')",
            name="ck_reminders_recurrence",
        ),
        Index("ix_reminders_user_due_at", "user_id", "due_at"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        String(64),
        default="UTC",
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(16),
        default="medium",
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(16),
        default="pending",
        nullable=False,
    )

    recurrence: Mapped[str] = mapped_column(
        String(16),
        default="none",
        nullable=False,
    )

    natural_language_input: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
