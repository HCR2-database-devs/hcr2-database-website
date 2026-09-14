from typing import Any

from fastapi.testclient import TestClient

from app.api import dependencies
from app.core.config import Settings, get_settings
from app.core.username_rules import (
    UsernameModerationError,
    UsernameValidationError,
    validate_username,
)
from app.main import create_app
from app.services.community_account_service import CommunityProfileError


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
        self.next_id = 1
        self.banners: dict[int, dict[str, Any]] = {}

    def add_user(
        self,
        discord_id: str,
        public: bool = True,
        username: str | None = None,
        onboarded: bool = True,
    ) -> dict[str, Any]:
        user_id = self.next_id
        user_username = username or f"Nick {user_id}"
        user = {
            "id": user_id,
            "discord_id": discord_id,
            "discord_username": f"Name {discord_id}",
            "discord_avatar": None,
            "username": user_username if onboarded else None,
            "username_norm": user_username.lower() if onboarded else None,
            "last_username_change_at": "2026-09-01T10:00:00" if onboarded else None,
            "created_at": "2026-09-05T10:00:00",
            "updated_at": "2026-09-05T10:00:00",
            "bio": "",
            "country": "fi",
            "profile_public": public,
            "admin_disabled": False,
            "show_country": True,
            "show_discord_username": False,
            "show_discord_avatar": False,
            "banner_updated_at": None,
        }
        self.users[user["id"]] = user
        self.next_id += 1
        return dict(user)

    def get_account(self, discord_id: str) -> dict[str, Any] | None:
        for user in self.users.values():
            if user["discord_id"] == discord_id:
                return dict(user)
        return None

    def get_account_by_id(self, user_id: int) -> dict[str, Any] | None:
        user = self.users.get(user_id)
        return dict(user) if user else None

    def set_username(
        self,
        discord_id: str,
        raw_username: str,
        cooldown_days: int = 30,
    ) -> dict[str, Any] | None:
        user = self.get_account(discord_id)
        if user is None:
            return None
        if user["username"] is not None and user["last_username_change_at"] is not None:
            raise CommunityProfileError(
                f"Your username can only be changed once every {cooldown_days} days.",
                409,
            )
        try:
            username = validate_username(raw_username)
        except (UsernameValidationError, UsernameModerationError) as exc:
            raise CommunityProfileError(exc.message) from None
        if any(
            other["username_norm"] == username.lower()
            and other["id"] != user["id"]
            and other["username"] is not None
            for other in self.users.values()
        ):
            raise CommunityProfileError(
                "This username isn't available. Please choose another one.",
                409,
            )
        user["username"] = username
        user["username_norm"] = username.lower()
        user["last_username_change_at"] = "2026-09-13T10:00:00"
        return dict(user)

    def get_public_profile(
        self,
        user_id: int,
        viewer_discord_id: str | None,
    ) -> dict[str, Any] | None:
        user = self.users.get(user_id)
        if user is None:
            return None
        is_owner = viewer_discord_id is not None and user["discord_id"] == viewer_discord_id
        if not is_owner and (not user["profile_public"] or user["admin_disabled"]):
            return None
        if not is_owner and user.get("username") is None:
            return None
        result = {key: value for key, value in user.items() if key != "discord_id"}
        if not is_owner:
            if not user["show_discord_username"]:
                result.pop("discord_username", None)
            if not user["show_discord_avatar"]:
                result.pop("discord_avatar", None)
        result["is_owner"] = is_owner
        return result

    def get_banner(self, user_id: int, viewer_discord_id: str | None) -> dict[str, Any] | None:
        banner = self.banners.get(user_id)
        user = self.users.get(user_id)
        if banner is None or user is None:
            return None
        is_owner = viewer_discord_id is not None and user["discord_id"] == viewer_discord_id
        if not is_owner and (not user["profile_public"] or user["admin_disabled"]):
            return None
        return {"content": banner["content"], "content_type": banner["content_type"]}

    def update_profile(self, discord_id: str, payload: Any) -> dict[str, Any] | None:
        user = self.get_account(discord_id)
        if user is None:
            return None
        if payload.country == "XX":
            raise CommunityProfileError("Unknown country code.")
        user["country"] = payload.country
        user["bio"] = payload.bio or ""
        return user

    def upload_banner(self, discord_id: str, content: bytes) -> dict[str, Any] | None:
        user = self.get_account(discord_id)
        if user is None:
            return None
        if not content.startswith(b"RIFF"):
            raise CommunityProfileError("The uploaded file is not a valid PNG, JPEG or WebP image.")
        self.banners[user["id"]] = {"content": content, "content_type": "image/webp"}
        user["banner_updated_at"] = "2026-09-06T10:00:00"
        return user

    def clear_banner(self, discord_id: str) -> dict[str, Any] | None:
        user = self.get_account(discord_id)
        if user is None:
            return None
        self.banners.pop(user["id"], None)
        user["banner_updated_at"] = None
        return user

    def list_members(self, **_: Any) -> dict[str, Any]:
        rows = [user for user in self.users.values() if user["profile_public"]]
        return {
            "members": rows,
            "count": len(rows),
            "limit": 20,
            "offset": 0,
            "search": None,
            "sort": "new",
        }


