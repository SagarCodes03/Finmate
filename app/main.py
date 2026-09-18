from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load local development configuration before importing app modules. app.database
# creates the cached Settings instance at import time.
load_dotenv()
load_dotenv(".venv/.env")

import app.models  # Registers all SQLAlchemy models before table creation.
from app.api.v1.router import api_router
from app.config import get_settings
from app.context.seed import seed_demo_customers
from app.database import Base, SessionLocal, engine, ensure_demo_context_schema

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_demo_context_schema()
    with SessionLocal() as db:
        seed_demo_customers(db)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    # The simulated-information confirmation is a cross-origin JSON PATCH
    # from the Vite UI.  Allow its preflight as well as journey POSTs.
    allow_methods=["POST", "PATCH"],
    allow_headers=["Content-Type"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/docs"}
