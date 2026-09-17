import io
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from PIL import Image

from app.repositories.community_user import UsernameConflictError
from app.services.community_account_service import (
    MAX_BANNER_DIMENSION,
    CommunityAccountService,
    CommunityProfileError,
)

USER_FIELDS = (
    "id",
    "discord_id",
    "discord_username",
    "discord_avatar",
    "username",
    "last_username_change_at",
    "created_at",
    "updated_at",
    "bio",
    "country",
    "favorite_vehicle_id",
    "favorite_vehicle_name",
    "favorite_map_id",
    "favorite_map_name",
    "profile_public",
    "show_country",
    "show_bio",
    "show_favorite_vehicle",
    "show_favorite_map",
    "show_discord_username",
    "show_discord_avatar",
    "admin_disabled",
    "banner_updated_at",
)


class FakeCommunityUserRepository:
    def __init__(self) -> None:
        self.rows: dict[int, dict[str, Any]] = {}
        self.next_id = 1
        self.banners: dict[int, dict[str, Any]] = {}
        self.username_conflicts: set[str] = set()

    def _new_row(
        self,
        discord_id: str,
        username: str = "",
        avatar: str | None = None,
    ) -> dict[str, Any]:
        return {
            "id": self.next_id,
            "discord_id": discord_id,
            "discord_username": username or discord_id,
            "discord_avatar": avatar,
            "username": None,
            "username_norm": None,
            "last_username_change_at": None,
            "created_at": "2026-09-05T10:00:00",
            "updated_at": "2026-09-05T10:00:00",
            "bio": "",
            "country": None,
            "favorite_vehicle_id": None,
            "favorite_vehicle_name": None,
            "favorite_map_id": None,
            "favorite_map_name": None,
            "profile_public": True,
            "show_country": False,
            "show_bio": False,
            "show_favorite_vehicle": False,
            "show_favorite_map": False,
            "show_discord_username": False,
            "show_discord_avatar": False,
            "admin_disabled": False,
            "banner_content_type": None,
            "banner_updated_at": None,
        }

    def _row_by_discord(self, discord_id: str) -> dict[str, Any] | None:
        for row in self.rows.values():
            if row["discord_id"] == discord_id:
                return row
        return None

    def ensure_account(
        self,
        discord_id: str,
        discord_username: str = "",
        discord_avatar: str | None = None,
    ) -> dict[str, Any]:
        existing = self._row_by_discord(discord_id)
        if existing is None:
            row = self._new_row(discord_id, discord_username, discord_avatar)
            self.rows[row["id"]] = row
            self.next_id += 1
            return dict(row)
        existing["discord_username"] = discord_username or ""
        existing["discord_avatar"] = discord_avatar
        return dict(existing)

    def set_username(
        self,
        user_id: int,
        username: str,
        username_norm: str,
    ) -> dict[str, Any]:
        row = self.rows.get(user_id)
        if row is None:
            return None
        if username_norm in self.username_conflicts:
            raise UsernameConflictError("Username is already taken.")
        if any(
            other["username_norm"] == username_norm
            and other["id"] != user_id
            and other["username"] is not None
            for other in self.rows.values()
        ):
            raise UsernameConflictError("Username is already taken.")
        row["username"] = username
        row["username_norm"] = username_norm
        row["last_username_change_at"] = datetime.now(UTC)
        row["updated_at"] = "2026-09-13T10:00:00"
        return dict(row)

    def get_by_discord_id(self, discord_id: str) -> dict[str, Any] | None:
        row = self._row_by_discord(discord_id)
        return dict(row) if row else None

    def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        row = self.rows.get(user_id)
        return dict(row) if row else None

    def favorite_names(
        self,
        vehicle_id: int | None,
        map_id: int | None,
    ) -> tuple[str | None, str | None]:
        vehicles = {1: "Super Diesel", 2: "Monster Truck"}
        maps = {1: "Countryside", 2: "City"}
        return (
            vehicles.get(vehicle_id) if vehicle_id else None,
            maps.get(map_id) if map_id else None,
        )

    def update_profile(self, discord_id: str, **fields: Any) -> dict[str, Any] | None:
        row = self._row_by_discord(discord_id)
        if row is None:
            return None
        for key, value in fields.items():
            row[key] = value
        vehicles = {1: "Super Diesel", 2: "Monster Truck"}
        maps = {1: "Countryside", 2: "City"}
        row["favorite_vehicle_name"] = vehicles.get(row["favorite_vehicle_id"])
        row["favorite_map_name"] = maps.get(row["favorite_map_id"])
        return dict(row)

    def update_banner(
        self,
        discord_id: str,
        content: bytes,
        content_type: str,
    ) -> dict[str, Any] | None:
        row = self._row_by_discord(discord_id)
        if row is None:
            return None
        self.banners[row["id"]] = {"content": content, "content_type": content_type}
        row["banner_updated_at"] = "2026-09-06T10:00:00"
        row["updated_at"] = "2026-09-06T10:00:00"
        return dict(row)

    def clear_banner(self, discord_id: str) -> dict[str, Any] | None:
        row = self._row_by_discord(discord_id)
        if row is None:
            return None
        self.banners.pop(row["id"], None)
        row["banner_updated_at"] = None
        return dict(row)

    def get_banner(self, user_id: int) -> dict[str, Any] | None:
        stored = self.banners.get(user_id)
        row = self.rows.get(user_id)
        if stored is None or row is None:
            return None
        return {
            "content": stored["content"],
            "content_type": stored["content_type"],
            "public": bool(row["profile_public"]) and not bool(row["admin_disabled"]),
            "discord_id": row["discord_id"],
        }

    def list_members(
        self,
        *,
        search: str | None,
        sort: str,
        country: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        rows = [
            row
            for row in self.rows.values()
            if row["profile_public"]
            and not row["admin_disabled"]
            and row["username"] is not None
        ]
        if country:
            rows = [row for row in rows if row["country"] == country]
        if search:
            rows = [
                row
                for row in rows
                if search.lower() in (row.get("username_norm") or "").lower()
            ]
        rows.sort(key=lambda row: row["created_at"], reverse=True)
        total = len(rows)
        return [dict(row) for row in rows[offset : offset + limit]], total


def _make_service() -> tuple[CommunityAccountService, FakeCommunityUserRepository]:
    repository = FakeCommunityUserRepository()
    return CommunityAccountService(repository), repository


def _onboard(repository: FakeCommunityUserRepository, user_id: int) -> None:
    repository.rows[user_id]["username"] = "Nipa"
    repository.rows[user_id]["username_norm"] = "nipa"


def _tiny_image_bytes(format_name: str = "PNG", size: tuple[int, int] = (8, 8)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, (120, 60, 200)).save(output, format=format_name)
    return output.getvalue()


class Payload:
    bio = ""
    country = None
    favorite_vehicle_id = None
    favorite_map_id = None
    profile_public = True
    show_country = False
    show_bio = False
    show_favorite_vehicle = False
    show_favorite_map = False
    show_discord_username = False
    show_discord_avatar = False


def test_update_profile_persists_fields() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")

    payload = Payload()
    payload.bio = "Hello world"
    payload.country = "FI"
    payload.favorite_vehicle_id = 1
    payload.show_country = True
    payload.show_bio = True
    payload.show_favorite_vehicle = True
    payload.show_discord_username = True

    account = service.update_profile("123", payload)

    assert account["bio"] == "Hello world"
    assert account["country"] == "fi"
    assert account["favorite_vehicle_id"] == 1
    assert account["favorite_vehicle_name"] == "Super Diesel"
    assert account["show_country"] is True
    assert account["show_bio"] is True
    assert account["show_discord_username"] is True
    assert account["show_discord_avatar"] is False


def test_update_profile_rejects_unknown_country() -> None:
    service, repository = _make_service()
    repository.ensure_account("123")

    payload = Payload()
    payload.country = "XX"

    with pytest.raises(CommunityProfileError):
        service.update_profile("123", payload)


def test_update_profile_rejects_unknown_favorite_vehicle() -> None:
    service, repository = _make_service()
    repository.ensure_account("123")

    payload = Payload()
    payload.favorite_vehicle_id = 999
    payload.show_favorite_vehicle = True

    with pytest.raises(CommunityProfileError):
        service.update_profile("123", payload)


def test_update_profile_rejects_overlong_bio() -> None:
    service, repository = _make_service()
    repository.ensure_account("123")

    payload = Payload()
    payload.bio = "x" * 501
    payload.show_bio = True

    with pytest.raises(CommunityProfileError):
        service.update_profile("123", payload)


def test_public_profile_hidden_when_private_for_other_users() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    _onboard(repository, 1)
    repository.rows[1]["profile_public"] = False

    assert service.get_public_profile(1, viewer_discord_id=None) is None
    assert service.get_public_profile(1, viewer_discord_id="other") is None
    owner = service.get_public_profile(1, viewer_discord_id="123")
    assert owner is not None
    assert owner["is_owner"] is True


def test_public_profile_hidden_when_admin_disabled() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    _onboard(repository, 1)
    repository.rows[1]["admin_disabled"] = True

    assert service.get_public_profile(1, viewer_discord_id=None) is None
    assert service.get_public_profile(1, viewer_discord_id="123") is not None


def test_public_profile_hidden_without_username_for_other_users() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")

    assert service.get_public_profile(1, viewer_discord_id=None) is None
    assert service.get_public_profile(1, viewer_discord_id="other") is None
    owner = service.get_public_profile(1, viewer_discord_id="123")
    assert owner is not None


def test_public_profile_visible_when_public() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    _onboard(repository, 1)

    profile = service.get_public_profile(1, viewer_discord_id=None)
    assert profile is not None
    assert profile["is_owner"] is False
    assert "discord_id" not in profile
    assert "discord_username" not in profile
    assert "discord_avatar" not in profile


def test_public_profile_never_leaks_discord_id_or_name_for_others() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    _onboard(repository, 1)
    repository.rows[1]["discord_username"] = "Nipa#1234"

    profile = service.get_public_profile(1, viewer_discord_id="other")

    assert profile is not None
    assert "discord_id" not in profile
    assert "discord_username" not in profile


def test_public_profile_shows_discord_username_when_toggled() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    _onboard(repository, 1)
    repository.rows[1]["discord_username"] = "Nipa#1234"
    repository.rows[1]["show_discord_username"] = True
    repository.rows[1]["discord_avatar"] = "abc"
    repository.rows[1]["show_discord_avatar"] = True

    profile = service.get_public_profile(1, viewer_discord_id="other")

    assert profile["discord_username"] == "Nipa#1234"
    assert profile["discord_avatar"] == "https://cdn.discordapp.com/avatars/123/abc.png"


def test_list_members_trims_hidden_fields() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    _onboard(repository, 1)
    row = repository.rows[1]
    row["bio"] = "secret bio"
    row["country"] = "fi"
    row["show_country"] = True
    row["show_bio"] = False

    result = service.list_members(search=None, sort="new", country=None, limit=20, offset=0)

    member = result["members"][0]
    assert member["bio"] is None
    assert member["country"] == "fi"
    assert member["username"] == "Nipa"
    assert result["count"] == 1


def test_list_members_counts_only_onboarded_public_profiles() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    _onboard(repository, 1)
    repository.ensure_account("456", "Private")
    _onboard(repository, 2)
    repository.rows[2]["profile_public"] = False
    repository.ensure_account("789", "NoName")

    result = service.list_members(search=None, sort="new", country=None, limit=20, offset=0)

    assert result["count"] == 1
    assert [m["username"] for m in result["members"]] == ["Nipa"]


def test_list_members_hides_discord_username_unless_toggled() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    _onboard(repository, 1)
    repository.rows[1]["discord_username"] = "Nipa#1234"
    repository.rows[1]["show_discord_username"] = False

    result = service.list_members(search=None, sort="new", country=None, limit=20, offset=0)

    assert "discord_username" not in result["members"][0]

    repository.rows[1]["show_discord_username"] = True
    result = service.list_members(search=None, sort="new", country=None, limit=20, offset=0)
    assert result["members"][0]["discord_username"] == "Nipa#1234"


def test_set_username_first_time_bypasses_cooldown() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")

    account = service.set_username("123", "  cool   racer  ", cooldown_days=30)

    assert account is not None
    assert account["username"] == "cool racer"
    assert account["last_username_change_at"] is not None


def test_set_username_enforces_cooldown() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    repository.set_username(1, "First", "first")
    repository.rows[1]["last_username_change_at"] = datetime.now(UTC) - timedelta(days=5)

    with pytest.raises(CommunityProfileError) as exc_info:
        service.set_username("123", "Second", cooldown_days=30)
    assert exc_info.value.status_code == 409


def test_set_username_enforces_cooldown_with_naive_timestamp() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    repository.set_username(1, "First", "first")
    naive = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=5)
    repository.rows[1]["last_username_change_at"] = naive

    with pytest.raises(CommunityProfileError) as exc_info:
        service.set_username("123", "Second", cooldown_days=30)
    assert exc_info.value.status_code == 409


