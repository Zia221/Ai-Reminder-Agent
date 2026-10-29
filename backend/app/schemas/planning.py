
from datetime import date

from pydantic import BaseModel, Field


class DailyPlanRequest(BaseModel):
    plan_date: date
    available_minutes: int = Field(
        ge=30,
        le=960,
    )


class PlanItem(BaseModel):
    task_id: int
    title: str
    priority: str
    start_time: str
    end_time: str
    duration_minutes: int
    status: str = "pending"


class DailyPlanRead(BaseModel):
    id: int
    plan_date: date
    available_minutes: int
    plan_items: list[PlanItem]
    summary: str


class NextTaskRecommendation(BaseModel):
    task_id: int
    title: str
    priority: str
    reason: str
