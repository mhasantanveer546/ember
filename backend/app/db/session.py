"""
Ember Backend — Database Session

Sets up the SQLAlchemy engine (connection pool to Postgres/Neon) and a
session factory. get_db() is a FastAPI dependency that provides one
database session per request, and guarantees it's closed afterward
regardless of whether the request succeeded or raised.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# SQLite-specific engine configuration. Two separate gotchas here, both
# ONLY relevant to SQLite (Neon/Postgres is unaffected — production
# never takes this branch):
#
#   1. check_same_thread=False: SQLite by default only allows a
#      connection to be used from the thread that created it. FastAPI's
#      TestClient may call route functions from a different thread than
#      the one that set up the engine, so this needs to be relaxed for
#      tests to work at all.
#
#   2. poolclass=StaticPool for ":memory:" specifically: an in-memory
#      SQLite database exists ONLY within a single connection — a new
#      connection gets a completely separate, empty database. Without
#      forcing the whole engine onto a single shared connection
#      (StaticPool), tables created via one connection would be
#      invisible to the next, causing confusing "no such table" errors
#      that only manifest under the test suite.
_connect_args: dict = {}
_engine_kwargs: dict = {"pool_pre_ping": True}

if settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    if ":memory:" in settings.database_url:
        _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(settings.database_url, connect_args=_connect_args, **_engine_kwargs)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    """
    SQLite does NOT enforce foreign key constraints by default, unlike
    Postgres — ON DELETE CASCADE / SET NULL declared in our models would
    silently be a no-op at the database level on SQLite otherwise. This
    only matters for the test suite (which uses SQLite); real Neon
    Postgres already enforces these correctly without any extra step.
    Without this, cascade-delete tests could pass for the wrong reason
    (relying only on SQLAlchemy's in-Python ORM-level cascade logic,
    which wouldn't catch a mistake in the actual FK constraint itself).
    """
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class every SQLAlchemy model (Phase 2.1) will inherit from."""

    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields one Session per request, closing it
    afterward. Usage in a route:

        @app.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()