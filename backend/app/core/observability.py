"""
Ember Backend — Request context middleware + /metrics (Phase 11)

For every HTTP request: assign/propagate a request id (X-Request-ID), time it,
record latency + status metrics keyed by the ROUTE TEMPLATE (never the raw
URL — /workspaces/{id}/search, not one series per UUID), emit one structured
log line, and turn an unhandled exception into a logged JSON 500 that carries
the request id so a user's bug report can be matched to the traceback.
"""

import hmac
import json
import logging
import re
import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core import metrics
from app.core.logging_config import request_id_var
from app.core.security_headers import _with_security

log = logging.getLogger("ember.request")
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
_QUIET_PATHS = {"/health", "/metrics"}


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = dict(scope.get("headers") or []).get(b"x-request-id", b"").decode("latin-1")
        rid = incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex  # never echo untrusted junk into logs
        token = request_id_var.set(rid)
        start = time.perf_counter()
        status_holder = {"code": 500}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
                message["headers"] = list(message.get("headers") or []) + [(b"x-request-id", rid.encode())]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:  # noqa: BLE001 — last line of defence; never leak a traceback to the client
            log.exception("unhandled exception", extra={"method": scope["method"], "path": scope["path"]})
            body = json.dumps({"detail": "Internal server error.", "request_id": rid}).encode()
            headers = _with_security(
                [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode()), (b"x-request-id", rid.encode())]
            )
            status_holder["code"] = 500
            await send({"type": "http.response.start", "status": 500, "headers": headers})
            await send({"type": "http.response.body", "body": body})
        finally:
            duration = time.perf_counter() - start
            path = scope["path"]
            if path not in _QUIET_PATHS:
                route = getattr(scope.get("route"), "path", None) or "unmatched"
                code = status_holder["code"]
                labels = {"method": scope["method"], "route": route}
                metrics.observe("ember_http_request_seconds", duration, labels)
                metrics.inc("ember_http_requests_total", {**labels, "status": f"{code // 100}xx"})
                if code >= 500:
                    metrics.inc("ember_http_errors_total", labels)
                level = logging.ERROR if code >= 500 else logging.WARNING if code == 429 else logging.INFO
                log.log(
                    level,
                    "request",
                    extra={"method": scope["method"], "route": route, "status": code, "duration_ms": round(duration * 1000, 1)},
                )
            request_id_var.reset(token)


def metrics_authorized(authorization: str | None, token: str, environment: str) -> bool:
    """
    /metrics reveals traffic patterns, so it is not public in production:
    require `Authorization: Bearer <METRICS_TOKEN>`; with no token configured
    it is open in development only.
    """
    if not token:
        return environment != "production"
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    return hmac.compare_digest(supplied.encode(), token.encode())
