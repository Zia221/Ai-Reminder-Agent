
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.daily_goal import DailyGoal
from app.models.task import Task
from app.models.user import User
from app.schemas.progress import (
    DailyGoalRead,
    DailyGoalUpdate,
    DailyProgressRead,
    ProgressHistoryRead,
)

router = APIRouter(prefix="/progress", tags=["progress"])


def get_zone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        raise HTTPException(
            status_code=422,
            detail="Invalid timezone. Use an IANA timezone such as Asia/Karachi.",
        )


def local_date(value: datetime | None, zone: ZoneInfo) -> date | None:
    if value is None:
        return None
    if value.tzinfo is None:
        # Database timestamps should normally be timezone-aware.
        # Treat a naive value as UTC rather than the server's local time.
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(zone).date()


def build_daily_progress(
    day: date,
    zone: ZoneInfo,
    tasks: list[Task],
    goal_target: int,
) -> DailyProgressRead:
    created_today = [
        task for task in tasks
        if local_date(task.created_at, zone) == day
    ]

    completed_today = [
        task for task in tasks
        if task.status == "completed"
        and local_date(task.completed_at, zone) == day
    ]

    due_today = [
        task for task in tasks
        if local_date(task.due_at, zone) == day
        and task.status != "cancelled"
    ]

    completed_due = sum(
        1 for task in due_today if task.status == "completed"
    )

    pending_due = sum(
        1 for task in due_today if task.status != "completed"
    )

    overdue = sum(
        1
        for task in tasks
        if task.due_at is not None
        and local_date(task.due_at, zone) is not None
        and local_date(task.due_at, zone) < day
        and task.status not in ("cancelled",)
        and (
    (task.status != "completed" and task.completed_at is None)
    or (
        task.completed_at is not None
        and local_date(task.completed_at, zone) is not None
        and local_date(task.completed_at, zone) > day
    )
)
    )

    rate = (
        round(completed_due / len(due_today) * 100, 1)
        if due_today else 0.0
    )

    return DailyProgressRead(
        day=day,
        tasks_created=len(created_today),
        tasks_completed=len(completed_today),
        tasks_due=len(due_today),
        completed_due=completed_due,
        pending_due=pending_due,
        overdue=overdue,
        completion_rate=rate,
        goal_target=goal_target,
        goal_progress=len(completed_today),
        goal_reached=len(completed_today) >= goal_target,
    )


def load_user_tasks(db: Session, user_id: int) -> list[Task]:
    return list(
        db.scalars(
            select(Task).where(Task.user_id == user_id)
        ).all()
    )


def load_goal(
    db: Session,
    user_id: int,
    day: date,
) -> DailyGoal | None:
    return db.scalar(
        select(DailyGoal).where(
            DailyGoal.user_id == user_id,
            DailyGoal.goal_date == day,
        )
    )


@router.get("/daily", response_model=DailyProgressRead)
def get_daily_progress(
    day: date | None = None,
    timezone_name: str = Query(
        default="Asia/Karachi",
        alias="timezone",
        max_length=64,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    zone = get_zone(timezone_name)
    selected_day = day or datetime.now(zone).date()

    tasks = load_user_tasks(db, current_user.id)
    goal = load_goal(db, current_user.id, selected_day)

    return build_daily_progress(
        selected_day,
        zone,
        tasks,
        goal.target_tasks if goal else 3,
    )


@router.put("/goal", response_model=DailyGoalRead)
def update_daily_goal(
    payload: DailyGoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = load_goal(db, current_user.id, payload.goal_date)

    if goal is None:
        goal = DailyGoal(
            user_id=current_user.id,
            goal_date=payload.goal_date,
            target_tasks=payload.target_tasks,
        )
        db.add(goal)
    else:
        goal.target_tasks = payload.target_tasks

    db.commit()
    db.refresh(goal)
    return goal


@router.get("/history", response_model=ProgressHistoryRead)
def get_progress_history(
    days: int = Query(default=7, ge=1, le=90),
    timezone_name: str = Query(
        default="Asia/Karachi",
        alias="timezone",
        max_length=64,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    zone = get_zone(timezone_name)
    today = datetime.now(zone).date()
    first_day = today - timedelta(days=days - 1)

    tasks = load_user_tasks(db, current_user.id)

    goals = db.scalars(
        select(DailyGoal).where(
            DailyGoal.user_id == current_user.id,
            DailyGoal.goal_date >= first_day,
            DailyGoal.goal_date <= today,
        )
    ).all()

    goals_by_day = {goal.goal_date: goal.target_tasks for goal in goals}

    results = [
        build_daily_progress(
            first_day + timedelta(days=offset),
            zone,
            tasks,
            goals_by_day.get(first_day + timedelta(days=offset), 3),
        )
        for offset in range(days)
    ]

    return ProgressHistoryRead(days=results)
