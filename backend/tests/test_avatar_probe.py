from typing import Any

import httpx
import pytest

from app.services.avatar_probe import avatar_reachable

LIVE = "https://cdn.discordapp.com/avatars/10001/a_1f2e3a.png"
DEAD = "https://cdn.discordapp.com/avatars/10001/deadbeefdeadbeefdeadbeefdeadbeef.png"


class _FakeClient:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def head(self, url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(self.status_code, request=httpx.Request("HEAD", url))

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(self.status_code, request=httpx.Request("GET", url))


@pytest.fixture()
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly if a test reaches the real network."""

    def explode(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("unexpected real network call")

    monkeypatch.setattr(httpx, "head", explode)
    monkeypatch.setattr(httpx, "get", explode)


def test_live_avatar_is_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "head", lambda url, **kw: _FakeClient(200).head(url))
    assert avatar_reachable(LIVE) is True


def test_rotated_hash_is_not_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Discord returns 404 once a member changes their avatar."""
    monkeypatch.setattr(httpx, "head", lambda url, **kw: _FakeClient(404).head(url))
    assert avatar_reachable(DEAD) is False


@pytest.mark.parametrize("status", [400, 403, 404, 410, 500, 502, 503])
def test_error_statuses_are_unreachable(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    monkeypatch.setattr(httpx, "head", lambda url, **kw: _FakeClient(status).head(url))
    assert avatar_reachable(LIVE) is False


def test_head_not_allowed_falls_back_to_get(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "head", lambda url, **kw: _FakeClient(405).head(url))
    monkeypatch.setattr(httpx, "get", lambda url, **kw: _FakeClient(200).get(url))

    assert avatar_reachable(LIVE) is True


def test_head_not_allowed_and_get_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "head", lambda url, **kw: _FakeClient(405).head(url))
    monkeypatch.setattr(httpx, "get", lambda url, **kw: _FakeClient(404).get(url))

    assert avatar_reachable(LIVE) is False


def test_network_error_is_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(url: str, **kwargs: Any) -> Any:
        raise httpx.ConnectError("no route to host")

    monkeypatch.setattr(httpx, "head", boom)

    assert avatar_reachable(LIVE) is False


def test_timeout_is_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    def slow(url: str, **kwargs: Any) -> Any:
        raise httpx.ReadTimeout("too slow")

    monkeypatch.setattr(httpx, "head", slow)

    assert avatar_reachable(LIVE) is False


def test_probe_uses_head_not_get(monkeypatch: pytest.MonkeyPatch) -> None:
    methods: list[str] = []

    def record(url: str, **kwargs: Any) -> httpx.Response:
        methods.append("HEAD")
        return _FakeClient(200).head(url)

    monkeypatch.setattr(httpx, "head", record)
    avatar_reachable(LIVE)

    assert methods == ["HEAD"]


def test_probe_sends_a_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def record(url: str, **kwargs: Any) -> httpx.Response:
        seen.update(kwargs)
        return _FakeClient(200).head(url)

    monkeypatch.setattr(httpx, "head", record)
    avatar_reachable(LIVE)

    assert "User-Agent" in seen["headers"]


def test_probe_passes_a_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def record(url: str, **kwargs: Any) -> httpx.Response:
        seen.update(kwargs)
        return _FakeClient(200).head(url)

    monkeypatch.setattr(httpx, "head", record)
    avatar_reachable(LIVE)

    assert seen["timeout"] > 0


def test_probe_follows_redirects(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def record(url: str, **kwargs: Any) -> httpx.Response:
        seen.update(kwargs)
        return _FakeClient(200).head(url)

    monkeypatch.setattr(httpx, "head", record)
    avatar_reachable(LIVE)

    assert seen["follow_redirects"] is True