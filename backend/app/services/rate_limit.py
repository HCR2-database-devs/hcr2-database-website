"""Shared fixed-window rate limiting for database-backed endpoints.

Extracted from ``app.services.public_submission_service`` so Phase 4 can apply
the same rules without duplicating the HMAC-keyed, upsert-based counter. The
submission service keeps its own private copy so existing Phase 1-3 behaviour
is untouched.

The window is a fixed one: a row is created on first use and its counter is
reset when the window has elapsed. That is adequate for the abuse patterns
this guards against (code rerolls, request spam) and matches the existing
``public_submission_rate_limit`` table shape.
"""

import hashlib
import hmac
from dataclasses import dataclass
from typing import Any

#: Table used to persist counters. Phase 4 creates it in migration
#: 20261016_add_hcr2_account_linking.
RATE_LIMIT_TABLE = "community_action_rate_limit"


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    """Outcome of a single rate-limit check."""

    allowed: bool
    retry_after: int = 0
    remaining: int = 0


def rate_limit_key(scope: str, value: str, secret: str | None) -> str:
    """Return a storage key that does not leak the raw value.

    Keys are HMACed so the table never contains Discord IDs or IP addresses in
    the clear. Without a secret the value is still hashed, just not keyed.
    """
    message = f"{scope}:{value}".encode()
    if secret:
        digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    else:
        digest = hashlib.sha256(message).hexdigest()
    return f"{scope}:{digest}"


def consume_rate_limit(
    cursor: Any,
    *,
    table: str,
    scope: str,
    value: str,
    limit: int,
    window_seconds: int,
    secret: str | None = None,
) -> RateLimitResult:
    """Consume one unit from the caller's window, returning whether it is allowed.

    The check and the increment happen in a single upsert so two concurrent
    requests cannot both slip through on the same remaining allowance. Must be
    called inside a transaction the caller controls.
    """
    if limit <= 0:
        return RateLimitResult(allowed=True, remaining=0)

    key = rate_limit_key(scope, value, secret)
    cursor.execute(
        f"""
        INSERT INTO {table} (rate_key, request_count, window_started_at)
        VALUES (%(rate_key)s, 1, CURRENT_TIMESTAMP)
        ON CONFLICT (rate_key) DO UPDATE SET
            request_count = CASE
                WHEN {table}.window_started_at
                     <= CURRENT_TIMESTAMP - make_interval(secs => %(window_seconds)s)
                THEN 1
                ELSE {table}.request_count + 1
            END,
            window_started_at = CASE
                WHEN {table}.window_started_at
                     <= CURRENT_TIMESTAMP - make_interval(secs => %(window_seconds)s)
                THEN CURRENT_TIMESTAMP
                ELSE {table}.window_started_at
            END
        RETURNING request_count,
                  GREATEST(
                      0,
                      EXTRACT(EPOCH FROM (
                          {table}.window_started_at
                          + make_interval(secs => %(window_seconds)s)
                          - CURRENT_TIMESTAMP
                      ))
                  )::int AS retry_after_seconds
        """,
        {"rate_key": key, "window_seconds": max(window_seconds, 1)},
    )
    row = cursor.fetchone()
    if row is None:
        return RateLimitResult(allowed=True, remaining=0)

    used = int(row["request_count"])
    if used > limit:
        return RateLimitResult(allowed=False, retry_after=max(int(row["retry_after_seconds"]), 1))
    return RateLimitResult(allowed=True, remaining=limit - used)


def purge_expired_windows(cursor: Any, *, table: str = RATE_LIMIT_TABLE) -> int:
    """Delete counter rows whose window has long elapsed. Returns row count."""
    cursor.execute(
        f"DELETE FROM {table} WHERE window_started_at < CURRENT_TIMESTAMP - INTERVAL '2 days'"
    )
    return int(cursor.rowcount)