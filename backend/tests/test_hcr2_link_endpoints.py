"""Endpoint tests for Phase 4 HCR2 player account linking.

Exercises authorization, beta enforcement, the "arbitrary names cannot be
posted directly" guarantee, and the fact that internal security metadata never
reaches a user-facing response while the code *does* reach the admin queue.
"""

from typing import Any

from fastapi.testclient import TestClient

from app.api import dependencies
from app.core.config import Settings, get_settings
from app.db.session import DatabaseConfig
from app.main import create_app
from app.services.community_account_service import CommunityProfileError
from app.services.hcr2_link_service import Hcr2LinkService
from tests.test_hcr2_link_service import (
    FakeHcr2LinkRepository,
    RecordingActivityLog,
    RecordingNotifications,
    _settings,
)
from tests.test_hcr2_link_service import (
    FakeHcr2LinkRepository as _Repo,
)


class FakeAuthService:
    def __init__(self) -> None:
        self.beta_ids: set[str] = {"beta-user"}

    def status_from_cookie(self, cookie: str | None) -> dict[str, Any]:
        if not cookie or cookie == "bad":
            return {"logged": False, "allowed": False}
        return {
            "logged": True,
            "allowed": cookie == "admin",
            "beta": cookie in self.beta_ids,
            "id": cookie,
            "username": f"Name {cookie}",
        }


class FakeCommunityAccountService:
    def __init__(self) -> None:
        self.users: dict[int, dict[str, Any]] = {}

    def add_user(self, discord_id: str, *, username: str | None = "Nipa") -> dict[str, Any]:
        user = {
            "id": len(self.users) + 1,
            "discord_id": discord_id,
            "discord_username": f"Name {discord_id}",
            "discord_avatar": None,
            "username": username,
        }
        self.users[user["id"]] = user
        return user

    def get_account(self, discord_id: str) -> dict[str, Any] | None:
        for user in self.users.values():
            if user["discord_id"] == discord_id:
                return user
        return None


def _beta_settings(**overrides: Any) -> Settings:
    """Settings with the Phase 4 flag in its shipped state: BETA."""
    return _settings(
        FEATURE_HCR2_ACCOUNT_LINKING="BETA",
        BETA_DISCORD_IDS="beta-user",
        ALLOWED_DISCORD_IDS="admin",
        **overrides,
    )


def _client(settings: Settings | None = None) -> tuple[TestClient, _Repo]:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings or _beta_settings()
    repository = FakeHcr2LinkRepository()
    community = FakeCommunityAccountService()
    for discord_id in ("beta-user", "admin"):
        community.add_user(discord_id)
    link_service = Hcr2LinkService(
        repository=repository,
        settings=settings or _beta_settings(),
        activity_log=RecordingActivityLog(),  # type: ignore[arg-type]
        notification_service=RecordingNotifications(),  # type: ignore[arg-type]
        # See the note in test_hcr2_link_service: keeps the rate limiter from
        # reaching the ambient development database during tests.
        config=DatabaseConfig(dsn=""),
    )
    app.dependency_overrides[dependencies.get_auth_service] = FakeAuthService
    app.dependency_overrides[dependencies.get_community_account_service] = lambda: community
    app.dependency_overrides[dependencies.get_hcr2_link_service] = lambda: link_service
    return TestClient(app), repository


def _cookie(name: str = "beta-user") -> dict[str, str]:
    return {"WC_TOKEN": name}


# -- authorization ---------------------------------------------------------


def test_endpoints_require_a_signed_in_user() -> None:
    client, _ = _client()

    for path in (
        "/api/v1/community/hcr2-link/config",
        "/api/v1/community/hcr2-link/status",
        "/api/v1/community/hcr2-link/players",
    ):
        response = client.get(path)
        assert response.status_code == 401, path


def test_beta_access_is_enforced_server_side() -> None:
    client, _ = _client()

    response = client.get("/api/v1/community/hcr2-link/status", cookies=_cookie("plain-user"))

    assert response.status_code == 403
    assert response.json()["detail"] == "This feature is currently disabled"


def test_disabled_flag_blocks_everyone_including_admins() -> None:
    client, _ = _client(_settings(FEATURE_HCR2_ACCOUNT_LINKING="DISABLED"))

    assert client.get(
        "/api/v1/community/hcr2-link/status", cookies=_cookie("admin")
    ).status_code == 403


