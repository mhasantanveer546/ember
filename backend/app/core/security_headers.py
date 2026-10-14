"""
Ember Backend — Security headers + request size guard (Phase 8)

Pure ASGI middleware (not BaseHTTPMiddleware) so it doesn't buffer
streaming bodies. Adds defensive headers to every response and rejects
oversized request bodies early, based on Content-Length, before FastAPI
spends memory parsing them.
"""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings

# Upload cap (25 MB) + multipart overhead. Everything else is tiny JSON.
MAX_BODY_BYTES = 26 * 1024 * 1024


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        raw_len = headers.get(b"content-length")
        if raw_len is not None:
            try:
                too_big = int(raw_len) > MAX_BODY_BYTES
            except ValueError:
                too_big = True
            if too_big:
                body = b'{"detail":"Request body too large."}'
                await send({"type": "http.response.start", "status": 413, "headers": _with_security(
                    [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())])})
                await send({"type": "http.response.body", "body": body})
                return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                message["headers"] = _with_security(list(message.get("headers") or []))
            await send(message)

        await self.app(scope, receive, send_wrapper)


def _with_security(existing: list[tuple[bytes, bytes]]) -> list[tuple[bytes, bytes]]:
    have = {k.lower() for k, _ in existing}
    extra = {
        b"x-content-type-options": b"nosniff",
        b"x-frame-options": b"DENY",
        b"referrer-policy": b"no-referrer",
        b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
        # The API serves JSON only; lock it down completely.
        b"content-security-policy": b"default-src 'none'; frame-ancestors 'none'",
        b"cache-control": b"no-store",
    }
    if settings.environment == "production":
        extra[b"strict-transport-security"] = b"max-age=63072000; includeSubDomains"
    return existing + [(k, v) for k, v in extra.items() if k not in have]
