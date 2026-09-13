from typing import Any

import pytest

from app.services.community_account_service import CommunityProfileError
from app.services.community_moderation_service import CommunityModerationService


class FakeModerationRepository:
    def __init__(self) -> None:
        self.profiles: dict[int, dict[str, Any]] = {}
        self.reports: dict[int, dict[str, Any]] = {}
        self.next_report_id = 1
        self.next_profile_id = 1

    def add_profile(self, username: str) -> dict[str, Any]:
        profile = {
            "id": self.next_profile_id,
            "discord_username": username,
            "discord_avatar": None,
            "created_at": "2026-09-05T10:00:00",
            "updated_at": "2026-09-05T10:00:00",
            "profile_public": True,
            "admin_disabled": False,
        }
        self.profiles[profile["id"]] = profile
        self.next_profile_id += 1
        return profile

    def list_profiles(self, *, search, limit, offset) -> tuple[list[dict[str, Any]], int]:
        rows = [dict(row) for row in self.profiles.values()]
        if search:
            rows = [row for row in rows if search.lower() in row["discord_username"].lower()]
        return rows[offset : offset + limit], len(rows)

    def get_profile(self, user_id: int) -> dict[str, Any] | None:
        row = self.profiles.get(user_id)
        return dict(row) if row else None

    def admin_update_profile(self, user_id: int, **fields: Any) -> dict[str, Any] | None:
        row = self.profiles.get(user_id)
        if row is None:
            return None
        row["bio"] = fields["bio"]
        row["country"] = fields["country"]
        row["favorite_vehicle_id"] = fields["favorite_vehicle_id"]
        row["favorite_map_id"] = fields["favorite_map_id"]
        row["profile_public"] = fields["profile_public"]
        row["show_country"] = fields["show_country"]
        row["show_bio"] = fields["show_bio"]
        row["show_favorite_vehicle"] = fields["show_favorite_vehicle"]
        row["show_favorite_map"] = fields["show_favorite_map"]
        row["discord_username"] = "Name " + str(user_id)
        return dict(row)

    def admin_clear_customization(self, user_id: int) -> dict[str, Any] | None:
        row = self.profiles.get(user_id)
        if row is None:
            return None
        row["discord_username"] = "cleared"
        return dict(row)

    def set_admin_disabled(self, user_id: int, disabled: bool) -> dict[str, Any] | None:
        row = self.profiles.get(user_id)
        if row is None:
            return None
        row["admin_disabled"] = disabled
        row["discord_username"] = "disabled-name" if disabled else "enabled-name"
        return dict(row)

    def create_report(self, target_id, reporter_id, category, reason) -> dict[str, Any] | None:
        for report in self.reports.values():
            if (
                report["community_user_id"] == target_id
                and report["reporter_community_user_id"] == reporter_id
                and report["status"] == "open"
            ):
                return None
        report = {
            "id": self.next_report_id,
            "community_user_id": target_id,
            "reporter_community_user_id": reporter_id,
            "category": category,
            "reason": reason,
            "status": "open",
            "created_at": "2026-09-06T10:00:00",
        }
        self.reports[report["id"]] = report
        self.next_report_id += 1
        return dict(report)

    def list_reports(self, *, status, limit, offset) -> tuple[list[dict[str, Any]], int]:
        rows = [dict(row) for row in self.reports.values()]
        if status:
            rows = [row for row in rows if row["status"] == status]
        return rows[offset : offset + limit], len(rows)

    def get_report(self, report_id: int) -> dict[str, Any] | None:
        row = self.reports.get(report_id)
        return dict(row) if row else None

    def resolve_report(self, report_id, status, admin_username, note) -> dict[str, Any] | None:
        row = self.reports.get(report_id)
        if row is None or row["status"] != "open":
            return None
        row["status"] = status
        row["resolved_by"] = admin_username
        row["resolution_note"] = note
        return dict(row)


class FakeCommunityRepository:
    def favorite_names(
        self,
        vehicle_id: int | None,
        map_id: int | None,
    ) -> tuple[str | None, str | None]:
        return (
            ("Super Diesel" if vehicle_id == 1 else None),
            ("Countryside" if map_id == 1 else None),
        )


class FakeActivityLog:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def log_action(
        self,
        admin_username: str,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        entity_name: str | None = None,
        note: str | None = None,
    ) -> None:
        self.calls.append(
            {
                "admin": admin_username,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity_name": entity_name,
                "note": note,
            }
        )


def _make_service() -> tuple[
    CommunityModerationService,
    FakeModerationRepository,
    FakeActivityLog,
]:
    repository = FakeModerationRepository()
    logging = FakeActivityLog()
    service = CommunityModerationService(repository, FakeCommunityRepository(), logging)
    return service, repository, logging


