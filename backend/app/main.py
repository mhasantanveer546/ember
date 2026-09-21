"""
Ember Backend — Application Entrypoint

Run locally with:
    uvicorn app.main:app --reload

Interactive docs available at /docs once running.
"""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

app = FastAPI(title="Ember API", version="0.1.0")


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Basic liveness check — confirms the API process itself is up.
    Does NOT check the database; see /health/db for that.
    """
    return {"status": "ok"}


@app.get("/health/db")
def health_check_db(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Confirms the API can actually reach the database (Neon), not just
    that the process is running. Runs the simplest possible query.
    """
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}