from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.core.config import Settings
from app.core.verification_code import hash_token, split_code
from app.db.session import DatabaseConfig
from app.repositories.hcr2_link import ActiveLinkConflictError
from app.services.community_account_service import CommunityProfileError
from app.services.hcr2_link_service import (
    INELIGIBLE_NAME_ERROR,
    NAME_TAKEN_ERROR,
    Hcr2LinkService,
)


def _settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "AUTH_SHARED_SECRET": "test-secret",
        "FEATURE_HCR2_ACCOUNT_LINKING": "ENABLED",
        "HCR2_LINK_VERIFICATION_TEAM_NAME": "hcr2xyz verify",
        "HCR2_LINK_VERIFICATION_TEAM_PASSWORD": "letmein",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


class FakeHcr2LinkRepository:
    """In-memory stand-in enforcing the same uniqueness rules as the schema."""

    def __init__(self, *, eligible: tuple[str, ...] = ("Demo Driver",)) -> None:
        self.eligible = set(eligible)
        self.requests: dict[int, dict[str, Any]] = {}
        self.links: dict[int, dict[str, Any]] = {}
        self.steps: list[dict[str, Any]] = []
        self.next_request_id = 1
        self.next_link_id = 1
        self.searches: list[str | None] = []
        self.expired_sweeps = 0
        self.conflict_on_approve = False

    # -- player names -------------------------------------------------------

    def search_eligible_players(
        self,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        self.searches.append(search)
        names = sorted(self.eligible)
        if search:
            names = [name for name in names if search.lower() in name.lower()]
        rows = [
            {"id_player": index + 1, "name_player": name, "record_count": 3}
            for index, name in enumerate(names)
        ]
        return rows[offset : offset + limit], len(rows)

    def find_eligible_player(self, name: str) -> dict[str, Any] | None:
        for index, candidate in enumerate(sorted(self.eligible)):
            if candidate == name:
                return {"id_player": index + 1, "name_player": candidate, "record_count": 3}
        return None

    # -- links --------------------------------------------------------------

    def get_active_link_for_user(self, community_user_id: int) -> dict[str, Any] | None:
        for link in self.links.values():
            if link["community_user_id"] == community_user_id and link["status"] == "active":
                return dict(link)
        return None

    def get_active_link_for_player(self, player_name_norm: str) -> dict[str, Any] | None:
        for link in self.links.values():
            if link["player_name_norm"] == player_name_norm and link["status"] == "active":
                return dict(link)
        return None

    def get_link(self, link_id: int) -> dict[str, Any] | None:
        link = self.links.get(link_id)
        return dict(link) if link else None

    def _add_link(self, values: dict[str, Any]) -> dict[str, Any]:
        link = {
            "id": self.next_link_id,
            "community_user_id": values["community_user_id"],
            "player_id": values["player_id"],
            "player_name": values["player_name"],
            "player_name_norm": values["player_name_norm"],
            "verification_method": values["verification_method"],
            "status": "active",
            "requested_at": values.get("requested_at") or datetime.now(UTC).replace(tzinfo=None),
            "approved_at": datetime.now(UTC).replace(tzinfo=None),
            "approved_by_admin": values.get("admin_username", ""),
            "revoked_at": None,
            "revoked_by_admin": "",
            "revocation_reason": None,
        }
        self.links[link["id"]] = link
        self.next_link_id += 1
        return dict(link)

    def list_links(self, **_: Any) -> tuple[list[dict[str, Any]], int]:
        rows = [dict(link) for link in self.links.values()]
        return rows, len(rows)

    def set_link_status(self, values: dict[str, Any]) -> dict[str, Any] | None:
        link = self.links.get(values["link_id"])
        if link is None:
            return None
        link["status"] = values["status"]
        link["revoked_at"] = values.get("revoked_at")
        link["revoked_by_admin"] = values.get("revoked_by_admin", "")
        link["revocation_reason"] = values.get("revocation_reason")
        return dict(link)

    # -- requests -----------------------------------------------------------

    def get_request(self, request_id: int) -> dict[str, Any] | None:
        request = self.requests.get(request_id)
        if request is None:
            return None
        # Mirrors ADMIN_REQUEST_COLUMNS, which selects the plaintext
        # code_value but never the code_token_hash, plus the JOIN to
        # community_user.
        row = {key: value for key, value in request.items() if key != "code_token_hash"}
        row["community_username"] = f"user-{request['community_user_id']}"
        row["discord_id"] = str(1000 + request["community_user_id"])
        row["discord_username"] = f"Name {row['discord_id']}"
        return row

    def get_active_request(self, community_user_id: int) -> dict[str, Any] | None:
        open_ids = ("draft", "in_progress", "submitted")
        candidates = [
            request
            for request in self.requests.values()
            if request["community_user_id"] == community_user_id and request["status"] in open_ids
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda row: row["updated_at"], reverse=True)
        return dict(candidates[0])

    def get_latest_request(self, community_user_id: int) -> dict[str, Any] | None:
        candidates = [
            request
            for request in self.requests.values()
            if request["community_user_id"] == community_user_id
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda row: (row["created_at"], row["id"]))
        return dict(candidates[-1])

    def list_open_request_ids(self, community_user_id: int) -> list[int]:
        return sorted(
            request["id"]
            for request in self.requests.values()
            if request["community_user_id"] == community_user_id
            and request["status"] in ("draft", "in_progress")
        )

    def list_requests_for_user(self, community_user_id: int) -> list[dict[str, Any]]:
        return [
            dict(request)
            for request in self.requests.values()
            if request["community_user_id"] == community_user_id
        ]

    def create_request(self, values: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC).replace(tzinfo=None)
        request = {
            "id": self.next_request_id,
            "community_user_id": values["community_user_id"],
            "link_id": None,
            "player_id": values["player_id"],
            "player_name": values["player_name"],
            "player_name_norm": values["player_name_norm"],
            "verification_method": values["verification_method"],
            "status": values["status"],
            "step": values["step"],
            "attempt_count": values["attempt_count"],
            "is_resubmission": values["is_resubmission"],
            "supersedes_request_id": values["supersedes_request_id"],
            "created_at": now,
            "updated_at": now,
            "expires_at": values["expires_at"],
            "submitted_at": None,
            "team_joined_at": None,
            "code_token_hash": None,
            "code_value": None,
            "code_generated_at": None,
            "code_expires_at": None,
            "code_last_generated_at": None,
            "code_roll_count": 0,
            "code_sent_confirmed_at": None,
            "code_visibility_confirmed": False,
            "discord_joined_at": None,
            "contacted_owner_at": None,
            "challenge_distance_m": None,
            "challenge_url": None,
            "challenge_id": None,
            "challenge_confirmed_at": None,
            "appointment_status": "waiting_contact",
            "appointment_at": None,
            "appointment_note": None,
            "decided_at": None,
            "decided_by_admin": "",
            "rejection_category": None,
            "rejection_reason": None,
            "admin_note": None,
        }
        self.requests[request["id"]] = request
        self.next_request_id += 1
        self._record_step(request["id"], request["step"], "Request started")
        return dict(request)

    def _record_step(self, request_id: int, step: str, detail: str) -> None:
        self.steps.append(
            {
                "request_id": request_id,
                "step": step,
                "reached_at": datetime.now(UTC).replace(tzinfo=None),
                "detail": detail,
            }
        )

    def mark_request_step(
        self,
        request_id: int,
        *,
        step: str,
        status: str | None = None,
        fields: dict[str, Any] | None = None,
        detail: str = "",
    ) -> dict[str, Any] | None:
        request = self.requests.get(request_id)
        if request is None:
            return None
        request["step"] = step
        if status is not None:
            request["status"] = status
        for key, value in (fields or {}).items():
            request[key] = value
        request["updated_at"] = datetime.now(UTC).replace(tzinfo=None)
        self._record_step(request_id, step, detail)
        return dict(request)

    def issue_code(self, values: dict[str, Any]) -> dict[str, Any] | None:
        request = self.requests.get(values["request_id"])
        if request is None:
            return None
        last = request["code_last_generated_at"]
        if last is not None:
            elapsed = (datetime.now(UTC).replace(tzinfo=None) - last).total_seconds()
            if elapsed < 10:
                return None
        request["code_token_hash"] = values["code_token_hash"]
        request["code_value"] = values["code_value"]
        request["code_generated_at"] = datetime.now(UTC).replace(tzinfo=None)
        request["code_last_generated_at"] = datetime.now(UTC).replace(tzinfo=None)
        request["code_expires_at"] = values["code_expires_at"]
        request["code_roll_count"] += 1
        self._record_step(request["id"], "team_code", "Verification code generated")
        return dict(request)

    def expire_stale_requests(self) -> int:
        self.expired_sweeps += 1
        return 0

    def cancel_open_requests_for_user(self, community_user_id: int) -> int:
        count = 0
        for request in self.requests.values():
            if (
                request["community_user_id"] == community_user_id
                and request["status"] in ("draft", "in_progress")
            ):
                request["status"] = "cancelled"
                request["code_token_hash"] = None
                count += 1
        return count

    def clear_codes_for_user(self, community_user_id: int) -> int:
        count = 0
        for request in self.requests.values():
            if request["community_user_id"] == community_user_id and request["code_token_hash"]:
                request["code_token_hash"] = None
                request["code_value"] = None
                count += 1
        return count

    # -- admin --------------------------------------------------------------

    def list_admin_requests(self, **_: Any) -> tuple[list[dict[str, Any]], int]:
        rows = [dict(request) for request in self.requests.values()]
        rows.sort(key=lambda row: (row["status"] != "submitted", row["id"]))
        return rows, len(rows)

    def list_request_history(self, **_: Any) -> list[dict[str, Any]]:
        return [dict(request) for request in self.requests.values()]

    def list_request_steps(self, request_id: int) -> list[dict[str, Any]]:
        return [step for step in self.steps if step["request_id"] == request_id]

    def approve_request(self, values: dict[str, Any]) -> dict[str, Any] | None:
        if self.conflict_on_approve:
            raise ActiveLinkConflictError("conflict")
        request = self.requests.get(values["request_id"])
        if request is None or request["status"] != "submitted":
            return None
        link = self._add_link(values)
        request["status"] = "approved"
        request["link_id"] = link["id"]
        request["decided_at"] = datetime.now(UTC).replace(tzinfo=None)
        request["decided_by_admin"] = values["admin_username"]
        request["admin_note"] = values.get("note")
        request["code_token_hash"] = None
        self._record_step(request["id"], "approved", "Approved")
        return link

    def reject_request(self, values: dict[str, Any]) -> dict[str, Any] | None:
        request = self.requests.get(values["request_id"])
        if request is None or request["status"] != "submitted":
            return None
        request["status"] = "rejected"
        request["decided_at"] = datetime.now(UTC).replace(tzinfo=None)
        request["decided_by_admin"] = values["admin_username"]
        request["rejection_category"] = values.get("category")
        request["rejection_reason"] = values.get("reason")
        request["admin_note"] = values.get("note")
        request["code_token_hash"] = None
        self._record_step(request["id"], "rejected", "Rejected")
        return {"id": request["id"], "status": "rejected"}

    def set_request_status(self, request_id: int, status: str) -> dict[str, Any] | None:
        request = self.requests.get(request_id)
        if request is None:
            return None
        request["status"] = status
        request["code_token_hash"] = None
        self._record_step(request_id, status, "Status changed")
        return dict(request)

    def set_appointment(self, values: dict[str, Any]) -> dict[str, Any] | None:
        request = self.requests.get(values["request_id"])
        if request is None or request["verification_method"] != "discord_screen_share":
            return None
        request["appointment_status"] = values["appointment_status"]
        request["appointment_at"] = values["appointment_at"]
        request["appointment_note"] = values.get("appointment_note")
        self._record_step(request["id"], "discord_schedule", "Appointment updated")
        return {"id": request["id"], "status": values["appointment_status"]}

    def find_conflicts(self, player_name_norm: str) -> dict[str, Any]:
        active = [
            link
            for link in self.links.values()
            if link["player_name_norm"] == player_name_norm and link["status"] == "active"
        ]
        claimants = {
            request["community_user_id"]
            for request in self.requests.values()
            if request["player_name_norm"] == player_name_norm
            and request["status"] in ("draft", "in_progress", "submitted")
        }
        return {
            "active_links": len(active),
            "open_requests": sum(
                1
                for request in self.requests.values()
                if request["player_name_norm"] == player_name_norm
                and request["status"] == "submitted"
            ),
            "competing_claimants": len(claimants),
        }


class RecordingActivityLog:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def log_action(
        self,
        admin_username: str,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        entity_name: str | None = None,
        note: str | None = None,
    ) -> None:
        self.entries.append(
            {
                "admin_username": admin_username,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity_name": entity_name,
                "note": note,
            }
        )


class RecordingNotifications:
    def __init__(self) -> None:
        self.sent: list[tuple[int, str, str]] = []

    def notify(self, community_user_id: int, notification_type: str, message: str) -> None:
        self.sent.append((community_user_id, notification_type, message))


def _make_service(
    *,
    repository: FakeHcr2LinkRepository | None = None,
    settings: Settings | None = None,
) -> tuple[Hcr2LinkService, FakeHcr2LinkRepository, RecordingActivityLog, RecordingNotifications]:
    repo = repository or FakeHcr2LinkRepository()
    log = RecordingActivityLog()
    notifications = RecordingNotifications()
    service = Hcr2LinkService(
        repository=repo,
        settings=settings or _settings(),
        activity_log=log,  # type: ignore[arg-type]
        notification_service=notifications,  # type: ignore[arg-type]
        # An unconfigured DSN makes the rate limiter fail open instead of
        # quietly persisting counters in whatever development database the
        # ambient settings point at, which would otherwise couple these unit
        # tests to a real Postgres and to each other's call counts.
        config=DatabaseConfig(dsn=""),
    )
    return service, repo, log, notifications


def _run_team_wizard(service: Hcr2LinkService, user_id: int = 1, name: str = "Demo Driver") -> dict:
    service.start_request(user_id, name)
    service.choose_method(user_id, "team")
    service.confirm_team_joined(user_id)
    service.generate_code(user_id)
    service.confirm_code_sent(user_id, visibility_confirmed=True)
    return service.submit_request(user_id, instructions_followed=True, method_steps_completed=True)


# -- configuration ---------------------------------------------------------


def test_config_exposes_team_details_and_owner_handles() -> None:
    service, *_ = _make_service()

    config = service.get_config()

    assert config["team"]["available"] is True
    assert config["team"]["team_name"] == "hcr2xyz verify"
    assert config["team"]["team_password"] == "letmein"
    assert config["team"]["requires_leaving_current_team"] is True
    assert config["team"]["supports_chinese_version"] is False
    assert config["discord"]["requires_microphone"] is False
    assert config["discord"]["requires_speaking"] is False
    assert config["discord"]["owner_handles"] == ["nipatsuyt", "titaniumhcr2", "yazi.arod"]
    assert config["automatic_verification"] is False


def test_config_reports_team_method_unavailable_when_unconfigured() -> None:
    service, *_ = _make_service(settings=_settings(HCR2_LINK_VERIFICATION_TEAM_NAME=""))

    config = service.get_config()

    assert config["team"]["available"] is False
    with pytest.raises(CommunityProfileError) as excinfo:
        service.choose_method(1, "team")
    assert excinfo.value.status_code == 503


# -- player name dropdown --------------------------------------------------


def test_search_only_returns_eligible_names() -> None:
    repo = FakeHcr2LinkRepository(eligible=("Demo Driver", "Other"))
    service, *_ = _make_service(repository=repo)

    result = service.search_players(search="demo", limit=20, offset=0)

    assert [row["name_player"] for row in result["players"]] == ["Demo Driver"]
    assert result["count"] == 1
    assert "submitter" not in result["players"][0]
    assert set(result["players"][0]) == {"id_player", "name_player", "record_count"}


def test_start_request_rejects_a_name_with_no_world_record() -> None:
    service, *_ = _make_service()

    with pytest.raises(CommunityProfileError) as excinfo:
        service.start_request(1, "Never Had A Record")

    assert excinfo.value.message == INELIGIBLE_NAME_ERROR


def test_start_request_rejects_an_arbitrary_name_submitted_directly() -> None:
    # Bypassing the dropdown must not help: the backend revalidates.
    service, repo, *_ = _make_service()

    with pytest.raises(CommunityProfileError):
        service.start_request(1, "Some Random Name")

    assert repo.requests == {}


def test_start_request_rejects_a_name_linked_to_another_account() -> None:
    repo = FakeHcr2LinkRepository()
    service, *_ = _make_service(repository=repo)
    service.start_request(1, "Demo Driver")
    repo._add_link(
        {
            "community_user_id": 99,
            "player_id": 1,
            "player_name": "Demo Driver",
            "player_name_norm": "demo driver",
            "verification_method": "team",
        }
    )

    with pytest.raises(CommunityProfileError) as excinfo:
        service.start_request(2, "Demo Driver")

    assert excinfo.value.message == NAME_TAKEN_ERROR
    # The generic message must not leak the other account's identity.
    assert "99" not in excinfo.value.message


def test_start_request_is_idempotent_for_the_same_name() -> None:
    service, *_ = _make_service()

    first = service.start_request(1, "Demo Driver")
    second = service.start_request(1, "Demo Driver")

    assert first["resumed"] is False
    assert second["resumed"] is True
    assert first["request"]["id"] == second["request"]["id"]


def test_start_request_requires_unlinking_before_switching_names() -> None:
    repo = FakeHcr2LinkRepository(eligible=("Demo Driver", "Other"))
    service, *_ = _make_service(repository=repo)
    repo._add_link(
        {
            "community_user_id": 1,
            "player_id": 1,
            "player_name": "Demo Driver",
            "player_name_norm": "demo driver",
            "verification_method": "team",
        }
    )

    with pytest.raises(CommunityProfileError) as excinfo:
        service.start_request(1, "Other")

    assert "Unlink" in excinfo.value.message


# -- team method -----------------------------------------------------------


def test_team_wizard_produces_a_submitted_request_and_no_link() -> None:
    service, repo, *_ = _make_service()

    result = _run_team_wizard(service)

    assert result["request"]["status"] == "submitted"
    assert result["automatic_verification"] is False
    assert "awaiting admin review" in result["message"]
    # The critical guarantee: submitting creates no active link at all.
    assert repo.links == {}
    assert service.get_status(1)["link"] is None


def test_generated_code_contains_the_player_name_and_a_random_token() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)

    first = service.generate_code(1)
    second_code = repo.requests[1]["code_value"]

    assert second_code.startswith("Demo Driver:")
    parsed = split_code(second_code)
    assert parsed is not None
    assert parsed.player_name == "Demo Driver"
    assert len(parsed.token) == 8
    assert first["code"] == second_code
    assert first["single_use"] is True
    assert first["previous_code_invalidated"] is True