def _payload(**overrides: Any) -> Any:
    defaults = {
        "bio": "",
        "country": None,
        "favorite_vehicle_id": None,
        "favorite_map_id": None,
        "profile_public": True,
        "show_country": False,
        "show_bio": False,
        "show_favorite_vehicle": False,
        "show_favorite_map": False,
        "category": "other",
        "reason": "",
        "h_captcha_response": "captcha-token",
    }
    defaults.update(overrides)
    return type("Payload", (), defaults)


@pytest.fixture(autouse=True)
def _accept_hcaptcha(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CommunityModerationService, "_verify_hcaptcha", lambda self, token: True)


def test_create_report_succeeds_for_other_users() -> None:
    service, repository, _ = _make_service()
    repository.add_profile("Target")
    repository.add_profile("Reporter")

    report = service.create_report(1, 2, _payload(category="spam", reason="Ads"))

    assert report["status"] == "open"
    assert report["community_user_id"] == 1
    assert report["category"] == "spam"


def test_create_report_rejects_self_report() -> None:
    service, repository, _ = _make_service()
    repository.add_profile("Target")

    with pytest.raises(CommunityProfileError):
        service.create_report(1, 1, _payload(category="other"))


def test_create_report_rejects_unknown_category() -> None:
    service, repository, _ = _make_service()
    repository.add_profile("Target")
    repository.add_profile("Reporter")

    with pytest.raises(CommunityProfileError):
        service.create_report(1, 2, _payload(category="gibberish"))


def test_create_report_requires_valid_hcaptcha(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CommunityModerationService, "_verify_hcaptcha", lambda self, token: False)
    service, repository, _ = _make_service()
    repository.add_profile("Target")
    repository.add_profile("Reporter")

    with pytest.raises(CommunityProfileError) as excinfo:
        service.create_report(1, 2, _payload(category="spam"))
    assert excinfo.value.status_code == 400
    assert repository.reports == {}


def test_create_report_duplicate_open_raises_conflict() -> None:
    service, repository, _ = _make_service()
    repository.add_profile("Target")
    repository.add_profile("Reporter")
    repository.reports[1] = {
        "id": 1,
        "community_user_id": 1,
        "reporter_community_user_id": 2,
        "category": "spam",
        "reason": "",
        "status": "open",
        "created_at": "2026-09-06T10:00:00",
    }
    repository.next_report_id = 2

    with pytest.raises(CommunityProfileError) as excinfo:
        service.create_report(1, 2, _payload(category="spam"))
    assert excinfo.value.status_code == 409


def test_resolve_report_logs_with_note() -> None:
    service, repository, logging = _make_service()
    repository.reports[7] = {
        "id": 7,
        "community_user_id": 1,
        "category": "spam",
        "reason": "",
        "status": "open",
        "created_at": "2026-09-06T10:00:00",
    }

    resolved = service.resolve_report(7, True, "Admin", note="Agreed")

    assert resolved["status"] == "resolved"
    assert logging.calls[-1]["action"] == "report_resolved"
    assert logging.calls[-1]["note"] == "Agreed"


def test_resolve_report_missing_raises() -> None:
    service, repository, _ = _make_service()

    with pytest.raises(CommunityProfileError) as excinfo:
        service.resolve_report(99, True, "Admin")
    assert excinfo.value.status_code == 404


def test_set_disabled_and_enable_log_actions() -> None:
    service, repository, logging = _make_service()
    repository.add_profile("Nipa")

    service.set_disabled(1, True, "Admin", note="Rule break")
    assert logging.calls[-1]["action"] == "disabled"
    assert logging.calls[-1]["note"] == "Rule break"
    assert logging.calls[-1]["entity_type"] == "community_user"

    service.set_disabled(1, False, "Admin")
    assert logging.calls[-1]["action"] == "enabled"


def test_reset_profile_clears_and_logs() -> None:
    service, repository, logging = _make_service()
    repository.add_profile("Nipa")

    updated = service.reset_profile(1, "Admin", note="Reset requested")

    assert updated["discord_username"] == "cleared"
    assert logging.calls[-1]["action"] == "reset"


def test_admin_update_validates_country() -> None:
    service, repository, _ = _make_service()
    repository.add_profile("Nipa")

    with pytest.raises(CommunityProfileError):
        service.update_profile(1, _payload(country="XX"))


def test_admin_update_logs_updated() -> None:
    service, repository, logging = _make_service()
    repository.add_profile("Nipa")

    service.update_profile(1, _payload(bio="Edited"), admin_username="Admin")

    assert logging.calls[-1]["action"] == "updated"
    assert logging.calls[-1]["entity_type"] == "community_user"