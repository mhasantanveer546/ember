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
    # "local" (development), "s3" (any S3-compatible service) or "gcs" (Google Cloud Storage).
    storage_backend: str = "local"
    local_storage_path: str = "./storage_data"
    s3_endpoint_url: str = ""  # e.g. https://<project>.supabase.co/storage/v1/s3 ; empty = AWS
    s3_bucket: str = ""
    s3_region: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    # Google Cloud Storage (STORAGE_BACKEND=gcs). Auth is the runtime service
    # account via Application Default Credentials — no key file or secret needed.
    gcs_bucket: str = ""

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

    # --- Phase 8: hardening ---
    # Fixed-window rate limiting backed by Redis. Fails open if Redis is down.
    rate_limit_enabled: bool = True
    # Only trust X-Forwarded-For when the API sits behind a proxy you control
    # (Render, Hugging Face, Cloud Run). If left false behind a proxy every
    # client looks like the proxy's IP; if true without a proxy clients can
    # spoof their IP and dodge the limiter.
    trust_proxy_headers: bool = False
    # --- Phase 11: observability ---
    log_level: str = "INFO"
    log_json: bool | None = None  # None = JSON in production, readable text otherwise
    sentry_dsn: str = ""  # optional; also `pip install sentry-sdk`
    metrics_token: str = ""  # bearer token for GET /metrics (required in production)

    # Swagger/OpenAPI endpoints. Unset = on in development, off in production.
    enable_docs: bool | None = None

    @model_validator(mode="after")
    def _check_production_safety(self) -> "Settings":
        if self.storage_backend not in ("local", "s3", "gcs"):
            raise ValueError("STORAGE_BACKEND must be 'local', 's3' or 'gcs'")
        if self.storage_backend == "gcs" and not self.gcs_bucket:
            raise ValueError("STORAGE_BACKEND=gcs requires GCS_BUCKET")
        if self.storage_backend == "s3" and not (
            self.s3_bucket and self.s3_access_key_id and self.s3_secret_access_key
        ):
            raise ValueError("STORAGE_BACKEND=s3 requires S3_BUCKET, S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY")
        if self.environment == "production":
            if len(self.jwt_secret) < 32:
                raise ValueError("In production JWT_SECRET must be at least 32 characters")
            if self.jwt_secret.lower().startswith(("change", "test", "secret", "dev")):
                raise ValueError("In production JWT_SECRET looks like a placeholder; generate a random one")
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