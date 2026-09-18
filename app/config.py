"""Application configuration loaded from environment variables."""

from functools import lru_cache
from os import getenv


class Settings:
    def __init__(self) -> None:
        self.app_name = getenv("APP_NAME", "FinMate API")
        self.environment = getenv("ENVIRONMENT", "development")
        self.database_url = getenv("DATABASE_URL", "sqlite:///./finmate.db")
        self.api_v1_prefix = getenv("API_V1_PREFIX", "/api/v1")
        self.n8n_journey_webhook_url = getenv(
            "N8N_JOURNEY_WEBHOOK_URL",
            "http://localhost:5678/webhook/finmate-journey",
        )
        self.n8n_request_timeout_seconds = float(getenv("N8N_REQUEST_TIMEOUT_SECONDS", "30"))
        self.cors_origins = tuple(
            origin.strip()
            for origin in getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if origin.strip()
        )
        self.gemini_api_key = getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model = getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
