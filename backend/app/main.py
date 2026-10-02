"""
Ember Backend — Application Entrypoint

Run locally with:
    uvicorn app.main:app --reload

Interactive docs available at /docs once running.
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.folders import router as folders_router
from app.api.index import router as index_router
from app.api.search import router as search_router
from app.api.workspaces import router as workspaces_router
from app.core.config import settings
from app.db.session import get_db

app = FastAPI(title="Ember API", version="0.1.0")

# Explicit origin allow-list (never "*" with credentials). Bearer tokens
# travel in the Authorization header, so cookies/credentials aren't needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(folders_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(index_router)


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