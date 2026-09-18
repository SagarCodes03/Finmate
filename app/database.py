"""SQLAlchemy engine, session, and FastAPI database dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection: object, _: object) -> None:
    if settings.database_url.startswith("sqlite"):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")  # type: ignore[attr-defined]


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def ensure_demo_context_schema() -> None:
    """Apply the additive SQLite field used by custom simulated context."""
    if not settings.database_url.startswith("sqlite"):
        return
    columns = {column["name"] for column in inspect(engine).get_columns("business_profiles")}
    if "recovery_allowed" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE business_profiles ADD COLUMN recovery_allowed BOOLEAN NOT NULL DEFAULT 1"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
