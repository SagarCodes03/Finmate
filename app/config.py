"""Application configuration loaded from environment variables."""

from functools import lru_cache
from os import getenv


class Settings:
    def __init__(self) -> None:
        self.app_name = getenv("APP_NAME", "FinMate API")
        self.environment = getenv("ENVIRONMENT", "development")
        self.database_url = getenv("DATABASE_URL", "sqlite:///./finmate.db")
        self.api_v1_prefix = getenv("API_V1_PREFIX", "/api/v1")


@lru_cache
def get_settings() -> Settings:
    return Settings()