def test_code_generation_is_rate_limited_by_the_server_side_cooldown() -> None:
    service, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)
    service.generate_code(1)

    # The repository's UPDATE matches zero rows inside the cooldown window, so
    # a client that ignores the countdown still cannot get a second code.
    with pytest.raises(CommunityProfileError) as excinfo:
        service.generate_code(1)

    assert excinfo.value.status_code == 429


def test_rerolling_invalidates_the_previous_code_immediately() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)
    first = service.generate_code(1)
    first_hash = repo.requests[1]["code_token_hash"]

    # Move past the cooldown the same way real time would.
    repo.requests[1]["code_last_generated_at"] -= timedelta(seconds=11)
    second = service.generate_code(1)

    assert second["code"] != first["code"]
    assert second["code_roll_count"] == 2
    # The stored hash tracks the newest code only, so the old one no longer
    # verifies and cannot be reused.
    assert repo.requests[1]["code_token_hash"] != first_hash
    from app.core.verification_code import verify_token

    old_token = split_code(first["code"]).token  # type: ignore[union-attr]
    assert verify_token(old_token, repo.requests[1]["code_token_hash"], "test-secret") is False


def test_only_one_code_hash_is_stored_per_request() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)
    service.generate_code(1)

    hashes = [request["code_token_hash"] for request in repo.requests.values()]
    assert len([value for value in hashes if value]) == 1


