import base64
import binascii
import hashlib
import hmac
import json
import math
import time
from typing import Any


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def verify_wc_token(jwt: str, secret: str) -> dict[str, Any] | None:
    if not isinstance(jwt, str) or not isinstance(secret, str) or not secret:
        return None
    parts = jwt.split(".")
    if len(parts) != 3:
        return None

    header, payload, signature = parts
    signed_data = f"{header}.{payload}".encode()
    expected = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), signed_data, hashlib.sha256).digest()
    ).decode().rstrip("=")

    if not hmac.compare_digest(expected, signature.rstrip("=")):
        return None

    try:
        decoded = json.loads(_base64url_decode(payload))
    except (ValueError, TypeError, binascii.Error, json.JSONDecodeError):
        return None

    if not isinstance(decoded, dict):
        return None
    subject = decoded.get("sub")
    if isinstance(subject, int) and not isinstance(subject, bool):
        subject = str(subject)
    if not isinstance(subject, str) or not subject.strip():
        return None
    expiration = decoded.get("exp")
    if isinstance(expiration, bool) or not isinstance(expiration, (int, float)):
        return None
    try:
        if not math.isfinite(expiration) or expiration <= time.time():
            return None
    except (OverflowError, TypeError, ValueError):
        return None
    return decoded


def is_allowed_admin(discord_id: str | None, allowed_discord_ids: list[str]) -> bool:
    if discord_id is None:
        return False
    return str(discord_id) in allowed_discord_ids

