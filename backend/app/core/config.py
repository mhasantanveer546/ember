"""
Ember Backend — Configuration

Loads settings from environment variables (populated from .env locally,
and from real environment variables / Secret Manager in production —
see docs/DEPLOYMENT.md, written in Phase 9).

Uses pydantic-settings so that:
  - every setting is typed and validated at startup (fail fast if
    DATABASE_URL is missing, rather than failing confusingly later)
  - .env is only ever read here, in one place — no os.environ.get()
    scattered through the codebase
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    database_url: str

    # --- Auth (hand-rolled JWT) ---
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # --- Redis / RQ ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Storage ---
    storage_backend: str = "local"
    local_storage_path: str = "./storage_data"

    # --- App ---
    environment: str = "development"
    api_base_url: str = "http://localhost:8000"


# Instantiated once, at import time. FastAPI's dependency injection
# (Phase 2.2 onward) will use a small get_settings() wrapper around this
# so it can also be overridden in tests.
settings = Settings()