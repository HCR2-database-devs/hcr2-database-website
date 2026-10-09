from typing import Any

from fastapi.testclient import TestClient

from app.api import dependencies
from app.core.config import Settings, get_settings
from app.main import create_app
from app.services.community_account_service import CommunityAccountService, build_api_profile

API_KEY = "dev-api-key"
ENDPOINT = "/api/v1/community-api/users/1"

_MISSING = object()


def _account(**overrides: Any) -> dict[str, Any]:
    account = {
        "id": 1,
        "discord_id": "10001",
        "discord_username": "Name 10001",
        "discord_avatar": "a_1f2e3a",
        "username": "Nick 1",
        "username_norm": "nick 1",
        "last_username_change_at": "2026-09-01T10:00:00",
        "created_at": "2026-09-05T10:00:00",
        "updated_at": "2026-09-05T10:00:00",
        "bio": "I love Countryside",
        "country": "fi",
        "favorite_vehicle_id": 3,
        "favorite_vehicle_name": "Sand Rail",
        "favorite_map_id": 7,
        "favorite_map_name": "Countryside",
        "profile_public": True,
        "show_bio": True,
        "show_country": True,
        "show_favorite_vehicle": True,
        "show_favorite_map": True,
        "show_discord_username": False,
        "show_discord_avatar": False,
        "admin_disabled": False,
        "banner_updated_at": "2026-09-07T10:00:00",
    }
    account.update(overrides)
    return account


class StubCommunityUserRepository:
    """Feeds the real service so admin_disabled gating is genuinely covered."""

    def __init__(self, account: dict[str, Any] | None) -> None:
        self.account = account

    def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        if self.account is None or self.account["id"] != user_id:
            return None
        return dict(self.account)


def _client(account: Any = _MISSING, api_keys: str = API_KEY) -> TestClient:
    resolved = _account() if account is _MISSING else account
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(API_KEYS=api_keys)
    app.dependency_overrides[dependencies.get_community_account_service] = (
        lambda: CommunityAccountService(StubCommunityUserRepository(resolved))
    )
    return TestClient(app)


def test_community_api_profile_requires_api_key() -> None:
    response = _client().get(ENDPOINT)

    assert response.status_code == 401
    assert response.json() == {"error": "Unauthorized: invalid API key"}


def test_community_api_profile_rejects_unknown_api_key() -> None:
    response = _client().get(f"{ENDPOINT}?api_key=wrong-key")

    assert response.status_code == 401
    assert response.json() == {"error": "Unauthorized: invalid API key"}


def test_community_api_profile_accepts_api_key_query_param() -> None:
    response = _client().get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_community_api_profile_accepts_api_key_header() -> None:
    response = _client().get(ENDPOINT, headers={"X-API-Key": API_KEY})

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_community_api_profile_returns_unknown_user_as_not_found() -> None:
    response = _client(account=None).get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 404


def test_community_api_profile_returns_full_account() -> None:
    response = _client().get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "Nick 1"
    assert body["discord_id"] == "10001"
    assert body["discord_username"] == "Name 10001"
    assert body["bio"] == "I love Countryside"
    assert body["country"] == "fi"
    assert body["favorite_vehicle_id"] == 3
    assert body["favorite_vehicle_name"] == "Sand Rail"
    assert body["favorite_map_id"] == 7
    assert body["favorite_map_name"] == "Countryside"
    assert body["has_banner"] is True
    assert body["banner_updated_at"] == "2026-09-07T10:00:00"


def test_community_api_profile_builds_absolute_avatar_url() -> None:
    response = _client().get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 200
    assert (
        response.json()["discord_avatar"]
        == "https://cdn.discordapp.com/avatars/10001/a_1f2e3a.gif"
    )


def test_community_api_profile_ignores_member_privacy_settings() -> None:
    account = _account(
        profile_public=False,
        show_bio=False,
        show_country=False,
        show_favorite_vehicle=False,
        show_favorite_map=False,
        show_discord_username=False,
        show_discord_avatar=False,
    )
    response = _client(account=account).get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 200
    body = response.json()
    assert body["profile_public"] is False
    assert body["bio"] == "I love Countryside"
    assert body["country"] == "fi"
    assert body["favorite_vehicle_name"] == "Sand Rail"
    assert body["favorite_map_name"] == "Countryside"
    assert body["discord_username"] == "Name 10001"


def test_community_api_profile_marks_private_fields() -> None:
    response = _client().get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 200
    body = response.json()
    # These fields were published by the member.
    assert body["bio_private"] is False
    assert body["country_private"] is False
    assert body["favorite_vehicle_id_private"] is False
    assert body["favorite_vehicle_name_private"] is False
    assert body["favorite_map_id_private"] is False
    assert body["favorite_map_name_private"] is False
    # These were not.
    assert body["discord_username_private"] is True
    assert body["discord_avatar_private"] is True


def test_community_api_profile_echoes_member_visibility_flags() -> None:
    response = _client().get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 200
    body = response.json()
    assert body["show_bio"] is True
    assert body["show_country"] is True
    assert body["show_favorite_vehicle"] is True
    assert body["show_favorite_map"] is True
    assert body["show_discord_username"] is False
    assert body["show_discord_avatar"] is False


def test_community_api_profile_reports_missing_banner() -> None:
    response = _client(account=_account(banner_updated_at=None)).get(
        f"{ENDPOINT}?api_key={API_KEY}"
    )

    assert response.status_code == 200
    assert response.json()["has_banner"] is False


def test_community_api_profile_keeps_null_fields_distinguishable_from_private() -> None:
    client = _client(account=_account(bio="", show_bio=False))
    response = client.get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 200
    body = response.json()
    assert body["bio"] == ""
    assert body["bio_private"] is True


def test_community_api_profile_withholds_admin_disabled_accounts() -> None:
    response = _client(account=_account(admin_disabled=True)).get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 404


def test_community_api_profile_serves_non_onboarded_accounts() -> None:
    response = _client(account=_account(username=None)).get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 200
    assert response.json()["username"] is None


def test_community_api_profile_is_rejected_when_no_keys_configured() -> None:
    response = _client(api_keys="").get(f"{ENDPOINT}?api_key={API_KEY}")

    assert response.status_code == 401


def test_community_api_profile_accepts_any_key_in_the_list() -> None:
    response = _client(api_keys="first-key,second-key").get(f"{ENDPOINT}?api_key=second-key")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_build_api_profile_omits_transform_for_plain_fields() -> None:
    profile = build_api_profile(_account())

    assert profile["id"] == 1
    assert profile["created_at"] == "2026-09-05T10:00:00"
    assert profile["profile_public"] is True
    assert profile["admin_disabled"] is False


def test_build_api_profile_tolerates_missing_optional_columns() -> None:
    profile = build_api_profile({"id": 9, "discord_id": "2", "discord_avatar": None})

    assert profile["id"] == 9
    assert profile["discord_avatar"] is None
    assert profile["has_banner"] is False
    assert profile["country"] is None
    assert profile["country_private"] is True