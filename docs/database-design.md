# AI Reminder Agent — Database Design

PostgreSQL is the primary database. Alembic manages schema changes.

## Implemented entities

- `users`: identity and account state
- `refresh_tokens`: hashed refresh-token records and revocation
- `tasks`: task status, due date, priority, and completion timestamp
- `reminders`: one-time and recurring reminders with time zone and status
- `reminder_preferences`: automation enablement and lead time
- `reminder_deliveries`: notification source, scheduled occurrence, recipient, attempt count, status, and errors
- `assistant_messages`: user-scoped assistant history
- `daily_goals`: user goal for a specific date
- `smart_plans`: generated daily plan
- `skill_profiles`: user target role, skills, experience, and goals
- `learning_roadmaps`: skill-gap analysis and milestone data

## Relationships and constraints

- Each task and reminder belongs to one user.
- Each delivery belongs to one user and references exactly one task or reminder.
- Task delivery uniqueness is enforced by `(task_id, task_due_at)`.
- Reminder delivery uniqueness is enforced by `(reminder_id, reminder_due_at)`.
- Daily goals are unique by `(user_id, goal_date)`.
- Skill profiles are unique by `user_id`.
- Foreign keys cascade user-owned records on account deletion.

## Reporting

Daily and weekly report values are computed from tasks and daily goals. Reports are generated on request and are not stored as a separate report entity in this implementation.

## Privacy and configuration

Secrets are kept in the local `backend/.env` file and must not be committed. PostgreSQL credentials, JWT secret, SMTP password, and OpenAI API key must not be shared.
