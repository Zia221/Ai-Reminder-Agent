# AI Reminder Agent — Security Notes

## Implemented protections

- Passwords are hashed with the configured `pwdlib` password-hashing backend.
- Access tokens are signed with a configured JWT secret.
- Refresh tokens are stored as hashes and rotated on refresh.
- Logout revokes the submitted refresh token.
- Authenticated API routes use the current user's ID and scope records by ownership.
- Input schemas validate fields, status values, and time zones.
- AI-generated task proposals require explicit user confirmation.
- Local environment files are ignored by Git.

## Local configuration

- Set a random `JWT_SECRET_KEY` in `backend/.env`.
- Do not commit `.env`, database credentials, SMTP credentials, or OpenAI API keys.
- Gmail SMTP requires an App Password. This implementation does not use Gmail OAuth and does not read the user's inbox.
- Set the CORS origin list to only the local frontend URLs you use.

## Remaining hardening before public deployment

- Password reset and account recovery
- Rate limiting and abuse protection
- HTTPS and production secret management
- Audit logging and operational monitoring
- Account deletion and data-export workflows
- SMTP provider-specific credential management and delivery monitoring
- Multi-process background worker infrastructure

This project is intended for local development and testing. Do not treat it as production-ready solely because the local tests pass.