def test_code_hash_is_keyed_with_the_configured_secret() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)
    state = service.generate_code(1)

    stored = repo.requests[1]["code_token_hash"]
    token = split_code(state["code"]).token  # type: ignore[union-attr]
    assert stored == hash_token(token, "test-secret")
    assert token not in stored


def test_team_wizard_blocks_submission_until_steps_are_claimed() -> None:
    service, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")

    with pytest.raises(CommunityProfileError):
        service.submit_request(1, instructions_followed=True, method_steps_completed=True)

    service.confirm_team_joined(1)
    with pytest.raises(CommunityProfileError):
        service.submit_request(1, instructions_followed=True, method_steps_completed=True)

    service.generate_code(1)
    with pytest.raises(CommunityProfileError):
        service.submit_request(1, instructions_followed=True, method_steps_completed=True)


def test_code_sent_requires_confirming_the_code_was_visible() -> None:
    service, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)
    service.generate_code(1)

    with pytest.raises(CommunityProfileError) as excinfo:
        service.confirm_code_sent(1, visibility_confirmed=False)

    assert "visible" in excinfo.value.message


def test_censored_player_names_cannot_be_used_in_a_code() -> None:
    repo = FakeHcr2LinkRepository(eligible=("Bad*Name",))
    service, *_ = _make_service(repository=repo)
    service.start_request(1, "Bad*Name")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)

    with pytest.raises(CommunityProfileError) as excinfo:
        service.generate_code(1)

    assert "censored" in excinfo.value.message


