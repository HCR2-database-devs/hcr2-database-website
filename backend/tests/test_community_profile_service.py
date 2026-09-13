import io
from typing import Any

import pytest
from PIL import Image

from app.services.community_account_service import (
    CommunityAccountService,
    CommunityProfileError,
    MAX_BANNER_DIMENSION,
)

USER_FIELDS = (
    "id",
    "discord_id",
    "discord_username",
    "discord_avatar",
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
    "admin_disabled",
    "banner_updated_at",
)


class FakeCommunityUserRepository:
    def __init__(self) -> None:
        self.rows: dict[int, dict[str, Any]] = {}
        self.next_id = 1
        self.banners: dict[int, dict[str, Any]] = {}

    def _new_row(self, discord_id: str, username: str = "", avatar: str | None = None) -> dict[str, Any]:
        return {
            "id": self.next_id,
            "discord_id": discord_id,
            "discord_username": username or discord_id,
            "discord_avatar": avatar,
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

    def update_banner(self, discord_id: str, content: bytes, content_type: str) -> dict[str, Any] | None:
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
            if row["profile_public"] and not row["admin_disabled"]
        ]
        if country:
            rows = [row for row in rows if row["country"] == country]
        if search:
            rows = [row for row in rows if search.lower() in row["discord_username"].lower()]
        rows.sort(key=lambda row: row["created_at"], reverse=True)
        total = len(rows)
        return [dict(row) for row in rows[offset : offset + limit]], total


def _make_service() -> tuple[CommunityAccountService, FakeCommunityUserRepository]:
    repository = FakeCommunityUserRepository()
    return CommunityAccountService(repository), repository


def _tiny_image_bytes(format_name: str = "PNG", size: tuple[int, int] = (8, 8)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, (120, 60, 200)).save(output, format=format_name)
    return output.getvalue()


def test_update_profile_persists_fields() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")

    class Payload:
        bio = "Hello world"
        country = "FI"
        favorite_vehicle_id = 1
        favorite_map_id = None
        profile_public = True
        show_country = True
        show_bio = True
        show_favorite_vehicle = True
        show_favorite_map = False

    account = service.update_profile("123", Payload())

    assert account["bio"] == "Hello world"
    assert account["country"] == "fi"
    assert account["favorite_vehicle_id"] == 1
    assert account["favorite_vehicle_name"] == "Super Diesel"
    assert account["show_country"] is True
    assert account["show_bio"] is True


def test_update_profile_rejects_unknown_country() -> None:
    service, repository = _make_service()
    repository.ensure_account("123")

    class Payload:
        bio = ""
        country = "XX"
        favorite_vehicle_id = None
        favorite_map_id = None
        profile_public = True
        show_country = False
        show_bio = False
        show_favorite_vehicle = False
        show_favorite_map = False

    with pytest.raises(CommunityProfileError):
        service.update_profile("123", Payload())


def test_update_profile_rejects_unknown_favorite_vehicle() -> None:
    service, repository = _make_service()
    repository.ensure_account("123")

    class Payload:
        bio = ""
        country = None
        favorite_vehicle_id = 999
        favorite_map_id = None
        profile_public = True
        show_country = False
        show_bio = False
        show_favorite_vehicle = True
        show_favorite_map = False

    with pytest.raises(CommunityProfileError):
        service.update_profile("123", Payload())


def test_update_profile_rejects_overlong_bio() -> None:
    service, repository = _make_service()
    repository.ensure_account("123")

    class Payload:
        bio = "x" * 501
        country = None
        favorite_vehicle_id = None
        favorite_map_id = None
        profile_public = True
        show_country = False
        show_bio = True
        show_favorite_vehicle = False
        show_favorite_map = False

    with pytest.raises(CommunityProfileError):
        service.update_profile("123", Payload())


def test_public_profile_hidden_when_private_for_other_users() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    repository.rows[1]["profile_public"] = False

    assert service.get_public_profile(1, viewer_discord_id=None) is None
    assert service.get_public_profile(1, viewer_discord_id="other") is None
    owner = service.get_public_profile(1, viewer_discord_id="123")
    assert owner is not None
    assert owner["is_owner"] is True


def test_public_profile_hidden_when_admin_disabled() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    repository.rows[1]["admin_disabled"] = True

    assert service.get_public_profile(1, viewer_discord_id=None) is None
    assert service.get_public_profile(1, viewer_discord_id="123") is not None


def test_public_profile_visible_when_public() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")

    profile = service.get_public_profile(1, viewer_discord_id=None)
    assert profile is not None
    assert profile["is_owner"] is False


def test_list_members_trims_hidden_fields() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    row = repository.rows[1]
    row["bio"] = "secret bio"
    row["country"] = "fi"
    row["show_country"] = True
    row["show_bio"] = False

    result = service.list_members(search=None, sort="new", country=None, limit=20, offset=0)

    member = result["members"][0]
    assert member["bio"] is None
    assert member["country"] == "fi"
    assert result["count"] == 1


def test_list_members_counts_only_public_profiles() -> None:
    service, repository = _make_service()
    repository.ensure_account("123", "Nipa")
    repository.ensure_account("456", "Private")
    repository.rows[2]["profile_public"] = False

    result = service.list_members(search=None, sort="new", country=None, limit=20, offset=0)

    assert result["count"] == 1
    assert [m["discord_username"] for m in result["members"]] == ["Nipa"]


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