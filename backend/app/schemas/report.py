
from datetime import date
from pydantic import BaseModel, ConfigDict


class DailyReportItem(BaseModel):
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


class WeeklyReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    week_start: date
    week_end: date
    tasks_created: int
    tasks_completed: int
    tasks_due: int
    completed_due: int
    pending_due: int
    overdue: int
    completion_rate: float
    goals_reached: int
    daily_breakdown: list[DailyReportItem]
    summary: str
    summary_is_ai: bool