class FakeCommunityModerationService:
    def __init__(self, community: FakeCommunityAccountService) -> None:
        self.community = community
        self.reports: dict[int, dict[str, Any]] = {}
        self.next_report_id = 1

    def get_profile(self, user_id: int) -> dict[str, Any] | None:
        return self.community.get_account_by_id(user_id)

    def list_profiles(self, **_: Any) -> dict[str, Any]:
        return {
            "profiles": list(self.community.users.values()),
            "count": len(self.community.users),
            "limit": 20,
            "offset": 0,
            "search": None,
        }

    def update_profile(
        self,
        user_id: int,
        payload: Any,
        admin_username: str = "",
    ) -> dict[str, Any] | None:
        return self.community.get_account_by_id(user_id)

    def set_disabled(
        self,
        user_id: int,
        disabled: bool,
        admin_username: str = "",
        note: str | None = None,
    ) -> dict[str, Any] | None:
        user = self.community.users.get(user_id)
        if user is None:
            return None
        user["admin_disabled"] = disabled
        return dict(user)

    def reset_profile(
        self,
        user_id: int,
        admin_username: str = "",
        note: str | None = None,
    ) -> dict[str, Any] | None:
        return self.community.get_account_by_id(user_id)

    def set_username(
        self,
        user_id: int,
        raw_username: str,
        admin_username: str = "",
        note: str | None = None,
    ) -> dict[str, Any] | None:
        user = self.community.users.get(user_id)
        if user is None:
            return None
        if any(
            other["username_norm"] == raw_username.strip().lower()
            and other["id"] != user_id
            and other["username"] is not None
            for other in self.community.users.values()
        ):
            raise CommunityProfileError(
                "This username isn't available. Please choose another one.",
                409,
            )
        user["username"] = raw_username.strip()
        user["username_norm"] = raw_username.strip().lower()
        user["last_username_change_at"] = None
        return dict(user)

    def reset_username(
        self,
        user_id: int,
        admin_username: str = "",
        note: str | None = None,
    ) -> dict[str, Any] | None:
        user = self.community.users.get(user_id)
        if user is None:
            return None
        user["username"] = None
        user["username_norm"] = None
        user["last_username_change_at"] = None
        return dict(user)

    def get_username_history(self, user_id: int) -> list[dict[str, Any]]:
        return []

    def create_report(self, target_id: int, reporter_id: int, payload: Any) -> dict[str, Any]:
        if reporter_id == target_id:
            raise CommunityProfileError("You cannot report your own profile.")
        report = {
            "id": self.next_report_id,
            "community_user_id": target_id,
            "category": payload.category,
            "status": "open",
            "created_at": "2026-09-06T10:00:00",
        }
        self.reports[report["id"]] = report
        self.next_report_id += 1
        return report

    def list_reports(self, **_: Any) -> dict[str, Any]:
        return {
            "reports": list(self.reports.values()),
            "count": len(self.reports),
            "limit": 20,
            "offset": 0,
            "status": None,
        }

    def resolve_report(
        self,
        report_id: int,
        resolved: bool,
        admin_username: str = "",
        note: str | None = None,
    ) -> dict[str, Any]:
        report = self.reports.get(report_id)
        if report is None:
            raise CommunityProfileError("Report is not open or does not exist.", status_code=404)
        report["status"] = "resolved" if resolved else "rejected"
        return report


