"""Seed SQLite with deterministic, simulated FinMate demo customers."""

import app.models
from app.context.seed import seed_demo_customers
from app.database import Base, SessionLocal, engine


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_customers(db)
    print("Seeded simulated FinMate demo customers.")