# -- discord method --------------------------------------------------------


def test_discord_method_requires_no_team_change_and_records_claims() -> None:
    service, repo, *_ = _make_service()

    service.start_request(1, "Demo Driver")
    service.choose_method(1, "discord_screen_share")
    service.confirm_discord_joined(1)
    service.confirm_contacted_owner(1)
    service.confirm_discord_ready(1)
    result = service.submit_request(
        1, instructions_followed=True, method_steps_completed=True
    )

    assert result["request"]["status"] == "submitted"
    request = repo.requests[1]
    assert request["discord_joined_at"] is not None
    assert request["contacted_owner_at"] is not None


def test_discord_method_is_rejected_for_a_team_request() -> None:
    service, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")

    with pytest.raises(CommunityProfileError):
        service.confirm_discord_joined(1)


# -- challenge method ------------------------------------------------------


def _challenge_settings(**overrides: Any) -> Settings:
    return _settings(HCR2_LINK_CHALLENGE_ENABLED=True, **overrides)


def test_challenge_method_is_unconfigured_until_it_is_enabled() -> None:
    service, *_ = _make_service()

    assert service.get_config()["challenge"]["available"] is False

    service.start_request(1, "Demo Driver")
    with pytest.raises(CommunityProfileError) as excinfo:
        service.choose_method(1, "playhcr_challenge")

    assert excinfo.value.status_code == 503


