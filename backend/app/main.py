"""
Ember Backend — Application Entrypoint

Run locally with:
    uvicorn app.main:app --reload

Interactive docs available at /docs once running.
"""

import json

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.folders import router as folders_router
from app.api.index import router as index_router
from app.api.search import router as search_router
from app.api.workspaces import router as workspaces_router
from app.core import metrics
from app.core.config import settings
from app.core.logging_config import configure_logging, init_error_tracking
from app.core.observability import RequestContextMiddleware, metrics_authorized
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.session import get_db

configure_logging(
    settings.log_level,
    json_logs=settings.log_json if settings.log_json is not None else settings.environment == "production",
)
init_error_tracking(settings.sentry_dsn, settings.environment)

# Interactive docs are handy in development but expose the full API surface;
# turn them off in production unless ENABLE_DOCS=true.
_docs_on = settings.enable_docs if settings.enable_docs is not None else settings.environment != "production"
app = FastAPI(
    title="Ember API",
    version="0.1.0",
    docs_url="/docs" if _docs_on else None,
    redoc_url=None,
    openapi_url="/openapi.json" if _docs_on else None,
)

# Added BEFORE CORS so CORS is the outer layer: even a 413 from the size
# guard then carries CORS headers and the browser can read the error.
app.add_middleware(SecurityHeadersMiddleware)
# Between security headers and CORS: sees every request, and its 500s still get CORS headers.
app.add_middleware(RequestContextMiddleware)

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

@app.get("/metrics", include_in_schema=False)
def metrics_endpoint(format: str = "prometheus", authorization: str | None = Header(default=None)) -> Response:
    if not metrics_authorized(authorization, settings.metrics_token, settings.environment):
        # 404, not 401: don't advertise that the endpoint exists to anonymous callers.
        raise HTTPException(status_code=404, detail="Not found")
    if format == "json":
        return Response(json.dumps(metrics.snapshot()), media_type="application/json")
    return Response(metrics.render_prometheus(), media_type="text/plain; version=0.0.4")