def _client() -> tuple[TestClient, FakeCommunityAccountService]:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        API_KEYS="dev-api-key",
        FEATURE_DISCORD_ACCOUNTS="ENABLED",
        FEATURE_COMMUNITY_PROFILES="ENABLED",
        FEATURE_PROFILE_CUSTOMIZATION="ENABLED",
        FEATURE_COMMUNITY_MEMBERS="ENABLED",
        FEATURE_PROFILE_REPORTING="ENABLED",
    )
    community = FakeCommunityAccountService()
    moderation = FakeCommunityModerationService(community)
    app.dependency_overrides[dependencies.get_auth_service] = FakeAuthService
    app.dependency_overrides[dependencies.get_community_account_service] = lambda: community
    app.dependency_overrides[dependencies.get_community_moderation_service] = lambda: moderation
    return TestClient(app), community


def _beta_client() -> tuple[TestClient, FakeCommunityAccountService]:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        API_KEYS="dev-api-key",
        BETA_DISCORD_IDS="beta-user",
        ALLOWED_DISCORD_IDS="admin",
    )
    community = FakeCommunityAccountService()
    moderation = FakeCommunityModerationService(community)
    app.dependency_overrides[dependencies.get_auth_service] = FakeAuthService
    app.dependency_overrides[dependencies.get_community_account_service] = lambda: community
    app.dependency_overrides[dependencies.get_community_moderation_service] = lambda: moderation
    return TestClient(app), community


def _cookie(token: str) -> dict[str, str]:
    return {"WC_TOKEN": token}


def test_me_requires_login() -> None:
    client, _ = _client()
    response = client.get("/api/v1/community/me")
    assert response.status_code == 401


def test_me_returns_account_when_logged_in() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.get("/api/v1/community/me", cookies=_cookie("user-a"))
    assert response.status_code == 200
    assert response.json()["discord_username"] == "Name user-a"


def test_update_profile_requires_login() -> None:
    client, _ = _client()
    response = client.patch("/api/v1/community/profile", json={"bio": "hi"})
    assert response.status_code == 401


