# AI Reminder Agent

A local-first productivity application built with FastAPI, PostgreSQL, SQLAlchemy/Alembic, React, TypeScript, and Vite.

## Features

- User registration, login, access tokens, refresh-token rotation, and logout
- One-time and recurring reminders with time-zone support
- AI-assisted reminder parsing (optional OpenAI API key)
- Task management and a personal AI assistant with confirmation-based task proposals
- Daily progress and goal tracking
- Weekly productivity reports with PDF export
- AI project mentor, skill-gap analysis, and learning roadmaps
- Smart daily planning and next-task recommendations
- Background email notifications for tasks and reminders
- Delivery history, retry handling, and user-specific automation preferences

## Requirements

- Python 3.12
- PostgreSQL
- Node.js 22 or later and npm
- `uv` Python package manager

## Local setup

### 1. Configure PostgreSQL

Create a database and user using pgAdmin or `psql`. Example:

```sql
CREATE USER reminder_app WITH PASSWORD 'choose_a_strong_password';
CREATE DATABASE ai_reminder_agent OWNER reminder_app;
```

If your PostgreSQL server uses a port other than `5433`, update `DATABASE_URL`.

### 2. Configure the backend

From the repository root:

```bash
cd backend
uv python install 3.12
uv sync
cp .env.example .env
```

Edit `backend/.env` and set at least:

- `DATABASE_URL`
- `JWT_SECRET_KEY`

Optional:

- `OPENAI_API_KEY` for AI parsing, assistant, mentor, smart planning, and AI report summaries
- `SMTP_USERNAME`, `SMTP_PASSWORD`, and optionally `SMTP_FROM` for email notifications
- `REMINDER_SCHEDULER_ENABLED=true` to enable the local scheduler

For Gmail SMTP, use a Google App Password. Do not use your normal Gmail password and never commit `.env`.

Apply database migrations:

```bash
uv run alembic upgrade head
```

Start the API:

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check:

- API health: <http://127.0.0.1:8000/health>
- Database readiness: <http://127.0.0.1:8000/health/ready>
- Swagger: <http://127.0.0.1:8000/docs>

### 3. Configure the frontend

Open a second terminal from the repository root:

```bash
cd apps/web
npm ci
cp .env.example .env
npm run dev
```

Open the Vite URL shown in the terminal (normally <http://localhost:5173>).

## Run tests and quality checks

Backend tests use a dedicated in-memory SQLite database, so they do not modify your PostgreSQL data:

```bash
cd backend
uv run pytest -v
uv run alembic heads
uv run alembic current
```

Frontend:

```bash
cd apps/web
npm run build
npm run lint
```

## Reminder scheduling behavior

- The backend scheduler checks due task and reminder notifications every minute.
- Reminder preferences define whether notifications are enabled and how far before the due time to notify.
- A one-time reminder is delivered once for its scheduled occurrence.
- Daily, weekly, and monthly reminders advance to the next occurrence after successful email delivery.
- Failed deliveries are recorded and retried up to three times automatically; a user can manually retry from the Automation page.
- Email notifications require SMTP settings. AI features require an OpenAI API key.
- Keep one backend process running locally when testing scheduled notifications. Multiple server workers should not be used with the in-process scheduler.

## Notes

- This project is intended for local development and testing. It is not deployed by these instructions.
- Never share your `.env` file, database credentials, JWT secret, SMTP password, or OpenAI API key.