def test_config_describes_the_challenge_method() -> None:
    service, *_ = _make_service(
        settings=_challenge_settings(HCR2_LINK_CHALLENGE_INSTRUCTIONS="Use the jeep.")
    )

    challenge = service.get_config()["challenge"]

    assert challenge["available"] is True
    assert challenge["min_distance_m"] == 1
    assert challenge["max_distance_m"] == 2000
    assert challenge["link_prefix"] == "https://playhcr.com/challenge?id="
    assert challenge["instructions"] == "Use the jeep."
    assert challenge["review"] == "manual"


def test_choosing_the_challenge_method_assigns_a_distance_in_range() -> None:
    service, repo, *_ = _make_service(settings=_challenge_settings())

    service.start_request(1, "Demo Driver")
    result = service.choose_method(1, "playhcr_challenge")

    distance = repo.requests[1]["challenge_distance_m"]
    assert 1 <= distance <= 2000
    assert repo.requests[1]["step"] == "challenge_assign"
    # The distance is the member's to read, not a secret, so it is in the view.
    assert result["request"]["challenge_distance_m"] == distance


def test_the_assigned_distance_cannot_be_re_rolled() -> None:
    service, repo, *_ = _make_service(settings=_challenge_settings())

    service.start_request(1, "Demo Driver")
    service.choose_method(1, "playhcr_challenge")
    assigned = repo.requests[1]["challenge_distance_m"]

    for _ in range(5):
        service.choose_method(1, "playhcr_challenge")

    assert repo.requests[1]["challenge_distance_m"] == assigned


def test_the_distance_respects_a_configured_maximum() -> None:
    service, repo, *_ = _make_service(
        settings=_challenge_settings(HCR2_LINK_CHALLENGE_MAX_DISTANCE_M=50)
    )

    service.start_request(1, "Demo Driver")
    service.choose_method(1, "playhcr_challenge")

    assert 1 <= repo.requests[1]["challenge_distance_m"] <= 50


def test_challenge_link_is_stored_and_clears_completion() -> None:
    service, repo, *_ = _make_service(settings=_challenge_settings())

    service.start_request(1, "Demo Driver")
    service.choose_method(1, "playhcr_challenge")
    result = service.confirm_challenge_link(
        1, challenge_url="https://playhcr.com/challenge?id=abc123"
    )

    request = repo.requests[1]
    assert request["challenge_url"] == "https://playhcr.com/challenge?id=abc123"
    assert request["challenge_id"] == "abc123"
    assert request["challenge_confirmed_at"] is not None
    assert request["step"] == "challenge_link"
    assert result["request"]["challenge_link_claimed"] is True


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "http://playhcr.com/challenge?id=abc123",
        "https://playhcr.com.evil.example/challenge?id=abc123",
        "https://playhcr.com/profile/player",
        "https://playhcr.com/challenge?user=abc123",
        "https://playhcr.com/challenge?id=",
        "https://evil.example/https://playhcr.com/challenge?id=abc123",
    ],
)
def test_only_a_playhcr_challenge_link_is_accepted(url: str) -> None:
    service, repo, *_ = _make_service(settings=_challenge_settings())

    service.start_request(1, "Demo Driver")
    service.choose_method(1, "playhcr_challenge")

    with pytest.raises(CommunityProfileError):
        service.confirm_challenge_link(1, challenge_url=url)

    assert repo.requests[1]["challenge_url"] is None
    assert repo.requests[1]["challenge_confirmed_at"] is None


def test_a_pasted_link_with_trailing_sentence_punctuation_is_normalized() -> None:
    service, repo, *_ = _make_service(settings=_challenge_settings())

    service.start_request(1, "Demo Driver")
    service.choose_method(1, "playhcr_challenge")
    service.confirm_challenge_link(
        1, challenge_url="  https://playhcr.com/challenge?id=abc123.  "
    )

    assert repo.requests[1]["challenge_id"] == "abc123"


def test_the_challenge_link_is_rejected_for_a_team_request() -> None:
    service, *_ = _make_service(settings=_challenge_settings())
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")

    with pytest.raises(CommunityProfileError):
        service.confirm_challenge_link(
            1, challenge_url="https://playhcr.com/challenge?id=abc123"
        )


def test_a_challenge_request_cannot_be_submitted_without_a_link() -> None:
    service, *_ = _make_service(settings=_challenge_settings())
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "playhcr_challenge")

    with pytest.raises(CommunityProfileError) as excinfo:
        service.submit_request(1, instructions_followed=True, method_steps_completed=True)

    assert excinfo.value.status_code == 409
    assert "playhcr.com challenge" in excinfo.value.message


