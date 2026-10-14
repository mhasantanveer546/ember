"""
Ember Backend — Rate limiting (Phase 8)

Fixed-window counters in Redis: INCR a per-(bucket, client) key and set its
expiry on first hit. Simple, cheap, and good enough to stop password
guessing, signup spam and upload floods. (A sliding window or token bucket
is smoother at window edges but needs more Redis round trips.)

Design choices:
  * Fails OPEN: if Redis is unreachable the request proceeds. Auth already
    depends on Redis for the denylist; a limiter outage shouldn't also take
    the whole API down. Failures are logged.
  * Keys are namespaced `rl:{bucket}:{client}` and expire on their own.
  * Client identity = IP (via X-Forwarded-For only if TRUST_PROXY_HEADERS),
    optionally combined with a per-request discriminator such as the login
    email, so one attacker can't lock out everyone behind a shared IP and a
    distributed attacker still can't hammer a single account.
"""

import logging
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.redis_client import get_redis_client

log = logging.getLogger("ember.ratelimit")


def client_ip(request: Request) -> str:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Left-most entry is the original client; proxies append theirs.
            return forwarded.split(",")[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def hit(redis_client, bucket: str, ident: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    """Count one hit. Returns (allowed, retry_after_seconds)."""
    key = f"rl:{bucket}:{ident}"
    try:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, window_seconds)
        if count > limit:
            ttl = redis_client.ttl(key)
            return False, max(int(ttl), 1) if ttl and ttl > 0 else window_seconds
    except Exception:  # noqa: BLE001 — limiter must never take the API down
        log.warning("rate limiter unavailable, failing open", exc_info=True)
    return True, 0


def rate_limit(bucket: str, limit: int, window_seconds: int) -> Callable:
    """Dependency factory: `dependencies=[Depends(rate_limit("login", 10, 60))]`."""

    def dependency(request: Request, redis_client=Depends(get_redis_client)) -> None:
        if not settings.rate_limit_enabled:
            return
        allowed, retry_after = hit(redis_client, bucket, client_ip(request), limit, window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down and try again shortly.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency


def enforce(request: Request, redis_client, bucket: str, discriminator: str, limit: int, window_seconds: int) -> None:
    """Imperative form for limits keyed by something in the request body (e.g. login email)."""
    if not settings.rate_limit_enabled:
        return
    ident = f"{client_ip(request)}:{discriminator}"
    allowed, retry_after = hit(redis_client, bucket, ident, limit, window_seconds)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please wait and try again.",
            headers={"Retry-After": str(retry_after)},
        )
