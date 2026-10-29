# AI Reminder Agent — Implemented Architecture

## Application components

- **Web client:** React, TypeScript, Vite, React Router
- **API:** Python 3.12 and FastAPI
- **Database:** PostgreSQL with SQLAlchemy and Alembic migrations
- **AI services:** OpenAI API, optional through `OPENAI_API_KEY`
- **Email:** SMTP (Gmail SMTP with an App Password is supported)
- **Scheduler:** APScheduler runs inside the local FastAPI process
- **PDF reports:** ReportLab
- **Tests:** Pytest and an isolated in-memory SQLite test database

## Request flow

1. The React client sends an HTTP request to FastAPI.
2. FastAPI validates the request and verifies the access token.
3. API routes scope records to the authenticated user.
4. SQLAlchemy reads or writes PostgreSQL records.
5. FastAPI returns JSON or a generated PDF.
6. The frontend uses a shared API helper that attempts one refresh-token rotation after a 401 response.

## Reminder and email flow

1. The user creates a one-time or recurring reminder. The selected IANA time zone is stored with it.
2. The scheduler checks due tasks and reminders every minute.
3. A delivery row is created for each scheduled occurrence, with a uniqueness constraint to prevent duplicate queue records.
4. SMTP sends the notification.
5. The delivery result and attempt count are stored.
6. Failed sends can be retried automatically up to three attempts or manually from the Automation page.
7. A recurring reminder advances to its next occurrence only after a successful notification.

The scheduler is intentionally process-local for this development project. Keep one backend process running when testing reminders. Do not start multiple workers with this in-process scheduler.

## AI behavior

AI features are optional and require an OpenAI API key:
- Natural-language reminder parsing
- Assistant chat and proposed task creation
- Skill-gap analysis, learning roadmap, and mentor chat
- AI-assisted smart planning
- AI-generated weekly summary

The backend validates AI-generated structures before using them. Smart planning falls back to deterministic task prioritization when the AI service is not configured or unavailable. Weekly reports use a statistics-based fallback summary.

## Data boundaries

- A **task** is a work item that can be completed.
- A **reminder** is a time-based notification, including recurrence.
- A delivery record is an attempt to send a notification, not proof that a task was completed.
- Daily progress and weekly reports are calculated from task status and completion timestamps.
- Every user-owned API query must be scoped to the authenticated user's ID.

## Local operation

The application is designed to run locally using PostgreSQL, the FastAPI development server, and the Vite development server. This repository does not include deployment configuration or a deployed environment.
