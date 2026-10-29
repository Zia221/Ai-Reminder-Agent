
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from openai import OpenAI

from app.core.config import settings
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.daily_goal import DailyGoal
from app.models.task import Task
from app.schemas.report import DailyReportItem, WeeklyReportRead


def get_week_dates(week_start: date) -> tuple[date, date]:
    # Normalize the selected date to Monday.
    monday = week_start - timedelta(days=week_start.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def to_local_date(
    value: datetime | None,
    zone: ZoneInfo,
) -> date | None:
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(zone).date()


def build_daily_item(
    day: date,
    zone: ZoneInfo,
    tasks: list[Task],
    goal_target: int,
) -> DailyReportItem:
    created = sum(
        1 for task in tasks
        if to_local_date(task.created_at, zone) == day
    )

    completed = sum(
        1 for task in tasks
        if task.status == "completed"
        and to_local_date(task.completed_at, zone) == day
    )

    due_tasks = [
        task for task in tasks
        if to_local_date(task.due_at, zone) == day
        and task.status != "cancelled"
    ]

    completed_due = sum(
        1 for task in due_tasks if task.status == "completed"
    )

    pending_due = len(due_tasks) - completed_due

    overdue = sum(
        1 for task in tasks
        if task.due_at is not None
        and to_local_date(task.due_at, zone) is not None
        and to_local_date(task.due_at, zone) < day
        and task.status != "cancelled"
        and (
            task.status != "completed"
            or (
                task.completed_at is not None
                and to_local_date(task.completed_at, zone) > day
            )
        )
    )

    rate = (
        round(completed_due / len(due_tasks) * 100, 1)
        if due_tasks else 0.0
    )

    return DailyReportItem(
        day=day,
        tasks_created=created,
        tasks_completed=completed,
        tasks_due=len(due_tasks),
        completed_due=completed_due,
        pending_due=pending_due,
        overdue=overdue,
        completion_rate=rate,
        goal_target=goal_target,
        goal_progress=completed,
        goal_reached=completed >= goal_target,
    )


def create_fallback_summary(report: WeeklyReportRead) -> str:
    best_day = max(
        report.daily_breakdown,
        key=lambda item: item.tasks_completed,
    )

    return (
        f"You completed {report.tasks_completed} tasks this week and "
        f"created {report.tasks_created} tasks. "
        f"Your completion rate for tasks due this week was "
        f"{report.completion_rate}%. "
        f"You reached your daily goal on {report.goals_reached} days. "
        f"Your most productive day was {best_day.day.isoformat()}, "
        f"with {best_day.tasks_completed} completed tasks. "
        f"You have {report.pending_due} tasks from this week still pending. "
        "For next week, review overdue tasks early and set a realistic "
        "daily goal."
    )


def generate_ai_summary(report: WeeklyReportRead) -> tuple[str, bool]:
    api_key = settings.openai_api_key

    if not api_key:
        return create_fallback_summary(report), False

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a productivity coach. Write a concise "
                        "weekly report summary based only on the supplied "
                        "statistics. Mention strengths, a realistic "
                        "improvement, and one actionable suggestion. "
                        "Do not invent tasks, events, or personal details. "
                        "Do not shame the user. Keep it under 150 words."
                    ),
                },
                {
                    "role": "user",
                    "content": report.model_dump_json(),
                },
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content

        if content:
            return content.strip(), True

    except Exception:
        pass

    return create_fallback_summary(report), False


def build_weekly_report(
    db: Session,
    user_id: int,
    week_start: date,
    timezone_name: str,
) -> WeeklyReportRead:
    zone = ZoneInfo(timezone_name)
    monday, sunday = get_week_dates(week_start)

    tasks = list(
        db.scalars(
            select(Task).where(Task.user_id == user_id)
        ).all()
    )

    goals = db.scalars(
        select(DailyGoal).where(
            DailyGoal.user_id == user_id,
            DailyGoal.goal_date >= monday,
            DailyGoal.goal_date <= sunday,
        )
    ).all()

    goals_by_day = {
        goal.goal_date: goal.target_tasks
        for goal in goals
    }

    daily_items = [
        build_daily_item(
            monday + timedelta(days=offset),
            zone,
            tasks,
            goals_by_day.get(monday + timedelta(days=offset), 3),
        )
        for offset in range(7)
    ]

    tasks_created = sum(item.tasks_created for item in daily_items)
    tasks_completed = sum(item.tasks_completed for item in daily_items)
    tasks_due = sum(item.tasks_due for item in daily_items)
    completed_due = sum(item.completed_due for item in daily_items)
    pending_due = sum(item.pending_due for item in daily_items)
    overdue = daily_items[-1].overdue

    completion_rate = (
        round(completed_due / tasks_due * 100, 1)
        if tasks_due else 0.0
    )

    goals_reached = sum(
        1 for item in daily_items if item.goal_reached
    )

    report = WeeklyReportRead(
        week_start=monday,
        week_end=sunday,
        tasks_created=tasks_created,
        tasks_completed=tasks_completed,
        tasks_due=tasks_due,
        completed_due=completed_due,
        pending_due=pending_due,
        overdue=overdue,
        completion_rate=completion_rate,
        goals_reached=goals_reached,
        daily_breakdown=daily_items,
        summary="",
        summary_is_ai=False,
    )

    summary, is_ai = generate_ai_summary(report)

    report.summary = summary
    report.summary_is_ai = is_ai

    return report
