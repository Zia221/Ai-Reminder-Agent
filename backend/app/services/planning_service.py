from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import json

from openai import OpenAI

from app.core.config import settings
from app.models.task import Task


def get_client() -> OpenAI:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.openai_api_key)


def get_model() -> str:
    return settings.openai_model


def prioritize_tasks(tasks: list[Task]) -> list[Task]:
    priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
    now = datetime.now().astimezone()

    def sort_key(task: Task):
        due_at = task.due_at
        if due_at is not None and due_at.tzinfo is None:
            due_at = due_at.replace(tzinfo=now.tzinfo)
        elif due_at is not None:
            due_at = due_at.astimezone(now.tzinfo)

        overdue = due_at is not None and due_at < now
        return (
            0 if overdue else 1,
            priority_order.get(task.priority, 4),
            due_at or datetime.max.replace(tzinfo=now.tzinfo),
            task.id,
        )

    return sorted(tasks, key=sort_key)


def _default_duration(task: Task) -> int:
    return {"urgent": 60, "high": 60, "medium": 45, "low": 30}.get(
        task.priority,
        45,
    )


def _format_time(value: datetime) -> str:
    return value.strftime("%H:%M")


def _build_schedule(
    tasks: list[Task],
    available_minutes: int,
    ordered_ids: list[int] | None = None,
    durations: dict[int, int] | None = None,
) -> list[dict]:
    task_lookup = {task.id: task for task in tasks}
    ordered_tasks = []
    seen: set[int] = set()

    if ordered_ids:
        for task_id in ordered_ids:
            if task_id in task_lookup and task_id not in seen:
                ordered_tasks.append(task_lookup[task_id])
                seen.add(task_id)

    for task in prioritize_tasks(tasks):
        if task.id not in seen:
            ordered_tasks.append(task)
            seen.add(task.id)

    # Avoid creating a schedule that runs past midnight.
    capacity = min(available_minutes, 16 * 60)
    planning_zone = ZoneInfo("Asia/Karachi")
    current = datetime.combine(
        datetime.now(planning_zone).date(),
        time(hour=8, minute=0),
        tzinfo=planning_zone,
    )
    total = 0
    items: list[dict] = []

    for task in ordered_tasks:
        duration = (durations or {}).get(task.id, _default_duration(task))
        if not isinstance(duration, int) or isinstance(duration, bool):
            duration = _default_duration(task)
        duration = max(15, min(180, duration))

        if total + duration > capacity:
            continue

        end = current + timedelta(minutes=duration)
        items.append(
            {
                "task_id": task.id,
                "title": task.title,
                "priority": task.priority,
                "start_time": _format_time(current),
                "end_time": _format_time(end),
                "duration_minutes": duration,
                "status": task.status,
            }
        )
        current = end
        total += duration

    return items


def generate_daily_plan(tasks: list[Task], available_minutes: int) -> dict:
    ranked = prioritize_tasks(tasks)
    ordered_ids: list[int] | None = None
    durations: dict[int, int] = {}
    summary = ""

    if settings.openai_api_key:
        client = None
        try:
            client = get_client()
            task_data = [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority,
                    "due_at": task.due_at.isoformat() if task.due_at else None,
                }
                for task in ranked
            ]

            prompt = f"""
You are a smart productivity planner.

Available minutes: {available_minutes}
Tasks:
{json.dumps(task_data, ensure_ascii=False, default=str)}

Return JSON only:
{{
  "summary": "short realistic summary",
  "plan_items": [
    {{"task_id": 1, "duration_minutes": 45}}
  ]
}}

Rules:
- Use only the supplied task IDs.
- Prioritize urgent tasks and deadlines.
- Do not schedule the same task twice.
- Choose realistic durations between 15 and 180 minutes.
- Do not include start_time or end_time.
"""
            response = client.chat.completions.create(
                model=get_model(),
                messages=[
                    {"role": "system", "content": "Return valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content
            if content:
                data = json.loads(content)
                allowed_ids = {task.id for task in ranked}
                ordered_ids = []
                for item in data.get("plan_items", []):
                    task_id = item.get("task_id")
                    duration = item.get("duration_minutes")
                    if task_id in allowed_ids and task_id not in ordered_ids:
                        ordered_ids.append(task_id)
                        if isinstance(duration, int) and not isinstance(duration, bool):
                            durations[task_id] = duration
                summary = str(data.get("summary") or "").strip()[:2000]
        except Exception:
            # Keep core planning available when the AI service is unavailable.
            ordered_ids = None
            durations = {}
            summary = ""
        finally:
            if client is not None:
                client.close()

    plan_items = _build_schedule(
        ranked,
        available_minutes,
        ordered_ids=ordered_ids,
        durations=durations,
    )

    if not summary:
        if settings.openai_api_key:
            summary = (
                "Your plan is ready using task priority and deadline ordering. "
                "The AI planner was unavailable, so a reliable fallback was used."
            )
        else:
            summary = (
                "Your plan is ready using task priority and deadline ordering. "
                "Add an OpenAI API key to enable AI-assisted scheduling."
            )

    return {"summary": summary, "plan_items": plan_items}


def recommend_next_task(tasks: list[Task]) -> dict | None:
    ranked_tasks = prioritize_tasks(tasks)
    if not ranked_tasks:
        return None

    task = ranked_tasks[0]
    return {
        "task_id": task.id,
        "title": task.title,
        "priority": task.priority,
        "reason": (
            "This is the highest-ranked active task based on priority "
            "and its deadline."
        ),
    }