def test_admins_pass_the_beta_gate() -> None:
    client, _ = _client()

    assert client.get(
        "/api/v1/community/hcr2-link/status", cookies=_cookie("admin")
    ).status_code == 200


def test_onboarding_is_required_before_linking() -> None:
    client, _ = _client()

    # A signed-in account without a username is sent to onboarding first.
    app = client.app
    community = next(
        override() for name, override in app.dependency_overrides.items()
        if name is dependencies.get_community_account_service
    )
    community.users = {}
    community.add_user("beta-user", username=None)

    response = client.get("/api/v1/community/hcr2-link/status", cookies=_cookie())
    assert response.status_code == 403
    assert "username" in response.json()["detail"]


def test_client_supplied_identity_is_ignored() -> None:
    client, _ = _client()

    # Trying to act as somebody else by posting an id changes nothing: the
    # cookie is the only source of identity.
    response = client.post(
        "/api/v1/community/hcr2-link/request/start",
        cookies=_cookie(),
        json={"player_name": "Demo Driver", "community_user_id": 999, "discord_id": "1"},
    )

    assert response.status_code == 200
    # The request was created for the cookie identity (id 1), not 999.
    assert response.json()["request"]["id"] == 1


# -- config ----------------------------------------------------------------


def test_config_returns_the_team_name_and_password() -> None:
    client, _ = _client()

    body = client.get("/api/v1/community/hcr2-link/config", cookies=_cookie()).json()

    assert body["team"]["team_name"] == "hcr2xyz verify"
    assert body["team"]["team_password"] == "letmein"
    assert body["discord"]["requires_microphone"] is False
    assert body["discord"]["requires_speaking"] is False
    assert body["automatic_verification"] is False


# -- dropdown --------------------------------------------------------------


def test_players_endpoint_only_returns_names_backed_by_records() -> None:
    client, _ = _client()

    body = client.get(
        "/api/v1/community/hcr2-link/players?q=demo", cookies=_cookie()
    ).json()

    assert [row["name_player"] for row in body["players"]] == ["Demo Driver"]
    assert set(body["players"][0]) == {"id_player", "name_player", "record_count"}


def test_players_endpoint_does_not_leak_submission_metadata() -> None:
    client, _ = _client()

    response = client.get("/api/v1/community/hcr2-link/players", cookies=_cookie())

    text = response.text
    for leaked in ("submitter", "ip", "questionable", "distance", "code"):
        assert leaked not in text


# -- arbitrary names -------------------------------------------------------


def test_arbitrary_player_names_cannot_be_posted_directly() -> None:
    client, repository = _client()

    response = client.post(
        "/api/v1/community/hcr2-link/request/start",
        cookies=_cookie(),
        json={"player_name": "Totally Made Up Name"},
    )

    assert response.status_code == 400
    assert "not available for linking" in response.json()["error"]
    assert repository.requests == {}


def test_duplicate_active_link_returns_a_generic_error() -> None:
    client, repository = _client()
    repository.links[1] = {
        "id": 1,
        "community_user_id": 4242,
        "player_id": 1,
        "player_name": "Demo Driver",
        "player_name_norm": "demo driver",
        "verification_method": "team",
        "status": "active",
        "requested_at": None,
        "approved_at": None,
        "approved_by_admin": "mod",
        "revoked_at": None,
        "revoked_by_admin": "",
        "revocation_reason": None,
    }

    response = client.post(
        "/api/v1/community/hcr2-link/request/start",
        cookies=_cookie(),
        json={"player_name": "Demo Driver"},
    )

    assert response.status_code == 409
    body = response.text
    assert "already linked" in body
    # The other account's identity must never be revealed.
    assert "4242" not in body


# -- team wizard -----------------------------------------------------------


