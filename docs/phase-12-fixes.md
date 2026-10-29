# Phase 12 — Fixes Applied

## Backend and database

- Completed the Alembic migration graph with one head revision.
- Removed destructive upgrade operations that dropped the reminders and assistant history tables.
- Made the legacy repair migrations safe when their tables already exist.
- Added a follow-up migration that restores missing table schemas and supports delivery records for either tasks or reminders.
- Added database constraints for delivery source and status.
- Added isolated SQLite test configuration so API tests do not touch a developer's PostgreSQL database.
- Normalized task/reminder due timestamps to UTC at the API boundary.
- Fixed refresh-token expiry comparisons when the database returns a naive timestamp.

## Reminder scheduling and notifications

- Connected the scheduler to both task deadlines and reminder occurrences.
- Added one-time and recurring reminder delivery.
- Daily, weekly, and monthly recurrence advances only after a successful email.
- Monthly recurrence clamps dates such as January 31 to the final day of February.
- Added a 24-hour catch-up window for missed notifications.
- Prevented repeated sends for the same occurrence using delivery uniqueness.
- Added stale-send recovery, up to three automatic attempts, and a manual retry endpoint.
- Ensured disabled automation and completed/paused/cancelled items are not sent.
- Added SMTP configuration validation and local Gmail App Password guidance.

## AI and productivity

- Replaced the invalid default AI model identifier with a configurable model default.
- Loaded AI and SMTP configuration through application settings so values in `backend/.env` are actually used.
- Kept smart planning usable without an AI key through deterministic priority/deadline scheduling.
- Validated recurring reminders require a due date.
- Corrected date/time handling for reminder entry and planning.

## Frontend

- Centralized API requests and added one automatic refresh-token retry after a 401.
- Updated dashboard navigation to point to working routes.
- Replaced outdated dashboard placeholder text with account-backed task/reminder/progress values.
- Added reminder automation access and failed-delivery retry controls.
- Corrected local-date handling for daily plans and time-zone-aware reminder entry.

## Verification

- Backend tests: **47 passed** in this review environment.
- Frontend TypeScript compilation: passed.
- Alembic history: one head, `a9c3f6d8e210`.
- Full Vite bundle was not produced in this Linux review container because the ZIP's prebundled `node_modules` did not include Linux native optional bindings. The corrected ZIP excludes `node_modules`; run `npm ci` on your machine before `npm run build`.

## Existing database data

Some previously applied migration revisions had already dropped reminders and assistant history. The new migration restores the missing table schemas, but it cannot recover rows already deleted from a database. Restore those rows from a PostgreSQL backup if you have one.
