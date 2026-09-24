"""
Ember Backend — Token Denylist

A JWT is valid until it expires — there's no built-in way to invalidate
one early. This denylist is the workaround: on logout or refresh-token
rotation, we record the token's `jti` (unique ID) in Redis with a TTL
matching its remaining lifetime. get_current_user (api/deps.py) checks
this denylist on every request.

This is a real limitation of hand-rolled JWT worth being explicit about:
revocation now depends on Redis being up and reachable on every request
that checks it — a managed auth provider would typically handle this
differently (e.g. shorter-lived tokens, or a different revocation
mechanism). Accepted trade-off here since the goal is learning the
mechanics, not avoiding all of JWT's rough edges.
"""

import redis


def _denylist_key(jti: str) -> str:
    return f"denylist:{jti}"


def add_to_denylist(redis_client: redis.Redis, jti: str, ttl_seconds: int) -> None:
    """Mark a token's jti as revoked, expiring automatically after ttl_seconds."""
    redis_client.set(_denylist_key(jti), "1", ex=ttl_seconds)


def is_denylisted(redis_client: redis.Redis, jti: str) -> bool:
    return bool(redis_client.exists(_denylist_key(jti)))