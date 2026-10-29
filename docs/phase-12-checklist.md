# Phase 12 — Final Testing & Quality

## Automated checks

- Backend API tests run with Pytest against an isolated in-memory SQLite database.
- Reminder scheduler tests cover recurring reminder advancement, duplicate prevention, disabled automation, and failed-send retry.
- Frontend TypeScript project compilation is checked with `tsc -b`.
- Alembic migration graph has one head revision.

## Local manual verification

1. Register a user and log in.
2. Create a one-time reminder and a daily recurring reminder.
3. Configure SMTP and enable email notifications.
4. Leave the backend running; confirm delivery history records a sent email.
5. Confirm recurring reminder moves to its next occurrence.
6. Disable automation and confirm no new notification is sent.
7. Create a task, complete it, and confirm progress and weekly report statistics update.
8. Generate a smart plan without an OpenAI key and verify the deterministic fallback.
9. Configure an OpenAI key and test AI parsing, assistant, mentor, and AI planning.
10. Download a weekly report PDF.

## Limitations to remember

- The in-process scheduler is for a single local backend process.
- SMTP delivery depends on the configured mail provider.
- Existing records already removed by an earlier destructive migration cannot be restored by recreating the table schema; restore those records from a database backup if available.
