import json
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api import dependencies
from app.core.config import Settings, get_settings
from app.core.network import canonicalize_client_ip, trusted_client_ip
from app.core.security import verify_wc_token
from app.db.session import DatabaseNotConfigured
from app.main import create_app
from app.services.hcaptcha import HCAPTCHA_VERIFY_URL, verify_hcaptcha
from app.services.public_submission_service import PublicSubmissionService, SubmissionResult
from app.services.submission_identity import SubmissionIdentity, resolve_submission_identity


def _valid_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "h_captcha_response": "ok",
        "mapId": "1",
        "vehicleId": "1",
        "distance": "12345",
        "playerName": "Demo Driver",
        "playerCountry": "FI",
        "tuningParts": ["Wings", "Coin Boost", "Magnet"],
    }
    payload.update(overrides)
    return payload


class _Cursor:
    def __init__(
        self,
        rate_counts: list[int] | None = None,
        account_id: int | None = 42,
        ban_row: dict[str, Any] | None = None,
    ) -> None:
        self.rate_counts = rate_counts or []
        self.account_id = account_id
        self.ban_row = ban_row
        self.row: dict[str, Any] | None = None
        self.queries: list[str] = []
        self.parameters: list[Any] = []

    def __enter__(self) -> "_Cursor":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def execute(self, query: str, parameters: Any = None) -> None:
        normalized = " ".join(query.split())
        self.queries.append(normalized)
        self.parameters.append(parameters)
        if "FROM community_user" in normalized:
            self.row = {"id": self.account_id} if self.account_id is not None else None
        elif "FROM ip_ban" in normalized:
            self.row = self.ban_row
        elif "public_submission_rate_limit" in normalized:
            count = self.rate_counts.pop(0) if self.rate_counts else 1
            self.row = {"request_count": count, "retry_after_seconds": 120}
        elif "MAX(distance)" in normalized:
            self.row = {"best_distance": None}
        else:
            self.row = None

    def fetchone(self) -> dict[str, Any] | None:
        return self.row


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor
        self.committed = False

    def __enter__(self) -> "_Connection":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def cursor(self) -> _Cursor:
        return self._cursor

    def commit(self) -> None:
        self.committed = True


def test_canonicalize_client_ip_maps_ipv4_mapped_ipv6() -> None:
    assert canonicalize_client_ip("::ffff:192.0.2.128") == "192.0.2.128"
    assert canonicalize_client_ip("2001:0db8::1") == "2001:db8::1"
    assert canonicalize_client_ip("not-an-ip") is None


def test_trusted_client_ip_ignores_forwarded_headers() -> None:
    request = SimpleNamespace(
        client=SimpleNamespace(host="192.0.2.10"),
        headers={"x-forwarded-for": "203.0.113.10", "cf-connecting-ip": "198.51.100.10"},
    )

    assert trusted_client_ip(request) == "192.0.2.10"


def test_verify_hcaptcha_uses_current_endpoint_and_optional_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class Response:
        status_code = 200

        def json(self) -> dict[str, bool]:
            return {"success": True}

    def fake_post(url: str, *, data: dict[str, str], timeout: float) -> Response:
        captured.update({"url": url, "data": data, "timeout": timeout})
        return Response()

    monkeypatch.setattr(httpx, "post", fake_post)

    assert verify_hcaptcha("token", "secret", "site", "192.0.2.10")
    assert captured["url"] == HCAPTCHA_VERIFY_URL
    assert captured["data"] == {
        "secret": "secret",
        "response": "token",
        "sitekey": "site",
        "remoteip": "192.0.2.10",
    }


def test_verify_hcaptcha_fails_closed_for_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Response:
        status_code = 200

        def json(self) -> Any:
            raise ValueError("invalid json")

    monkeypatch.setattr(httpx, "post", lambda *_args, **_kwargs: Response())

    assert verify_hcaptcha("token", "secret") is False


def test_verify_wc_token_rejects_non_numeric_expiration() -> None:
    import base64
    import hashlib
    import hmac
    import time

    payload = {"sub": "123", "exp": "tomorrow"}
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').decode().rstrip("=")
    signed = f"{header}.{encoded}".encode()
    signature = base64.urlsafe_b64encode(
        hmac.new(b"secret", signed, hashlib.sha256).digest()
    ).decode().rstrip("=")

    assert verify_wc_token(f"{header}.{encoded}.{signature}", "secret") is None
    assert int(time.time()) > 0


