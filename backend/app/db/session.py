"""
Ember Backend — Database Session

Sets up the SQLAlchemy engine (connection pool to Postgres/Neon) and a
session factory. get_db() is a FastAPI dependency that provides one
database session per request, and guarantees it's closed afterward
regardless of whether the request succeeded or raised.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

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