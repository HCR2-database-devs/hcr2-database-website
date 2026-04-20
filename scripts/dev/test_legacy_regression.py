from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("LEGACY_BASE_URL", "http://127.0.0.1:18080").rstrip("/")
AUTH_SECRET = os.environ.get("AUTH_SHARED_SECRET", "dev-only-hcr2-secret")
ADMIN_SUBJECT = os.environ.get("DEV_DISCORD_ID", "dev-admin")
ADMIN_USERNAME = os.environ.get("DEV_DISCORD_USERNAME", "Dev Admin")


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: str
    content_type: str

    def json(self) -> Any:
        return json.loads(self.body)


@dataclass(frozen=True)
class Check:
    name: str
    method: str
    path: str
    expected_status: int
    validator: Callable[[HttpResult], None]
    body: bytes | None = None
    headers: dict[str, str] | None = None
    expected_failure: bool = False


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def make_token() -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64url(
        json.dumps(
            {
                "sub": ADMIN_SUBJECT,
                "username": ADMIN_USERNAME,
                "exp": int(time.time()) + 86400,
            },
            separators=(",", ":"),
        ).encode()
    )
    signature = _b64url(
        hmac.new(AUTH_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{signature}"


def request(check: Check) -> HttpResult:
    req = Request(
        f"{BASE_URL}{check.path}",
        method=check.method,
        data=check.body,
        headers=check.headers or {},
    )
    try:
        with urlopen(req, timeout=10) as response:
            return HttpResult(
                status=response.status,
                body=response.read().decode("utf-8", errors="replace"),
                content_type=response.headers.get("Content-Type", ""),
            )
    except HTTPError as exc:
        return HttpResult(
            status=exc.code,
            body=exc.read().decode("utf-8", errors="replace"),
            content_type=exc.headers.get("Content-Type", ""),
        )
    except URLError as exc:
        raise RuntimeError(f"Unable to reach {BASE_URL}: {exc}") from exc


def require_text(fragment: str) -> Callable[[HttpResult], None]:
    def validator(result: HttpResult) -> None:
        if fragment not in result.body:
            raise AssertionError(f"Expected body to contain {fragment!r}")

    return validator


def require_json_value(path: list[str], expected: Any) -> Callable[[HttpResult], None]:
    def validator(result: HttpResult) -> None:
        data = result.json()
        active: Any = data
        for key in path:
            active = active[key]
        if active != expected:
            raise AssertionError(f"Expected {'.'.join(path)}={expected!r}, got {active!r}")

    return validator


def require_json_list_length_at_least(path: list[str] | None, minimum: int) -> Callable[[HttpResult], None]:
    def validator(result: HttpResult) -> None:
        data = result.json()
        active = data
        if path:
            for key in path:
                active = active[key]
        if not isinstance(active, list):
            raise AssertionError(f"Expected list at {path or '<root>'}, got {type(active).__name__}")
        if len(active) < minimum:
            raise AssertionError(f"Expected at least {minimum} rows, got {len(active)}")

    return validator


def require_status_only(_: HttpResult) -> None:
    return None


def main() -> int:
    token = make_token()
    admin_cookie = {"Cookie": f"WC_TOKEN={token}"}
    json_headers = {"Content-Type": "application/json"}

    checks = [
        Check("public index", "GET", "/", 200, require_text("HCR2 Adventure Records")),
        Check("legacy css", "GET", "/css/style.css", 200, require_text("body")),
        Check("legacy logo", "GET", "/img/hcrdatabaselogo.png", 200, require_status_only),
        Check(
            "maintenance status",
            "GET",
            "/php/maintenance_status.php",
            200,
            require_json_value(["maintenance"], False),
        ),
        Check("maps data", "GET", "/php/load_data.php?type=maps", 200, require_json_list_length_at_least(None, 1)),
        Check(
            "vehicles data",
            "GET",
            "/php/load_data.php?type=vehicles",
            200,
            require_json_list_length_at_least(None, 1),
        ),
        Check(
            "players data",
            "GET",
            "/php/load_data.php?type=players",
            200,
            require_json_list_length_at_least(None, 1),
        ),
        Check(
            "tuning parts data",
            "GET",
            "/php/load_data.php?type=tuning_parts",
            200,
            require_json_list_length_at_least(None, 1),
        ),
        Check(
            "tuning setups data",
            "GET",
            "/php/load_data.php?type=tuning_setups",
            200,
            require_json_list_length_at_least(None, 1),
        ),
        Check(
            "records data",
            "GET",
            "/php/load_data.php?type=records",
            200,
            require_json_list_length_at_least(None, 1),
        ),
        Check("news data", "GET", "/php/get_news.php", 200, require_json_list_length_at_least(["news"], 1)),
        Check(
            "hcaptcha site key",
            "GET",
            "/php/get_hcaptcha_sitekey.php",
            200,
            require_json_value(["sitekey"], "dev-hcaptcha-site-key"),
        ),
        Check(
            "auth status logged out",
            "GET",
            "/auth/status.php",
            200,
            require_json_value(["logged"], False),
        ),
        Check(
            "auth status admin token",
            "GET",
            "/auth/status.php",
            200,
            require_json_value(["allowed"], True),
            headers=admin_cookie,
        ),
        Check(
            "api records unauthorized",
            "GET",
            "/php/api_records.php",
            401,
            require_json_value(["error"], "Unauthorized: invalid API key"),
        ),
        Check(
            "api records authorized",
            "GET",
            "/php/api_records.php?api_key=dev-api-key",
            200,
            require_json_list_length_at_least(["records"], 1),
        ),
        Check(
            "admin pending list",
            "GET",
            "/auth/admin_pending.php",
            200,
            require_json_list_length_at_least(["pending"], 1),
            headers=admin_cookie,
        ),
        Check(
            "admin integrity",
            "POST",
            "/auth/admin_actions.php",
            200,
            require_json_value(["ok"], True),
            body=urlencode({"action": "integrity"}).encode(),
            headers={**admin_cookie, "Content-Type": "application/x-www-form-urlencoded"},
        ),
        Check(
            "public submit rejected by hcaptcha",
            "POST",
            "/php/public_submit.php",
            400,
            require_json_value(["error"], "hCaptcha verification failed. Please try again."),
            body=json.dumps({}).encode(),
            headers=json_headers,
        ),
        Check(
            "delete record authorized no-op",
            "POST",
            "/php/delete_record.php",
            200,
            require_json_value(["success"], True),
            body=json.dumps({"recordId": 999999}).encode(),
            headers={**admin_cookie, **json_headers},
        ),
    ]

    failures = 0
    for check in checks:
        result = request(check)
        passed = result.status == check.expected_status
        detail = ""
        if passed:
            try:
                check.validator(result)
            except Exception as exc:  # noqa: BLE001
                passed = False
                detail = str(exc)
        else:
            detail = f"expected HTTP {check.expected_status}, got {result.status}"

        label = "XFAIL" if check.expected_failure and passed else "PASS" if passed else "FAIL"
        print(f"{label}: {check.name} [{check.method} {check.path}] -> {result.status}")
        if detail:
            print(f"  {detail}")
        if not passed:
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
