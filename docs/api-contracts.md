
# AI Reminder Agent — API Contracts

## 1. API Version

All application endpoints will initially use:

/api/v1

## 2. Authentication

POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout

GET /api/v1/users/me

## 3. Tasks

GET /api/v1/tasks
POST /api/v1/tasks
GET /api/v1/tasks/{task_id}
PATCH /api/v1/tasks/{task_id}
DELETE /api/v1/tasks/{task_id}

## 4. Reminders

GET /api/v1/reminders
POST /api/v1/reminders
GET /api/v1/reminders/{reminder_id}
PATCH /api/v1/reminders/{reminder_id}
DELETE /api/v1/reminders/{reminder_id}

POST /api/v1/reminders/{reminder_id}/pause
POST /api/v1/reminders/{reminder_id}/resume

## 5. Daily Progress

GET /api/v1/progress
POST /api/v1/progress
GET /api/v1/progress/{entry_id}
PATCH /api/v1/progress/{entry_id}
DELETE /api/v1/progress/{entry_id}

## 6. Reports

GET /api/v1/reports
POST /api/v1/reports/weekly
GET /api/v1/reports/{report_id}
GET /api/v1/reports/{report_id}/download

## 7. Projects and Skills

GET /api/v1/projects
POST /api/v1/projects
PATCH /api/v1/projects/{project_id}

GET /api/v1/skills
POST /api/v1/skills

POST /api/v1/project-recommendations
GET /api/v1/project-recommendations

## 8. AI Assistant and Planner

POST /api/v1/assistant/chat
GET /api/v1/goals
POST /api/v1/goals
PATCH /api/v1/goals/{goal_id}

## 9. Gmail Integration

GET /api/v1/integrations/gmail
POST /api/v1/integrations/gmail/connect
POST /api/v1/integrations/gmail/disconnect

## 10. API Rules

- Validate all request bodies.
- Authenticate protected endpoints.
- Check ownership before reading or modifying records.
- Use consistent response and error formats.
- Apply pagination to potentially large lists.
- Avoid returning secrets or sensitive OAuth credentials.
- Use idempotency controls where duplicate operations are dangerous.

Note: These are planned API contracts, not implemented endpoints.
Request schemas, response schemas, and status codes will be finalized
during implementation.