def test_set_username_allows_change_after_cooldown() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    repository.set_username(1, "First", "first")
    repository.rows[1]["last_username_change_at"] = datetime.now(UTC) - timedelta(days=31)

    account = service.set_username("123", "Second", cooldown_days=30)

    assert account["username"] == "Second"


def test_set_username_rejects_format() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")

    for bad in ("ab", "a" * 21, "https://evil.example", "has@symbol"):
        with pytest.raises(CommunityProfileError):
            service.set_username("123", bad, cooldown_days=30)


def test_set_username_rejects_reserved_and_profanity() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")

    for bad in ("admin", " hCr2 ", "Official", "shItface"):
        with pytest.raises(CommunityProfileError) as exc_info:
            service.set_username("123", bad, cooldown_days=30)
        assert exc_info.value.message == "This username isn't available. Please choose another one."


def test_set_username_conflict_returns_generic_message() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    repository.set_username(1, "Taker", "taker")
    repository.ensure_account("456", "Other")
    repository.rows[2]["username"] = "taken"

    with pytest.raises(CommunityProfileError) as exc_info:
        service.set_username("456", "Taker", cooldown_days=30)
    assert exc_info.value.status_code == 409
    assert "isn't available" in exc_info.value.message


def test_upload_banner_normalizes_to_webp() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")

    account = service.upload_banner("123", _tiny_image_bytes())

    stored = repository.banners[1]
    assert stored["content_type"] == "image/webp"
    assert stored["content"].startswith(b"RIFF")
    assert account["banner_updated_at"] is not None


def test_upload_banner_downscales_large_images() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")

    wide = _tiny_image_bytes("PNG", size=(4000, 10))
    service.upload_banner("123", wide)

    stored = repository.banners[1]
    with Image.open(io.BytesIO(stored["content"])) as converted:
        assert converted.width <= MAX_BANNER_DIMENSION


def test_upload_banner_rejects_non_image() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")

    with pytest.raises(CommunityProfileError):
        service.upload_banner("123", b"<svg onload=\"alert(1)\"></svg>")


def test_get_banner_respects_privacy() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    repository.ensure_account("456", "Other")
    service.upload_banner("123", _tiny_image_bytes())

    assert service.get_banner(1, viewer_discord_id=None) is not None
    assert service.get_banner(1, viewer_discord_id="other") is not None

    repository.rows[1]["profile_public"] = False
    assert service.get_banner(1, viewer_discord_id=None) is None
    assert service.get_banner(1, viewer_discord_id="other") is None
    assert service.get_banner(1, viewer_discord_id="123") is not None