def test_resolve_submission_identity_uses_canonical_account_creation() -> None:
    class Auth:
        def status_from_cookie(self, cookie: str | None) -> dict[str, Any]:
            assert cookie == "token"
            return {"logged": True, "id": "123", "username": "driver", "avatar": "hash"}

    class Community:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def get_or_create(self, **kwargs: str | None) -> dict[str, int]:
            self.calls.append(kwargs)
            return {"id": 42}

    community = Community()
    request = SimpleNamespace(cookies={"WC_TOKEN": "token"})

    identity = resolve_submission_identity(request, Auth(), community)

    assert identity == SubmissionIdentity(community_user_id=42, discord_id="123")
    assert community.calls == [
        {
            "discord_id": "123",
            "discord_username": "driver",
            "discord_avatar": "hash",
        }
    ]


def test_disabled_identity_is_rejected_before_hcaptcha(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        PublicSubmissionService,
        "_verify_hcaptcha",
        lambda self, token: (_ for _ in ()).throw(AssertionError("hCaptcha must not run")),
    )
    service = PublicSubmissionService(Settings())

    result = service.submit(
        _valid_payload(),
        "192.0.2.10",
        identity=SubmissionIdentity(
            community_user_id=42,
            discord_id="123",
            admin_disabled=True,
        ),
    )

    assert result.status_code == 403
    assert result.payload == {
        "error": "Your community account is disabled and cannot submit records."
    }


def test_disabled_authenticated_submission_returns_exact_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = _Cursor(account_id=None)
    connection = _Connection(cursor)
    monkeypatch.setattr(
        "app.services.public_submission_service.open_connection",
        lambda: connection,
    )
    monkeypatch.setattr(PublicSubmissionService, "_verify_hcaptcha", lambda self, token: True)
    service = PublicSubmissionService(Settings())

    result = service.submit(
        _valid_payload(),
        "192.0.2.10",
        identity=SubmissionIdentity(community_user_id=42, discord_id="123"),
    )

    assert result.status_code == 403
    assert result.payload == {
        "error": "Your community account is disabled and cannot submit records."
    }
    assert any("admin_disabled = FALSE" in query for query in cursor.queries)
    assert connection.committed is False


def test_authenticated_submission_skips_ip_ban_and_omits_ip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = _Cursor(rate_counts=[1, 1])
    connection = _Connection(cursor)
    monkeypatch.setattr(
        "app.services.public_submission_service.open_connection",
        lambda: connection,
    )
    monkeypatch.setattr(PublicSubmissionService, "_verify_hcaptcha", lambda self, token: True)
    service = PublicSubmissionService(Settings())

    result = service.submit(
        _valid_payload(),
        "192.0.2.10",
        identity=SubmissionIdentity(community_user_id=42, discord_id="123"),
    )

    assert result.status_code == 200
    assert not any("FROM ip_ban" in query for query in cursor.queries)
    insert_parameters = cursor.parameters[-1]
    assert insert_parameters["submitter_ip"] is None
    assert insert_parameters["submitter_community_user_id"] == 42
    assert connection.committed is True


def test_rate_limit_key_is_hmac_keyed_without_raw_ip() -> None:
    service = PublicSubmissionService(
        Settings(SUBMISSION_RATE_LIMIT_HMAC_SECRET="rate-secret", AUTH_SHARED_SECRET="")
    )

    key = service._rate_limit_key("ip", "192.0.2.10")

    assert key.startswith("ip:")
    assert "192.0.2.10" not in key
    assert key == service._rate_limit_key("ip", "192.0.2.10")
    assert key != service._rate_limit_key("ip", "192.0.2.11")


def test_atomic_rate_limit_returns_retry_after_without_record_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = _Cursor(rate_counts=[1, 6])
    connection = _Connection(cursor)
    monkeypatch.setattr(
        "app.services.public_submission_service.open_connection",
        lambda: connection,
    )
    monkeypatch.setattr(PublicSubmissionService, "_verify_hcaptcha", lambda self, token: True)
    service = PublicSubmissionService(Settings())

    result = service.submit(_valid_payload(), "192.0.2.10")

    assert result.status_code == 429
    assert result.retry_after == 120
    assert not any("MAX(distance)" in query for query in cursor.queries)
    assert any("ON CONFLICT (rate_key) DO UPDATE" in query for query in cursor.queries)
    assert connection.committed is False


