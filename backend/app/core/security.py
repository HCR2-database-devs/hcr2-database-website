import base64
import hashlib
import hmac
import json
import time
from typing import Any


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def verify_wc_token(jwt: str, secret: str) -> dict[str, Any] | None:
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
    except (ValueError, json.JSONDecodeError):
        return None

    if not isinstance(decoded, dict):
        return None
    if not decoded.get("sub") or not decoded.get("exp"):
        return None
    if int(decoded["exp"]) < int(time.time()):
        return None
    return decoded


def is_allowed_admin(discord_id: str | None, allowed_discord_ids: list[str]) -> bool:
    if discord_id is None:
        return False
    return str(discord_id) in allowed_discord_ids

