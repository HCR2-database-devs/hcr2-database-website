import base64
import hashlib
import hmac
import json
import time

from app.core.security import is_allowed_admin, verify_wc_token


def _base64url_json(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _signed_token(payload: dict[str, object], secret: str) -> str:
    header = _base64url_json({"alg": "HS256", "typ": "JWT"})
    body = _base64url_json(payload)
    data = f"{header}.{body}".encode()
    signature = base64.urlsafe_b64encode(
        hmac.new(secret.encode(), data, hashlib.sha256).digest()
    ).decode().rstrip("=")
    return f"{header}.{body}.{signature}"


def test_verify_wc_token_accepts_valid_hmac_token() -> None:
    secret = "test-secret"
    token = _signed_token(
        {"sub": "123", "username": "admin", "exp": int(time.time()) + 60},
        secret,
    )

    payload = verify_wc_token(token, secret)

    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["username"] == "admin"


def test_verify_wc_token_rejects_invalid_signature() -> None:
    token = _signed_token({"sub": "123", "exp": int(time.time()) + 60}, "good-secret")

    assert verify_wc_token(token, "bad-secret") is None


def test_verify_wc_token_rejects_expired_token() -> None:
    token = _signed_token({"sub": "123", "exp": int(time.time()) - 60}, "test-secret")

    assert verify_wc_token(token, "test-secret") is None


def test_is_allowed_admin_uses_discord_allowlist() -> None:
    assert is_allowed_admin("123", ["123", "456"]) is True
    assert is_allowed_admin("999", ["123", "456"]) is False
    assert is_allowed_admin(None, ["123", "456"]) is False
