from typing import Any

from app.services.community_account_service import CommunityAccountService

ACCOUNT_FIELDS = (
    "id",
    "discord_id",
    "discord_username",
    "discord_avatar",
    "created_at",
    "updated_at",
)


class FakeCommunityUserRepository:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.next_id = 1

    def get_by_discord_id(self, discord_id: str) -> dict[str, Any] | None:
        for row in self.rows:
            if row["discord_id"] == discord_id:
                return dict(row)
        return None

    def ensure_account(
        self,
        discord_id: str,
        discord_username: str,
        discord_avatar: str | None,
    ) -> dict[str, Any]:
        existing = self.get_by_discord_id(discord_id)
        if existing is None:
            row = {
                "id": self.next_id,
                "discord_id": discord_id,
                "discord_username": discord_username or "",
                "discord_avatar": discord_avatar,
                "created_at": "2026-09-05T10:00:00",
                "updated_at": "2026-09-05T10:00:00",
            }
            self.next_id += 1
            self.rows.append(row)
            return dict(row)

        changed = (
            existing["discord_username"] != (discord_username or "")
            or existing["discord_avatar"] != discord_avatar
        )
        existing["discord_username"] = discord_username or ""
        existing["discord_avatar"] = discord_avatar
        if changed:
            existing["updated_at"] = "2026-09-05T11:00:00"
        return dict(existing)


def _make_service() -> tuple[CommunityAccountService, FakeCommunityUserRepository]:
    repository = FakeCommunityUserRepository()
    return CommunityAccountService(repository), repository


def test_get_or_create_creates_account_when_missing() -> None:
    service, repository = _make_service()

    account = service.get_or_create("123", "Nipa", None)

    assert account["discord_id"] == "123"
    assert account["discord_username"] == "Nipa"
    assert account["discord_avatar"] is None
    assert service.get_account("123") == account
    assert len(repository.rows) == 1


def test_get_or_create_returns_existing_account_for_same_discord_id() -> None:
    service, repository = _make_service()

    first = service.get_or_create("123", "Nipa", None)
    second = service.get_or_create("123", "Nipa", None)

    assert first["id"] == second["id"] == 1
    assert first["created_at"] == second["created_at"] == "2026-09-05T10:00:00"
    assert second["updated_at"] == "2026-09-05T10:00:00"
    assert len(repository.rows) == 1


def test_get_or_create_updates_username_and_avatar_when_changed() -> None:
    service, repository = _make_service()

    first = service.get_or_create("123", "Nipa", None)
    updated = service.get_or_create("123", "Nipa2", "a1b2c3")

    assert first["id"] == updated["id"]
    assert updated["discord_username"] == "Nipa2"
    assert updated["discord_avatar"] == "a1b2c3"
    assert updated["updated_at"] == "2026-09-05T11:00:00"
    assert len(repository.rows) == 1


def test_get_or_create_keeps_account_id_stable_across_updates() -> None:
    service, _ = _make_service()

    created = service.get_or_create("123", "Nipa", None)
    for name, avatar in [("Nipa2", "h1"), ("Nipa3", None), ("Nipa", None)]:
        service.get_or_create("123", name, avatar)

    assert service.get_account("123")["id"] == created["id"]


def test_get_account_returns_none_for_unknown_discord_id() -> None:
    service, _ = _make_service()

    assert service.get_account("missing") is None


def test_account_fields_are_extensible_safe() -> None:
    service, _ = _make_service()
    account = service.get_or_create("123", "Nipa", "avatar-hash")

    for field in ACCOUNT_FIELDS:
        assert field in account