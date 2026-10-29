
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class DailyGoalUpdate(BaseModel):
    goal_date: date
    target_tasks: Annotated[int, Field(ge=1, le=100)]


class DailyGoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_date: date
    target_tasks: int


class DailyProgressRead(BaseModel):
    day: date
    tasks_created: int
    tasks_completed: int
    tasks_due: int
    completed_due: int
    pending_due: int
    overdue: int
    completion_rate: float
    goal_target: int
    goal_progress: int
    goal_reached: bool


class ProgressHistoryRead(BaseModel):
    days: list[DailyProgressRead]