def test_update_profile_returns_error_for_invalid_country() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.patch(
        "/api/v1/community/profile",
        json={"country": "XX"},
        cookies=_cookie("user-a"),
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Unknown country code."}


def test_update_profile_succeeds() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.patch(
        "/api/v1/community/profile",
        json={"country": "fi", "bio": "Hello"},
        cookies=_cookie("user-a"),
    )
    assert response.status_code == 200
    assert response.json()["bio"] == "Hello"
    assert response.json()["country"] == "fi"


def test_banner_upload_requires_login() -> None:
    client, _ = _client()
    response = client.post("/api/v1/community/profile/banner")
    assert response.status_code == 401


def test_banner_upload_rejects_invalid_image() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.post(
        "/api/v1/community/profile/banner",
        files={"banner": ("banner.png", b"<svg></svg>", "image/png")},
        cookies=_cookie("user-a"),
    )
    assert response.status_code == 400


def test_members_list_is_public() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.get("/api/v1/community/members")
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_public_profile_returns_404_for_private_profile() -> None:
    client, community = _client()
    community.add_user("user-a", public=False)
    response = client.get("/api/v1/community/1")
    assert response.status_code == 404


def test_public_profile_visible_and_owner_can_view_private() -> None:
    client, community = _client()
    community.add_user("user-a", public=False)
    assert client.get("/api/v1/community/1", cookies=_cookie("other")).status_code == 404
    owner = client.get("/api/v1/community/1", cookies=_cookie("user-a"))
    assert owner.status_code == 200
    assert owner.json()["is_owner"] is True


def test_banner_endpoint_respects_privacy() -> None:
    client, community = _client()
    community.add_user("user-a", public=False)
    community.banners[1] = {"content": b"image-bytes", "content_type": "image/webp"}

    assert client.get("/api/v1/community/1/banner").status_code == 404
    owner = client.get("/api/v1/community/1/banner", cookies=_cookie("user-a"))
    assert owner.status_code == 200
    assert owner.headers["content-type"] == "image/webp"
    assert owner.content == b"image-bytes"


def test_report_requires_login() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.post("/api/v1/community/1/report", json={"category": "spam"})
    assert response.status_code == 401


def test_report_self_returns_400() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.post(
        "/api/v1/community/1/report",
        json={"category": "spam"},
        cookies=_cookie("user-a"),
    )
    assert response.status_code == 400


def test_report_succeeds_for_other_user() -> None:
    client, community = _client()
    community.add_user("user-a")
    community.add_user("user-b")
    response = client.post(
        "/api/v1/community/1/report",
        json={"category": "spam", "reason": "Ads"},
        cookies=_cookie("user-b"),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "open"


def test_admin_profiles_require_admin() -> None:
    client, community = _client()
    community.add_user("user-a")
    assert client.get("/api/v1/admin/community/profiles").status_code == 401
    assert (
        client.get(
            "/api/v1/admin/community/profiles",
            cookies=_cookie("user-a"),
        ).status_code
        == 403
    )
    ok = client.get("/api/v1/admin/community/profiles", cookies=_cookie("admin"))
    assert ok.status_code == 200
    assert ok.json()["count"] == 1


def test_admin_disable_profile() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.post("/api/v1/admin/community/profiles/1/disable", cookies=_cookie("admin"))
    assert response.status_code == 200
    assert community.users[1]["admin_disabled"] is True


def test_admin_report_resolution() -> None:
    client, community = _client()
    community.add_user("user-a")
    community.add_user("user-b")
    created = client.post(
        "/api/v1/community/1/report",
        json={"category": "spam"},
        cookies=_cookie("user-b"),
    )
    report_id = created.json()["id"]
    resolved = client.post(
        f"/api/v1/admin/community/reports/{report_id}/resolve",
        json={"note": "Confirmed"},
        cookies=_cookie("admin"),
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


def test_beta_members_list_denied_for_anonymous_user() -> None:
    client, _ = _beta_client()
    response = client.get("/api/v1/community/members")
    assert response.status_code == 403


def test_beta_members_list_denied_for_non_beta_user() -> None:
    client, community = _beta_client()
    community.add_user("user-a")
    response = client.get("/api/v1/community/members", cookies=_cookie("user-a"))
    assert response.status_code == 403


def test_beta_members_list_allowed_for_beta_user() -> None:
    client, community = _beta_client()
    community.add_user("beta-user")
    response = client.get("/api/v1/community/members", cookies=_cookie("beta-user"))
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_beta_members_list_allowed_for_admin_user() -> None:
    client, community = _beta_client()
    community.add_user("beta-user")
    response = client.get("/api/v1/community/members", cookies=_cookie("admin"))
    assert response.status_code == 200


def test_beta_profile_denied_for_non_beta_user() -> None:
    client, community = _beta_client()
    community.add_user("user-a")
    response = client.get("/api/v1/community/1", cookies=_cookie("user-a"))
    assert response.status_code == 403


def test_beta_profile_allowed_for_beta_user() -> None:
    client, community = _beta_client()
    community.add_user("beta-user")
    response = client.get("/api/v1/community/1", cookies=_cookie("beta-user"))
    assert response.status_code == 200


def test_beta_profile_edit_denied_for_non_beta_user() -> None:
    client, community = _beta_client()
    community.add_user("user-a")
    response = client.patch(
        "/api/v1/community/profile",
        json={"bio": "hi"},
        cookies=_cookie("user-a"),
    )
    assert response.status_code == 403


def test_beta_profile_edit_allowed_for_beta_user() -> None:
    client, community = _beta_client()
    community.add_user("beta-user")
    response = client.patch(
        "/api/v1/community/profile",
        json={"bio": "hi"},
        cookies=_cookie("beta-user"),
    )
    assert response.status_code == 200
    assert response.json()["bio"] == "hi"


def test_beta_report_denied_for_non_beta_user() -> None:
    client, community = _beta_client()
    community.add_user("user-a")
    community.add_user("user-b")
    response = client.post(
        "/api/v1/community/1/report",
        json={"category": "spam"},
        cookies=_cookie("user-b"),
    )
    assert response.status_code == 403


def test_beta_report_allowed_for_beta_user() -> None:
    client, community = _beta_client()
    community.add_user("user-a")
    community.add_user("beta-user")
    response = client.post(
        "/api/v1/community/1/report",
        json={"category": "spam"},
        cookies=_cookie("beta-user"),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "open"


def test_profile_edit_denied_without_username() -> None:
    client, community = _client()
    community.add_user("user-a", onboarded=False)
    response = client.patch(
        "/api/v1/community/profile",
        json={"bio": "hi"},
        cookies=_cookie("user-a"),
    )
    assert response.status_code == 403


def test_members_denied_for_logged_in_user_without_username() -> None:
    client, community = _client()
    community.add_user("user-a", onboarded=False)
    response = client.get("/api/v1/community/members", cookies=_cookie("user-a"))
    assert response.status_code == 403


def test_members_allowed_anonymously() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.get("/api/v1/community/members")
    assert response.status_code == 200


def test_public_profile_denied_for_logged_in_user_without_username() -> None:
    client, community = _client()
    community.add_user("user-a")
    community.add_user("user-b", onboarded=False)
    response = client.get("/api/v1/community/1", cookies=_cookie("user-b"))
    assert response.status_code == 403


def test_set_username_requires_login() -> None:
    client, _ = _client()
    response = client.post("/api/v1/community/profile/username", json={"username": "Racer"})
    assert response.status_code == 401


def test_set_username_succeeds_for_unboarded_user() -> None:
    client, community = _client()
    community.add_user("user-a", onboarded=False)
    response = client.post(
        "/api/v1/community/profile/username",
        json={"username": "  Racer   One  "},
        cookies=_cookie("user-a"),
    )
    assert response.status_code == 200
    assert response.json()["username"] == "Racer One"
    assert response.json()["last_username_change_at"] is not None


def test_set_username_rejects_invalid_format() -> None:
    client, community = _client()
    community.add_user("user-a", onboarded=False)
    response = client.post(
        "/api/v1/community/profile/username",
        json={"username": "a"},
        cookies=_cookie("user-a"),
    )
    assert response.status_code == 400


def test_set_username_rejects_generic_unavailability() -> None:
    client, community = _client()
    community.add_user("user-a", onboarded=False)
    response = client.post(
        "/api/v1/community/profile/username",
        json={"username": "admin"},
        cookies=_cookie("user-a"),
    )
    assert response.status_code == 400
    assert response.json()["error"] == (
        "This username isn't available. Please choose another one."
    )


def test_set_username_enforces_cooldown() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.post(
        "/api/v1/community/profile/username",
        json={"username": "NewName"},
        cookies=_cookie("user-a"),
    )
    assert response.status_code == 409


def test_admin_can_set_username_via_patch() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.patch(
        "/api/v1/admin/community/profiles/1",
        json={"username": "ForcedName"},
        cookies=_cookie("admin"),
    )
    assert response.status_code == 200
    assert community.users[1]["username"] == "ForcedName"


def test_admin_reset_username_endpoint() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.post(
        "/api/v1/admin/community/profiles/1/reset-username",
        json={"note": "Name change"},
        cookies=_cookie("admin"),
    )
    assert response.status_code == 200
    assert community.users[1]["username"] is None


def test_admin_profile_detail_includes_username_history() -> None:
    client, community = _client()
    community.add_user("user-a")
    response = client.get(
        "/api/v1/admin/community/profiles/1",
        cookies=_cookie("admin"),
    )
    assert response.status_code == 200
    assert response.json()["username_history"] == []
    assert response.json()["username"] == "Nick 1"


def test_auth_status_sends_features_and_no_beta_for_logged_out() -> None:
    client, _ = _beta_client()
    response = client.get("/api/v1/auth/status")
    assert response.status_code == 200
    assert response.json() == {
        "logged": False,
        "allowed": False,
        "features": {
            "discord_accounts": "BETA",
            "community_profiles": "BETA",
            "profile_customization": "BETA",
            "community_members": "BETA",
            "profile_reporting": "BETA",
        },
    }


def test_auth_status_exposes_beta_flag_and_features_for_beta_user() -> None:
    client, _ = _beta_client()
    response = client.get("/api/v1/auth/status", cookies=_cookie("beta-user"))
    assert response.status_code == 200
    body = response.json()
    assert body["logged"] is True
    assert body["beta"] is True
    assert body["features"]["community_members"] == "BETA"


def test_auth_status_no_beta_flag_for_non_beta_user() -> None:
    client, _ = _beta_client()
    response = client.get("/api/v1/auth/status", cookies=_cookie("user-a"))
    assert response.status_code == 200
    body = response.json()
    assert body["logged"] is True
    assert body["beta"] is False