def test_a_challenge_request_is_never_approved_automatically() -> None:
    service, repo, *_ = _make_service(settings=_challenge_settings())
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "playhcr_challenge")
    service.confirm_challenge_link(1, challenge_url="https://playhcr.com/challenge?id=abc123")

    result = service.submit_request(1, instructions_followed=True, method_steps_completed=True)

    assert result["request"]["status"] == "submitted"
    assert result["automatic_verification"] is False
    assert repo.links == {}


def test_an_unknown_stored_method_cannot_be_submitted() -> None:
    service, repo, *_ = _make_service(settings=_challenge_settings())
    service.start_request(1, "Demo Driver")
    repo.requests[1]["verification_method"] = "carrier_pigeon"

    with pytest.raises(CommunityProfileError) as excinfo:
        service.submit_request(1, instructions_followed=True, method_steps_completed=True)

    assert excinfo.value.status_code == 409


def test_submit_requires_following_the_instructions() -> None:
    service, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "discord_screen_share")
    service.confirm_discord_joined(1)
    service.confirm_contacted_owner(1)
    service.confirm_discord_ready(1)

    with pytest.raises(CommunityProfileError) as excinfo:
        service.submit_request(1, instructions_followed=False, method_steps_completed=True)

    assert "followed" in excinfo.value.message


# -- request lifecycle -----------------------------------------------------


def test_a_submitted_request_cannot_be_edited() -> None:
    service, *_ = _make_service()
    _run_team_wizard(service)

    with pytest.raises(CommunityProfileError) as excinfo:
        service.confirm_team_joined(1)

    assert excinfo.value.status_code == 409


def test_stale_request_is_expired_when_status_is_read() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    repo.requests[1]["expires_at"] = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)

    status = service.get_status(1)

    assert status["request"]["status"] == "expired"


def test_cancelling_a_request_invalidates_its_code() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)
    service.generate_code(1)

    service.cancel_request(1)

    assert repo.requests[1]["status"] == "cancelled"
    assert repo.requests[1]["code_token_hash"] is None


def test_resubmitting_after_rejection_increments_the_attempt_count() -> None:
    service, repo, *_ = _make_service()
    _run_team_wizard(service)
    service.reject_request(
        1,
        admin_username="mod",
        category="code_not_visible",
        reason="We could not see the code in team chat.",
    )

    restarted = service.start_request(1, "Demo Driver")

    assert restarted["request"]["attempt_count"] == 2
    assert restarted["request"]["is_resubmission"] is True
    assert restarted["request"]["supersedes_request_id"] == 1


def test_too_many_open_requests_are_refused() -> None:
    repo = FakeHcr2LinkRepository(eligible=("A Name", "B Name"))
    service, *_ = _make_service(
        repository=repo,
        settings=_settings(HCR2_LINK_MAX_OPEN_REQUESTS="1"),
    )
    service.start_request(1, "A Name")

    with pytest.raises(CommunityProfileError) as excinfo:
        service.start_request(1, "B Name")

    assert "unfinished request" in excinfo.value.message


# -- user-facing payload privacy -------------------------------------------


def test_user_view_never_exposes_security_or_admin_metadata() -> None:
    service, *_ = _make_service()
    _run_team_wizard(service)
    service.reject_request(
        1,
        admin_username="mod",
        category="code_not_visible",
        reason="Not visible",
        note="internal note",
    )

    view = service.get_status(1)["history"][0]

    for leaked in (
        "code_token_hash",
        "admin_note",
        "rejection_reason",
        "decided_by_admin",
        "discord_id",
    ):
        assert leaked not in view
    assert view["rejection_category"] == "code_not_visible"


# -- admin review ----------------------------------------------------------


def test_only_a_submitted_request_can_be_reviewed() -> None:
    service, *_ = _make_service()
    service.start_request(1, "Demo Driver")

    with pytest.raises(CommunityProfileError) as excinfo:
        service.approve_request(1, admin_username="mod")

    assert excinfo.value.status_code == 409


def test_approval_creates_the_active_link_and_audits_it() -> None:
    service, repo, log, notifications = _make_service()
    _run_team_wizard(service)

    result = service.approve_request(1, admin_username="mod", note="Saw the code")

    assert result["link"]["status"] == "active"
    assert result["link"]["player_name"] == "Demo Driver"
    assert result["link"]["approved_by_admin"] == "mod"
    assert service.get_status(1)["link"]["player_name"] == "Demo Driver"
    assert any(entry["action"] == "request_approved" for entry in log.entries)
    assert any(kind == "hcr2_link_approved" for _, kind, _ in notifications.sent)


def test_approval_revalidates_the_name_against_the_records_database() -> None:
    # The record can disappear between submitting and approving.
    service, repo, *_ = _make_service()
    _run_team_wizard(service)
    repo.eligible.clear()

    with pytest.raises(CommunityProfileError) as excinfo:
        service.approve_request(1, admin_username="mod")

    assert excinfo.value.message == INELIGIBLE_NAME_ERROR
    assert repo.links == {}


def test_approval_reports_a_duplicate_active_link_generically() -> None:
    service, repo, *_ = _make_service()
    _run_team_wizard(service)
    repo.conflict_on_approve = True

    with pytest.raises(CommunityProfileError) as excinfo:
        service.approve_request(1, admin_username="mod")

    assert excinfo.value.message == NAME_TAKEN_ERROR
    assert excinfo.value.status_code == 409


