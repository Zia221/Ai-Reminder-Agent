from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Reminder Agent API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://reminder_app:change-me@localhost:5432/ai_reminder_agent"

    jwt_secret_key: str = Field(
        default="dev-only-change-this-secret-before-running",
        min_length=32,
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=365)

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-luna"

    reminder_scheduler_enabled: bool = True

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @model_validator(mode="after")
    def validate_production_secret(self):
        if self.environment.lower() in {"production", "prod"} and (
            self.jwt_secret_key == "dev-only-change-this-secret-before-running"
        ):
            raise ValueError("JWT_SECRET_KEY must be set to a secure production secret.")
        return self
    @property
    def smtp_configured(self) -> bool:
        placeholders = {
        "",
        "your_gmail@gmail.com",
        "your_gmail_app_password",
        "replace_me",
    }

        username = self.smtp_username.strip()
        password = self.smtp_password.strip()

        return (
        username.lower() not in placeholders
        and password.lower() not in placeholders
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
