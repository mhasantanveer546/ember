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

from pydantic import model_validator
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
    # Development convenience: run document-processing jobs immediately,
    # inside the API process, instead of waiting for a separate worker.
    # Handy on Windows (RQ's normal worker needs os.fork). Never use in
    # production: uploads would block until processing finishes.
    run_jobs_inline: bool = False

    # --- Storage ---
    # "local" (development) or "s3" (any S3-compatible service; production).
    storage_backend: str = "local"
    local_storage_path: str = "./storage_data"
    s3_endpoint_url: str = ""  # e.g. https://<project>.supabase.co/storage/v1/s3 ; empty = AWS
    s3_bucket: str = ""
    s3_region: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    # --- App ---
    environment: str = "development"
    api_base_url: str = "http://localhost:8000"

    # --- CORS (Phase 6): browser origins allowed to call this API.
    # Comma-separated in the environment, e.g.
    #   CORS_ORIGINS=http://localhost:3000,https://ember.example.com
    cors_origins: str = "http://localhost:3000"

    # Set to false on a public deployment once your own account exists, so
    # strangers can't create accounts (and consume your storage/quota).
    allow_registration: bool = True

    @model_validator(mode="after")
    def _check_production_safety(self) -> "Settings":
        if self.storage_backend not in ("local", "s3"):
            raise ValueError("STORAGE_BACKEND must be 'local' or 's3'")
        if self.storage_backend == "s3" and not (
            self.s3_bucket and self.s3_access_key_id and self.s3_secret_access_key
        ):
            raise ValueError("STORAGE_BACKEND=s3 requires S3_BUCKET, S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY")
        if self.environment == "production":
            if len(self.jwt_secret) < 32:
                raise ValueError("In production JWT_SECRET must be at least 32 characters")
            if "localhost" in self.cors_origins:
                raise ValueError("In production CORS_ORIGINS must list your real web origin(s), not localhost")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# Instantiated once, at import time. FastAPI's dependency injection
# (Phase 2.2 onward) will use a small get_settings() wrapper around this
# so it can also be overridden in tests.
settings = Settings()