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

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


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


# pool_pre_ping=True: checks each connection is still alive before use.
# Matters especially for Neon, which may close idle connections — without
# this, the first query on a stale connection would fail outright.

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