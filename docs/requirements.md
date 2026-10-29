# AI Reminder Agent — Implemented Product Scope

## Product goal

A personal productivity web application for creating reminders, managing tasks, tracking completion, and using optional AI tools to organize work.

## Included features

### Accounts
- Registration and login
- Access tokens and rotating refresh tokens
- Logout and account-active checks
- User-scoped API access

### Reminders
- Create, list, read, update, pause, resume, complete, and delete reminders
- One-time reminders
- Daily, weekly, and monthly recurrence
- IANA time-zone validation and local-time recurrence
- Optional AI interpretation of natural-language reminder requests

### Tasks and assistant
- Task creation, update, completion, and deletion
- Priorities and due dates
- AI assistant chat with saved history
- Task proposals require user confirmation before creation

### Productivity
- Daily progress and daily goals
- Weekly reports with a daily breakdown
- PDF export
- Smart daily planning and next-task recommendations

### AI mentor
- Skill profile
- Skill-gap analysis
- Learning roadmap and milestone tracking
- Mentor chat

### Notifications
- Global automation preferences
- SMTP email delivery for task and reminder notifications
- Delivery history
- Automatic retry and manual retry for failed sends

## Data integrity rules

- A reminder is not proof of task completion.
- Email delivery is not proof of task completion.
- Daily and weekly completion statistics are derived from task status and completion timestamps.
- User records remain isolated by authenticated user ID.
- AI output does not directly execute unconfirmed task actions.

## External configuration

- PostgreSQL is required for the normal local application.
- OpenAI API key is optional; AI features return a helpful configuration response or use a deterministic fallback where supported.
- SMTP credentials are optional; email notification settings remain disabled until SMTP is configured.
- Gmail SMTP uses an App Password, not a normal Gmail password.

## Not included in this development scope

- Password-reset email flows
- Gmail OAuth or inbox access
- Mobile application
- Payment processing
- Deployment or public hosting
- Multi-process scheduler/worker infrastructure
- Stored progress journals independent of task records