def test_rejection_requires_a_category_and_a_reason() -> None:
    service, *_ = _make_service()
    _run_team_wizard(service)

    with pytest.raises(CommunityProfileError):
        service.reject_request(1, admin_username="mod", category="nope", reason="x")
    with pytest.raises(CommunityProfileError):
        service.reject_request(1, admin_username="mod", category="other", reason="   ")


def test_rejection_notifies_the_member_with_the_reason() -> None:
    service, _, log, notifications = _make_service()
    _run_team_wizard(service)

    service.reject_request(
        1,
        admin_username="mod",
        category="code_not_visible",
        reason="The code was censored in team chat.",
    )

    message = next(
        message for _, kind, message in notifications.sent if kind == "hcr2_link_rejected"
    )
    assert "censored" in message
    assert any(entry["action"] == "request_rejected" for entry in log.entries)


def test_appointment_updates_require_the_discord_method() -> None:
    service, *_ = _make_service()
    _run_team_wizard(service)

    with pytest.raises(CommunityProfileError) as excinfo:
        service.set_appointment(
            1, admin_username="mod", appointment_status="scheduled", appointment_at=None
        )

    assert excinfo.value.status_code == 409


def test_appointment_accepts_every_documented_status() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "discord_screen_share")
    service.confirm_discord_joined(1)
    service.confirm_contacted_owner(1)
    service.confirm_discord_ready(1)
    service.submit_request(1, instructions_followed=True, method_steps_completed=True)

    for status in (
        "waiting_contact",
        "awaiting_scheduling",
        "scheduled",
        "awaiting_screen_share",
        "awaiting_decision",
        "cancelled",
    ):
        service.set_appointment(
            1,
            admin_username="mod",
            appointment_status=status,
            appointment_at=datetime(2026, 10, 20, 18, 30),
        )
        assert repo.requests[1]["appointment_status"] == status


def test_request_retry_reopens_the_request_without_deciding_it() -> None:
    service, _, log, _ = _make_service()
    _run_team_wizard(service)

    service.request_retry(1, admin_username="mod", note="Please reroll the code")

    assert service.get_status(1)["request"]["status"] == "in_progress"
    assert any(entry["action"] == "request_retry_requested" for entry in log.entries)


def test_retry_rejected_by_the_database_layer_is_reported_as_generic() -> None:
    service, *_ = _make_service()

    with pytest.raises(CommunityProfileError) as excinfo:
        service.request_retry(999, admin_username="mod")

    assert excinfo.value.status_code == 404


def test_admin_can_cancel_and_expire_a_request() -> None:
    service, repo, log, _ = _make_service()
    _run_team_wizard(service)

    service.set_terminal_status(1, status="cancelled", admin_username="mod", note="Duplicate")

    assert repo.requests[1]["status"] == "cancelled"
    assert any(entry["action"] == "request_cancelled" for entry in log.entries)


def test_terminal_status_rejects_unsupported_values() -> None:
    service, *_ = _make_service()
    _run_team_wizard(service)

    with pytest.raises(CommunityProfileError):
        service.set_terminal_status(1, status="approved", admin_username="mod")


# -- link management -------------------------------------------------------


def test_self_unlink_is_immediate_and_audited() -> None:
    service, repo, log, notifications = _make_service()
    _run_team_wizard(service)
    service.approve_request(1, admin_username="mod")

    service.unlink(1)

    assert service.get_status(1)["link"] is None
    assert repo.links[1]["status"] == "revoked"
    assert any(entry["action"] == "link_revoked" for entry in log.entries)
    assert any(kind == "hcr2_link_revoked" for _, kind, _ in notifications.sent)


def test_unlink_requires_an_existing_link() -> None:
    service, *_ = _make_service()

    with pytest.raises(CommunityProfileError) as excinfo:
        service.unlink(1)

    assert excinfo.value.status_code == 404


def test_admin_link_status_change_requires_a_reason() -> None:
    service, *_ = _make_service()
    _run_team_wizard(service)
    service.approve_request(1, admin_username="mod")

    with pytest.raises(CommunityProfileError):
        service.set_link_status(1, status="revoked", admin_username="mod", reason="  ")

    result = service.set_link_status(
        1, status="revoked", admin_username="mod", reason="Player asked us to remove it"
    )

    assert result["link"]["status"] == "revoked"


def test_admin_can_suspend_and_restore_a_link() -> None:
    service, *_ = _make_service()
    _run_team_wizard(service)
    service.approve_request(1, admin_username="mod")

    service.set_link_status(1, status="suspended", admin_username="mod", reason="Under review")
    assert service.get_status(1)["link"] is None

    service.set_link_status(1, status="active", admin_username="mod")
    assert service.get_status(1)["link"]["player_name"] == "Demo Driver"


def test_conflicting_claims_are_surfaced_for_a_name() -> None:
    repo = FakeHcr2LinkRepository(eligible=("Demo Driver",))
    service, *_ = _make_service(repository=repo)
    service.start_request(1, "Demo Driver")
    repo.requests[1]["player_name_norm"] = "demo driver"

    conflicts = service.find_conflicts("Demo Driver")

    assert conflicts["competing_claimants"] == 1
    assert conflicts["active_links"] == 0


def test_listing_requests_sweeps_expired_rows() -> None:
    service, repo, *_ = _make_service()

    service.list_requests(status=None, method=None, search=None, limit=20, offset=0)

    assert repo.expired_sweeps == 1

# -- timestamps handed to the browser --------------------------------------


