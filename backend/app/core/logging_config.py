"""
Ember Backend — Structured logging (Phase 11)

One JSON object per line (easy for Cloud Logging / Loki / `jq` to parse) with a
request_id stamped on every record emitted while a request is being handled, so
you can pull every log line of one failing request with a single filter.
Locally (LOG_JSON=false) a readable single-line format is used instead.
"""

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        for key, value in record.__dict__.items():  # logger.info("x", extra={"duration_ms": 3})
            if key not in _RESERVED and not key.startswith("_"):
                entry[key] = value
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


class _PlainFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        extras = {k: v for k, v in record.__dict__.items() if k not in _RESERVED and not k.startswith("_")}
        base = f"{self.formatTime(record, '%H:%M:%S')} {record.levelname:<7} [{request_id_var.get()[:8]}] {record.name}: {record.getMessage()}"
        if extras:
            base += " " + " ".join(f"{k}={v}" for k, v in extras.items())
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_logs else _PlainFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    # uvicorn's own access log duplicates our per-request line; keep its errors.
    logging.getLogger("uvicorn.access").disabled = True
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers[:] = []
        lg.propagate = True


def init_error_tracking(dsn: str, environment: str) -> bool:
    """Optional Sentry. Install `sentry-sdk` and set SENTRY_DSN to enable; otherwise a no-op."""
    if not dsn:
        return False
    try:
        import sentry_sdk
    except ImportError:
        logging.getLogger("ember").warning("SENTRY_DSN is set but sentry-sdk is not installed; error tracking disabled")
        return False
    sentry_sdk.init(dsn=dsn, environment=environment, send_default_pii=False, traces_sample_rate=0.0)
    return True
