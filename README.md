# FinMate API

The initial backend foundation for FinMate, built with FastAPI and SQLite.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Test

```powershell
pytest
```

Copy `.env.example` to `.env` to customize configuration. The default database is a local `finmate.db` SQLite file.
