
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.task import Task
from app.models.smart_plan import SmartPlan
from app.schemas.planning import (
    DailyPlanRequest,
    DailyPlanRead,
    NextTaskRecommendation,
)
from app.services.planning_service import (
    generate_daily_plan,
    recommend_next_task,
)

router = APIRouter(
    prefix="/planning",
    tags=["Smart Planning"],
)


@router.post("/generate", response_model=DailyPlanRead)
def generate_plan(
    payload: DailyPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = db.scalars(
        select(Task).where(
            Task.user_id == current_user.id,
            Task.status.in_([
                "pending",
                "in_progress",
            ]),
        )
    ).all()

    if not tasks:
        raise HTTPException(
            status_code=400,
            detail="No pending tasks available to plan.",
        )

    try:
        result = generate_daily_plan(
            tasks,
            payload.available_minutes,
        )

        plan = SmartPlan(
            user_id=current_user.id,
            plan_date=payload.plan_date,
            available_minutes=payload.available_minutes,
            plan_items=result["plan_items"],
            summary=result["summary"],
        )

        db.add(plan)
        db.commit()
        db.refresh(plan)

        return plan

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Could not generate daily plan. Check AI configuration.",
        )


@router.get("/today", response_model=DailyPlanRead)
def get_today_plan(
    plan_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    selected_date = plan_date or datetime.now(ZoneInfo("Asia/Karachi")).date()

    plan = db.scalar(
        select(SmartPlan).where(
            SmartPlan.user_id == current_user.id,
            SmartPlan.plan_date == selected_date,
        ).order_by(SmartPlan.created_at.desc())
    )

    if plan is None:
        raise HTTPException(
            status_code=404,
            detail="No plan found for this date.",
        )

    return plan


@router.get(
    "/recommendation",
    response_model=NextTaskRecommendation | None,
)
def get_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = db.scalars(
        select(Task).where(
            Task.user_id == current_user.id,
            Task.status.in_([
                "pending",
                "in_progress",
            ]),
        )
    ).all()

    result = recommend_next_task(tasks)

    return result
