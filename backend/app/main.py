from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import (
    assistant,
    auth,
    automation,
    mentor,
    planning,
    progress,
    reminders,
    reports,
    tasks,
    users,
)
from app.core.config import settings
from app.db.session import engine
from app.services.reminder_scheduler import run_reminder_job


scheduler = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.reminder_scheduler_enabled and not scheduler.running:
        scheduler.add_job(
            run_reminder_job,
            trigger="interval",
            minutes=1,
            id="automatic_task_and_reminder_notifications",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()

    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    reminders.router,
    users.router,
    planning.router,
    automation.router,
    tasks.router,
    mentor.router,
    reports.router,
    assistant.router,
    progress.router,
):
    app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Check whether the API process is running."""
    return {"status": "ok", "app": settings.app_name}


@app.get("/health/ready", tags=["Health"])
def readiness_check() -> dict[str, str]:
    """Check whether the API can reach the configured database."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable. Check DATABASE_URL and database service.",
        ) from exc

    return {"status": "ready", "database": "connected"}