def test_timestamps_are_serialized_as_explicit_utc() -> None:
    # The database stores naive UTC, and JavaScript parses a string with no
    # timezone designator as *local* time. Without the trailing Z a 15 minute
    # code expiry read as local time was already in the past on any browser
    # east of UTC, so the wizard reported the code expired immediately.
    service, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)
    state = service.generate_code(1)
    view = service.get_status(1)["request"]

    for payload in (state, view):
        for key, value in payload.items():
            if key.endswith("_at") and value is not None:
                assert str(value).endswith("Z"), f"{key}={value!r} is not unambiguously UTC"

    assert state["code_expires_in_seconds"] > 0


def test_code_expiry_seconds_stay_positive_just_after_generation() -> None:
    service, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)

    state = service.generate_code(1)

    assert state["code_expired"] is False
    assert 0 < state["code_expires_in_seconds"] <= service.settings.hcr2_link_code_ttl_seconds


def test_expired_code_is_reported_as_expired() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)
    service.generate_code(1)
    repo.requests[1]["code_expires_at"] = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)
    )

    assert service.code_state(repo.requests[1])["code_expired"] is True


# -- server-side step stays truthful ---------------------------------------


def test_new_request_starts_past_the_player_name_step() -> None:
    # The name is already validated when the request is created, so storing
    # "select_player" made the server disagree with the wizard and the frontend
    # snapped back a step after every Continue.
    service, repo, *_ = _make_service()

    service.start_request(1, "Demo Driver")

    assert repo.requests[1]["step"] == "choose_method"


def test_choosing_a_method_moves_the_stored_step_into_the_verify_stage() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")

    service.choose_method(1, "team")
    assert repo.requests[1]["step"] == "team_join"

    repo.requests[1]["step"] = "choose_method"
    service.choose_method(1, "discord_screen_share")
    assert repo.requests[1]["step"] == "discord_join"


def test_stored_step_tracks_the_wizard_through_submission() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    assert repo.requests[1]["step"] == "choose_method"

    service.choose_method(1, "team")
    assert repo.requests[1]["step"] == "team_join"

    service.confirm_team_joined(1)
    assert repo.requests[1]["step"] == "team_join"

    service.generate_code(1)
    assert repo.requests[1]["step"] == "team_join"

    service.confirm_code_sent(1, visibility_confirmed=True)
    assert repo.requests[1]["step"] == "team_sent"

    service.submit_request(1, instructions_followed=True, method_steps_completed=True)
    assert repo.requests[1]["step"] == "summary"
    assert repo.requests[1]["status"] == "submitted"


def test_resuming_an_unfinished_request_reports_the_right_step() -> None:
    service, repo, *_ = _make_service()
    service.start_request(1, "Demo Driver")
    service.choose_method(1, "team")
    service.confirm_team_joined(1)

    resumed = service.get_status(1)["request"]

    assert resumed["step"] == "team_join"
    assert resumed["status"] == "in_progress" or resumed["status"] == "draft"


# -- live vs decided requests ---------------------------------------------


def test_status_flags_whether_the_request_is_still_resumable() -> None:
    service, *_ = _make_service()

    assert service.get_status(1)["request_is_live"] is False

    service.start_request(1, "Demo Driver")
    assert service.get_status(1)["request_is_live"] is True


def test_submitted_request_is_still_live() -> None:
    service, *_ = _make_service()
    _run_team_wizard(service)

    status = service.get_status(1)

    assert status["request_is_live"] is True
    assert status["request"]["status"] == "submitted"


def test_approved_request_is_no_longer_live() -> None:
    # The frontend used to treat any returned request as resumable, so after an
    # approval the wizard kept holding a finished request.
    service, *_ = _make_service()
    _run_team_wizard(service)
    service.approve_request(1, admin_username="mod")

    status = service.get_status(1)

    assert status["request"]["status"] == "approved"
    assert status["request_is_live"] is False


def test_revoked_link_is_reported_as_not_live_so_the_user_can_restart() -> None:
    # Regression: an admin revoking the link left `request` pointing at the
    # still-approved attempt. The wizard treated that as resumable, so the
    # player-name picker refused to open and "Start a new request" did nothing.
    service, *_ = _make_service()
    _run_team_wizard(service)
    service.approve_request(1, admin_username="mod")
    service.unlink(1)

    status = service.get_status(1)

    assert status["link"] is None
    assert status["request_is_live"] is False, "a decided request must not be resumable"

    # And the user can genuinely start over, including on a different name.
    repo = service.repository
    repo.eligible = {"Demo Driver", "Other"}
    fresh = service.start_request(1, "Other")

    assert fresh["resumed"] is False
    assert fresh["request"]["player_name"] == "Other"
    assert fresh["request"]["step"] == "choose_method"
    assert service.get_status(1)["request_is_live"] is True


def test_rejected_and_expired_requests_are_not_live() -> None:
    service, *_ = _make_service()
    _run_team_wizard(service)
    service.reject_request(
        1, admin_username="mod", category="code_not_visible", reason="censored"
    )

    assert service.get_status(1)["request_is_live"] is False

    fresh = service.start_request(1, "Demo Driver")
    service.repository.requests[fresh["request"]["id"]]["expires_at"] = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)
    )
    assert service.get_status(1)["request_is_live"] is False


def test_unlinking_after_an_approval_allows_starting_a_new_one() -> None:
    service, *_ = _make_service()
    _run_team_wizard(service)
    service.approve_request(1, admin_username="mod")

    # Still linked, so a new request on the same name is refused on purpose.
    with pytest.raises(CommunityProfileError):
        service.start_request(1, "Demo Driver")

    service.unlink(1)
    fresh = service.start_request(1, "Demo Driver")

    assert fresh["resumed"] is False
    assert fresh["request"]["attempt_count"] == 2
    assert service.get_status(1)["request_is_live"] is True
