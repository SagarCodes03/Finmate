from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models  # Registers all SQLAlchemy models before table creation.
from app.api.v1.router import api_router
from app.config import get_settings
from app.context.seed import seed_demo_customers
from app.database import Base, SessionLocal, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_customers(db)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs"}