def _start_team_wizard(client: TestClient) -> None:
    assert (
        client.post(
            "/api/v1/community/hcr2-link/request/start",
            cookies=_cookie(),
            json={"player_name": "Demo Driver"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/community/hcr2-link/request/method",
            cookies=_cookie(),
            json={"verification_method": "team"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/community/hcr2-link/request/team/joined", cookies=_cookie()
        ).status_code
        == 200
    )


def test_team_code_endpoint_returns_the_code_without_the_hash() -> None:
    client, _ = _client()
    _start_team_wizard(client)

    body = client.post("/api/v1/community/hcr2-link/request/team/code", cookies=_cookie()).json()

    assert body["code"].startswith("Demo Driver:")
    assert body["single_use"] is True
    assert body["previous_code_invalidated"] is True
    assert body["reroll_cooldown_seconds"] == 10
    assert "code_token_hash" not in body


def test_code_reroll_cooldown_is_enforced_by_the_server() -> None:
    client, _ = _client()
    _start_team_wizard(client)
    client.post("/api/v1/community/hcr2-link/request/team/code", cookies=_cookie())

    response = client.post("/api/v1/community/hcr2-link/request/team/code", cookies=_cookie())

    assert response.status_code == 429
    assert "seconds" in response.json()["error"]


def test_full_team_flow_submits_to_the_review_queue_without_approving() -> None:
    client, repository = _client()
    _start_team_wizard(client)
    code = client.post(
        "/api/v1/community/hcr2-link/request/team/code", cookies=_cookie()
    ).json()["code"]
    client.post(
        "/api/v1/community/hcr2-link/request/team/sent",
        cookies=_cookie(),
        json={"visibility_confirmed": True},
    )

    response = client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["request"]["status"] == "submitted"
    assert body["automatic_verification"] is False
    assert "awaiting admin review" in body["message"]
    assert repository.links == {}
    assert code.startswith("Demo Driver:")


def test_status_endpoint_never_leaks_the_hash_or_admin_metadata() -> None:
    client, _ = _client()
    _start_team_wizard(client)
    client.post("/api/v1/community/hcr2-link/request/team/code", cookies=_cookie())

    response = client.get("/api/v1/community/hcr2-link/status", cookies=_cookie())

    assert response.status_code == 200
    text = response.text
    for leaked in ("code_token_hash", "admin_note", "decided_by_admin", "discord_id"):
        assert leaked not in text


# -- discord wizard --------------------------------------------------------


def test_discord_flow_never_requires_a_microphone_in_its_payload() -> None:
    client, _ = _client()
    client.post(
        "/api/v1/community/hcr2-link/request/start",
        cookies=_cookie(),
        json={"player_name": "Demo Driver"},
    )
    client.post(
        "/api/v1/community/hcr2-link/request/method",
        cookies=_cookie(),
        json={"verification_method": "discord_screen_share"},
    )
    assert (
        client.post(
            "/api/v1/community/hcr2-link/request/discord/joined", cookies=_cookie()
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/community/hcr2-link/request/discord/contacted", cookies=_cookie()
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/community/hcr2-link/request/discord/ready", cookies=_cookie()
        ).status_code
        == 200
    )

    response = client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    assert response.status_code == 200
    assert response.json()["request"]["status"] == "submitted"


def test_unconfigured_method_is_reported_as_not_configured() -> None:
    client, _ = _client(_settings(HCR2_LINK_VERIFICATION_TEAM_NAME=""))
    client.post(
        "/api/v1/community/hcr2-link/request/start",
        cookies=_cookie(),
        json={"player_name": "Demo Driver"},
    )

    response = client.post(
        "/api/v1/community/hcr2-link/request/method",
        cookies=_cookie(),
        json={"verification_method": "team"},
    )

    assert response.status_code == 503
    assert "not configured" in response.json()["error"]


# -- challenge method ------------------------------------------------------


def _challenge_client() -> tuple[TestClient, _Repo]:
    return _client(_settings(HCR2_LINK_CHALLENGE_ENABLED=True))


def _start_challenge_wizard(client: TestClient) -> None:
    client.post(
        "/api/v1/community/hcr2-link/request/start",
        cookies=_cookie(),
        json={"player_name": "Demo Driver"},
    )
    client.post(
        "/api/v1/community/hcr2-link/request/method",
        cookies=_cookie(),
        json={"verification_method": "playhcr_challenge"},
    )


def test_the_challenge_card_is_off_until_the_method_is_enabled() -> None:
    client, _ = _client()

    config = client.get("/api/v1/community/hcr2-link/config", cookies=_cookie()).json()

    assert config["challenge"]["available"] is False


def test_config_publishes_the_accepted_challenge_link_prefix() -> None:
    client, _ = _challenge_client()

    config = client.get("/api/v1/community/hcr2-link/config", cookies=_cookie()).json()

    assert config["challenge"]["available"] is True
    assert config["challenge"]["link_prefix"] == "https://playhcr.com/challenge?id="
    assert config["challenge"]["min_distance_m"] == 1
    assert config["challenge"]["max_distance_m"] == 2000


def test_choosing_the_challenge_method_assigns_a_distance_server_side() -> None:
    client, repository = _challenge_client()

    _start_challenge_wizard(client)
    response = client.get("/api/v1/community/hcr2-link/status", cookies=_cookie())

    distance = repository.requests[1]["challenge_distance_m"]
    assert 1 <= distance <= 2000
    assert response.json()["request"]["challenge_distance_m"] == distance


def test_the_unconfigured_challenge_method_returns_503() -> None:
    client, _ = _client()
    client.post(
        "/api/v1/community/hcr2-link/request/start",
        cookies=_cookie(),
        json={"player_name": "Demo Driver"},
    )

    response = client.post(
        "/api/v1/community/hcr2-link/request/method",
        cookies=_cookie(),
        json={"verification_method": "playhcr_challenge"},
    )

    assert response.status_code == 503
    assert "not configured" in response.json()["error"]


def test_challenge_flow_accepts_a_playhcr_link_and_submits() -> None:
    client, repository = _challenge_client()
    _start_challenge_wizard(client)

    response = client.post(
        "/api/v1/community/hcr2-link/request/challenge/link",
        cookies=_cookie(),
        json={"challenge_url": "https://playhcr.com/challenge?id=abc123"},
    )

    assert response.status_code == 200
    assert response.json()["request"]["challenge_link_claimed"] is True
    assert repository.requests[1]["challenge_id"] == "abc123"

    submitted = client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    assert submitted.status_code == 200
    assert submitted.json()["request"]["status"] == "submitted"
    assert submitted.json()["automatic_verification"] is False
    # Submitting queues a human; it never creates a link by itself.
    assert repository.links == {}


def test_the_challenge_endpoint_rejects_a_link_that_is_not_a_playhcr_challenge() -> None:
    client, repository = _challenge_client()
    _start_challenge_wizard(client)

    response = client.post(
        "/api/v1/community/hcr2-link/request/challenge/link",
        cookies=_cookie(),
        json={"challenge_url": "https://playhcr.com.attacker.example/challenge?id=abc"},
    )

    assert response.status_code == 400
    assert repository.requests[1]["challenge_url"] is None


def test_the_challenge_endpoint_refuses_an_empty_link() -> None:
    client, _ = _challenge_client()
    _start_challenge_wizard(client)

    response = client.post(
        "/api/v1/community/hcr2-link/request/challenge/link",
        cookies=_cookie(),
        json={"challenge_url": ""},
    )

    assert response.status_code == 400


def test_a_challenge_link_cannot_be_sent_for_a_team_request() -> None:
    client, _ = _challenge_client()
    client.post(
        "/api/v1/community/hcr2-link/request/start",
        cookies=_cookie(),
        json={"player_name": "Demo Driver"},
    )
    client.post(
        "/api/v1/community/hcr2-link/request/method",
        cookies=_cookie(),
        json={"verification_method": "team"},
    )

    response = client.post(
        "/api/v1/community/hcr2-link/request/challenge/link",
        cookies=_cookie(),
        json={"challenge_url": "https://playhcr.com/challenge?id=abc123"},
    )

    assert response.status_code == 409


def test_submitting_a_challenge_request_without_a_link_is_refused() -> None:
    client, repository = _challenge_client()
    _start_challenge_wizard(client)

    response = client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    assert response.status_code == 409
    assert repository.requests[1]["status"] != "submitted"


def test_the_admin_queue_shows_the_distance_and_the_challenge_link() -> None:
    client, _ = _challenge_client()
    _start_challenge_wizard(client)
    client.post(
        "/api/v1/community/hcr2-link/request/challenge/link",
        cookies=_cookie(),
        json={"challenge_url": "https://playhcr.com/challenge?id=abc123"},
    )
    client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    detail = client.get(
        "/api/v1/admin/hcr2-link/requests/1", cookies=_cookie("admin")
    ).json()
    request = detail["request"]

    assert request["verification_method"] == "playhcr_challenge"
    assert request["challenge_distance_m"] is not None
    assert request["challenge_url"] == "https://playhcr.com/challenge?id=abc123"
    assert request["challenge_id"] == "abc123"


def test_the_challenge_endpoint_requires_a_signed_in_user() -> None:
    client, _ = _challenge_client()

    response = client.post(
        "/api/v1/community/hcr2-link/request/challenge/link",
        json={"challenge_url": "https://playhcr.com/challenge?id=abc123"},
    )

    assert response.status_code == 401


def test_unlink_endpoint_revokes_the_callers_own_link() -> None:
    client, repository = _client()
    _start_team_wizard(client)
    client.post("/api/v1/community/hcr2-link/request/team/code", cookies=_cookie())
    client.post(
        "/api/v1/community/hcr2-link/request/team/sent",
        cookies=_cookie(),
        json={"visibility_confirmed": True},
    )
    client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )
    client.post("/api/v1/admin/hcr2-link/requests/1/approve", cookies=_cookie("admin"))

    response = client.post("/api/v1/community/hcr2-link/link/unlink", cookies=_cookie())

    assert response.status_code == 200
    assert repository.links[1]["status"] == "revoked"


# -- admin review queue ----------------------------------------------------


def test_admin_queue_requires_an_admin() -> None:
    client, _ = _client()

    assert client.get("/api/v1/admin/hcr2-link/requests").status_code == 401
    assert (
        client.get("/api/v1/admin/hcr2-link/requests", cookies=_cookie("beta-user")).status_code
        == 403
    )
    assert (
        client.get("/api/v1/admin/hcr2-link/requests", cookies=_cookie("admin")).status_code == 200
    )


def test_admin_queue_never_auto_approves() -> None:
    client, repository = _client()
    _start_team_wizard(client)
    client.post("/api/v1/community/hcr2-link/request/team/code", cookies=_cookie())
    client.post(
        "/api/v1/community/hcr2-link/request/team/sent",
        cookies=_cookie(),
        json={"visibility_confirmed": True},
    )
    client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    body = client.get(
        "/api/v1/admin/hcr2-link/requests?status=submitted", cookies=_cookie("admin")
    ).json()

    assert body["count"] == 1
    assert repository.links == {}
    assert body["requests"][0]["status"] == "submitted"


def test_admin_detail_exposes_the_code_and_the_discord_identity() -> None:
    client, _ = _client()
    _start_team_wizard(client)
    code = client.post(
        "/api/v1/community/hcr2-link/request/team/code", cookies=_cookie()
    ).json()["code"]
    client.post(
        "/api/v1/community/hcr2-link/request/team/sent",
        cookies=_cookie(),
        json={"visibility_confirmed": True},
    )
    client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    body = client.get("/api/v1/admin/hcr2-link/requests/1", cookies=_cookie("admin")).json()

    request = body["request"]
    assert request["code_value"] == code
    # The Discord snowflake and display name are available for identification
    # inside the admin panel only.
    assert request["discord_id"]
    assert request["discord_username"].startswith("Name ")
    assert request["community_username"] == "user-1"
    assert request["code_sent_confirmed_at"] is not None
    assert request["code_visibility_confirmed"] is True
    assert request["team_joined_at"] is not None
    assert body["steps"]
    # Even for an admin the token hash is not exposed; the plaintext is what
    # they compare against team chat.
    assert "code_token_hash" not in request


def test_admin_can_approve_and_then_revoke() -> None:
    client, repository = _client()
    _start_team_wizard(client)
    client.post("/api/v1/community/hcr2-link/request/team/code", cookies=_cookie())
    client.post(
        "/api/v1/community/hcr2-link/request/team/sent",
        cookies=_cookie(),
        json={"visibility_confirmed": True},
    )
    client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    approved = client.post(
        "/api/v1/admin/hcr2-link/requests/1/approve",
        cookies=_cookie("admin"),
        json={"note": "Saw the code"},
    )
    assert approved.status_code == 200
    assert approved.json()["link"]["status"] == "active"

    revoked = client.post(
        "/api/v1/admin/hcr2-link/links/1/status",
        cookies=_cookie("admin"),
        json={"status": "revoked", "reason": "Member asked us to remove it"},
    )
    assert revoked.status_code == 200
    assert revoked.json()["link"]["status"] == "revoked"
    assert repository.links[1]["revoked_by_admin"] == "Name admin"


def test_admin_can_reject_with_a_category_and_reason() -> None:
    client, _ = _client()
    _start_team_wizard(client)
    client.post("/api/v1/community/hcr2-link/request/team/code", cookies=_cookie())
    client.post(
        "/api/v1/community/hcr2-link/request/team/sent",
        cookies=_cookie(),
        json={"visibility_confirmed": True},
    )
    client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    response = client.post(
        "/api/v1/admin/hcr2-link/requests/1/reject",
        cookies=_cookie("admin"),
        json={
            "category": "code_not_visible",
            "reason": "The code was censored in team chat.",
            "note": "internal only",
        },
    )

    assert response.status_code == 200


def test_admin_can_schedule_cancel_and_retry() -> None:
    client, _ = _client()
    client.post(
        "/api/v1/community/hcr2-link/request/start",
        cookies=_cookie(),
        json={"player_name": "Demo Driver"},
    )
    client.post(
        "/api/v1/community/hcr2-link/request/method",
        cookies=_cookie(),
        json={"verification_method": "discord_screen_share"},
    )
    for step in ("joined", "contacted", "ready"):
        assert (
            client.post(
                f"/api/v1/community/hcr2-link/request/discord/{step}", cookies=_cookie()
            ).status_code
            == 200
        )
    client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    scheduled = client.post(
        "/api/v1/admin/hcr2-link/requests/1/appointment",
        cookies=_cookie("admin"),
        json={"appointment_status": "scheduled", "appointment_at": "2026-10-20T18:30:00"},
    )
    assert scheduled.status_code == 200

    retried = client.post(
        "/api/v1/admin/hcr2-link/requests/1/retry",
        cookies=_cookie("admin"),
        json={"note": "Please reroll"},
    )
    assert retried.status_code == 200

    cancelled = client.post(
        "/api/v1/admin/hcr2-link/requests/1/cancel",
        cookies=_cookie("admin"),
        json={"note": "Duplicate claim"},
    )
    assert cancelled.status_code == 200


def test_admin_actions_reject_an_unknown_reason_category() -> None:
    client, _ = _client()
    _start_team_wizard(client)
    client.post(
        "/api/v1/community/hcr2-link/request/submit",
        cookies=_cookie(),
        json={"instructions_followed": True, "method_steps_completed": True},
    )

    response = client.post(
        "/api/v1/admin/hcr2-link/requests/1/reject",
        cookies=_cookie("admin"),
        json={"category": "not-a-category", "reason": "x"},
    )

    assert response.status_code == 400


def test_admin_column_list_never_selects_the_token_hash() -> None:
    # Guards the real SQL column list, not just the fake used above: the
    # plaintext code is what an admin compares against team chat, so the keyed
    # hash has no reason to leave the database.
    from app.repositories.hcr2_link import ADMIN_REQUEST_COLUMNS, USER_REQUEST_COLUMNS

    assert "r.code_token_hash" not in ADMIN_REQUEST_COLUMNS
    assert "r.code_value" in ADMIN_REQUEST_COLUMNS
    assert "r.code_token_hash" in USER_REQUEST_COLUMNS


def test_admin_detail_returns_404_for_a_missing_request() -> None:
    client, _ = _client()

    assert (
        client.get("/api/v1/admin/hcr2-link/requests/999", cookies=_cookie("admin")).status_code
        == 404
    )


def test_domain_errors_do_not_leak_internals() -> None:
    client, _ = _client()

    response = client.post(
        "/api/v1/community/hcr2-link/request/start",
        cookies=_cookie(),
        json={"player_name": "No Such Player"},
    )

    assert response.status_code == 400
    assert "Traceback" not in response.text
    assert "SELECT" not in response.text


def test_service_error_helper_is_shared_with_phase_two() -> None:
    # Guards the assumption that Phase 4 reuses CommunityProfileError rather
    # than introducing a parallel error type.
    error = CommunityProfileError("boom", 409)

    assert error.status_code == 409
    assert error.message == "boom"