def test_submission_route_resolves_authenticated_identity() -> None:
    class Auth:
        def status_from_cookie(self, cookie: str | None) -> dict[str, Any]:
            return {"logged": True, "id": "123", "username": "driver"}

    class Community:
        def get_or_create(self, **kwargs: str | None) -> dict[str, int]:
            return {"id": 42}

    class Submission:
        def __init__(self) -> None:
            self.calls: list[tuple[str | None, Any]] = []

        def submit_with_identity(
            self,
            data: dict[str, Any],
            submitter_ip: str | None,
            identity: Any,
        ) -> SubmissionResult:
            self.calls.append((submitter_ip, identity))
            return SubmissionResult(200, {"success": True})

    submission = Submission()
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    app.dependency_overrides[dependencies.get_auth_service] = lambda: Auth()
    app.dependency_overrides[dependencies.get_community_account_service] = lambda: Community()
    app.dependency_overrides[dependencies.get_public_submission_service] = lambda: submission
    client = TestClient(app)
    client.cookies.set("WC_TOKEN", "token")

    response = client.post("/api/v1/submissions", json=_valid_payload())

    assert response.status_code == 200
    assert submission.calls[0][1] == SubmissionIdentity(
        community_user_id=42,
        discord_id="123",
    )


def test_submission_route_does_not_downgrade_identity_database_failure() -> None:
    class Auth:
        def status_from_cookie(self, cookie: str | None) -> dict[str, Any]:
            return {"logged": True, "id": "123"}

    class Community:
        def get_or_create(self, **kwargs: str | None) -> dict[str, int]:
            raise DatabaseNotConfigured("offline")

    class Submission:
        def submit_with_identity(self, *_args: Any) -> SubmissionResult:
            raise AssertionError("submission service must not run")

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    app.dependency_overrides[dependencies.get_auth_service] = lambda: Auth()
    app.dependency_overrides[dependencies.get_community_account_service] = lambda: Community()
    app.dependency_overrides[dependencies.get_public_submission_service] = lambda: Submission()
    client = TestClient(app)
    client.cookies.set("WC_TOKEN", "token")

    response = client.post("/api/v1/submissions", json=_valid_payload())

    assert response.status_code == 500
    assert response.json() == {"error": "Database error"}


def test_submission_route_returns_json_for_submission_database_failure() -> None:
    class Submission:
        def submit_with_identity(self, *_args: Any) -> SubmissionResult:
            raise DatabaseNotConfigured("offline")

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    app.dependency_overrides[dependencies.get_public_submission_service] = lambda: Submission()

    response = TestClient(app).post("/api/v1/submissions", json=_valid_payload())

    assert response.status_code == 500
    assert response.json() == {"error": "Database error"}


def test_submission_route_rejects_unresolvable_identity_without_degrading() -> None:
    class Auth:
        def status_from_cookie(self, cookie: str | None) -> dict[str, Any]:
            return {"logged": True}

    class Community:
        def get_or_create(self, **kwargs: str | None) -> dict[str, int]:
            raise AssertionError("account lookup must not run without a Discord ID")

    class Submission:
        def submit_with_identity(self, *_args: Any) -> SubmissionResult:
            raise AssertionError("submission service must not run")

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    app.dependency_overrides[dependencies.get_auth_service] = lambda: Auth()
    app.dependency_overrides[dependencies.get_community_account_service] = lambda: Community()
    app.dependency_overrides[dependencies.get_public_submission_service] = lambda: Submission()
    client = TestClient(app)
    client.cookies.set("WC_TOKEN", "token")

    response = client.post("/api/v1/submissions", json=_valid_payload())

    assert response.status_code == 403
    assert response.json() == {
        "error": "Your session could not be verified. Please sign in again."
    }


def test_submission_route_rejects_identity_with_unusable_account_id() -> None:
    class Auth:
        def status_from_cookie(self, cookie: str | None) -> dict[str, Any]:
            return {"logged": True, "id": "123"}

    class Community:
        def get_or_create(self, **kwargs: str | None) -> dict[str, int]:
            return {"id": 0}

    class Submission:
        def submit_with_identity(self, *_args: Any) -> SubmissionResult:
            raise AssertionError("submission service must not run")

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    app.dependency_overrides[dependencies.get_auth_service] = lambda: Auth()
    app.dependency_overrides[dependencies.get_community_account_service] = lambda: Community()
    app.dependency_overrides[dependencies.get_public_submission_service] = lambda: Submission()
    client = TestClient(app)
    client.cookies.set("WC_TOKEN", "token")

    response = client.post("/api/v1/submissions", json=_valid_payload())

    assert response.status_code == 403
    assert response.json() == {
        "error": "Your session could not be verified. Please sign in again."
    }
