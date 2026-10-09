import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from PIL import Image, ImageOps
from PIL.Image import DecompressionBombError

from app.core.username_rules import (
    UsernameModerationError,
    UsernameValidationError,
    username_key,
    validate_username,
)
from app.repositories.community_user import CommunityUserRepository, UsernameConflictError
from app.services.countries import COUNTRY_CODES

MAX_BIO_LENGTH = 500
MAX_BANNER_RAW_BYTES = 10 * 1024 * 1024
MAX_BANNER_DIMENSION = 2048
MAX_BANNER_PIXELS = 50_000_000
MAX_SEARCH_LENGTH = 50

DISCORD_AVATAR_CDN = "https://cdn.discordapp.com/avatars/{discord_id}/{hash}.{ext}"


def _cooldown_unit(cooldown_days: int) -> str:
    return "day" if cooldown_days == 1 else "days"


def discord_avatar_url(discord_id: str | None, avatar: str | None) -> str | None:
    """Build a full Discord CDN avatar URL from an avatar hash.

    Discord OAuth exposes ``avatar`` as a bare hash (e.g. ``a_1f2e3a...``),
    not a URL. This normalizes it into the CDN URL used by ``<img>`` while
    leaving already-absolute URLs untouched.
    """
    if not avatar:
        return None
    if avatar.startswith(("http://", "https://")):
        return avatar
    if not discord_id:
        return None
    ext = "gif" if avatar.startswith("a_") else "png"
    return DISCORD_AVATAR_CDN.format(discord_id=discord_id, hash=avatar, ext=ext)


class CommunityProfileError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class ProfileField:
    """One field of the API-key profile payload.

    ``source`` is the key to read from the repository row. ``transform`` derives
    the value from ``(account, raw_value)`` (avatar URL, boolean flags, ...).
    ``visibility_flag`` is the ``show_*`` column governing whether the member
    chose to publish this field; when set, the payload gains a ``<name>_private``
    boolean so consumers can tell "hidden by the member" from "genuinely empty".
    """

    name: str
    source: str
    transform: Callable[[dict[str, Any], Any], Any] | None = None
    visibility_flag: str | None = None


def _avatar_url(account: dict[str, Any], avatar: Any) -> str | None:
    return discord_avatar_url(account["discord_id"], avatar)


def _is_set(_account: dict[str, Any], value: Any) -> bool:
    return value is not None and value != ""


#: Declarative source of truth for ``GET /api/v1/community-api/users/{user_id}``.
#:
#: The API key grants trusted access, so every column is returned regardless of
#: the member's ``profile_public`` / ``show_*`` choices. Fields the member has
#: marked private are still present but flagged, never hidden.
#:
#: To expose another profile value, add one row here. Only a genuinely new
#: database column additionally requires an entry in ``PROFILE_COLUMNS``
#: (backend/app/repositories/community_user.py).
API_PROFILE_FIELDS: tuple[ProfileField, ...] = (
    ProfileField("id", "id"),
    ProfileField("discord_id", "discord_id"),
    ProfileField("username", "username"),
    ProfileField("created_at", "created_at"),
    ProfileField("updated_at", "updated_at"),
    ProfileField("last_username_change_at", "last_username_change_at"),
    ProfileField("discord_username", "discord_username", visibility_flag="show_discord_username"),
    ProfileField("discord_avatar", "discord_avatar", _avatar_url, "show_discord_avatar"),
    ProfileField("bio", "bio", visibility_flag="show_bio"),
    ProfileField("country", "country", visibility_flag="show_country"),
    ProfileField(
        "favorite_vehicle_id",
        "favorite_vehicle_id",
        visibility_flag="show_favorite_vehicle",
    ),
    ProfileField(
        "favorite_vehicle_name",
        "favorite_vehicle_name",
        visibility_flag="show_favorite_vehicle",
    ),
    ProfileField(
        "favorite_map_id",
        "favorite_map_id",
        visibility_flag="show_favorite_map",
    ),
    ProfileField(
        "favorite_map_name",
        "favorite_map_name",
        visibility_flag="show_favorite_map",
    ),
    ProfileField("has_banner", "banner_updated_at", _is_set),
    ProfileField("banner_updated_at", "banner_updated_at"),
    ProfileField("profile_public", "profile_public"),
    ProfileField("admin_disabled", "admin_disabled"),
)

#: Keys describing the member's own privacy settings, echoed so consumers can
#: interpret the ``*_private`` markers without a second request.
API_PROFILE_VISIBILITY_FLAGS: tuple[str, ...] = (
    "show_bio",
    "show_country",
    "show_favorite_vehicle",
    "show_favorite_map",
    "show_discord_username",
    "show_discord_avatar",
)


def build_api_profile(account: dict[str, Any]) -> dict[str, Any]:
    """Serialize a repository row into the API-key profile payload."""
    profile: dict[str, Any] = {}
    for spec in API_PROFILE_FIELDS:
        raw = account.get(spec.source)
        profile[spec.name] = spec.transform(account, raw) if spec.transform else raw
        if spec.visibility_flag is not None:
            profile[f"{spec.name}_private"] = not bool(account.get(spec.visibility_flag))
    for flag in API_PROFILE_VISIBILITY_FLAGS:
        profile[flag] = bool(account.get(flag))
    return profile


@dataclass(frozen=True, slots=True)
class CommunityAccountService:
    repository: CommunityUserRepository

    def get_account(self, discord_id: str) -> dict[str, Any] | None:
        return self.repository.get_by_discord_id(discord_id)

    def get_account_by_id(self, user_id: int) -> dict[str, Any] | None:
        return self.repository.get_by_id(user_id)

    def get_or_create(
        self,
        discord_id: str,
        discord_username: str | None,
        discord_avatar: str | None,
    ) -> dict[str, Any]:
        return self.repository.ensure_account(
            discord_id=discord_id,
            discord_username=discord_username or "",
            discord_avatar=discord_avatar_url(discord_id, discord_avatar),
        )

    def set_username(
        self,
        discord_id: str,
        raw_username: str,
        cooldown_days: int,
    ) -> dict[str, Any] | None:
        try:
            username = validate_username(raw_username)
        except (UsernameValidationError, UsernameModerationError) as exc:
            raise CommunityProfileError(exc.message) from None

        account = self.repository.get_by_discord_id(discord_id)
        if account is None:
            return None

        if account["username"] is not None:
            last_change = account["last_username_change_at"]
            if last_change is not None and cooldown_days > 0:
                if last_change.tzinfo is None:
                    last_change = last_change.replace(tzinfo=UTC)
                cooldown_seconds = cooldown_days * 24 * 60 * 60
                elapsed = (datetime.now(UTC) - last_change).total_seconds()
                if elapsed < cooldown_seconds:
                    raise CommunityProfileError(
                        f"Your username can only be changed once every {cooldown_days} "
                        f"{_cooldown_unit(cooldown_days)}.",
                        409,
                    )

        try:
            return self.repository.set_username(
                int(account["id"]),
                username,
                username_key(username),
            )
        except UsernameConflictError:
            raise CommunityProfileError(
                "This username isn't available. Please choose another one.",
                409,
            ) from None

    def update_profile(self, discord_id: str, payload: Any) -> dict[str, Any] | None:
        bio = payload.bio or ""
        if len(bio) > MAX_BIO_LENGTH:
            raise CommunityProfileError(f"Bio must be at most {MAX_BIO_LENGTH} characters.")

        country = payload.country
        if country is not None:
            country = country.strip().lower()
            if country and country not in COUNTRY_CODES:
                raise CommunityProfileError("Unknown country code.")
            if not country:
                country = None

        vehicle_id = payload.favorite_vehicle_id
        map_id = payload.favorite_map_id
        vehicle_name, map_name = self.repository.favorite_names(vehicle_id, map_id)
        if vehicle_id is not None and vehicle_name is None:
            raise CommunityProfileError("Unknown favorite vehicle.")
        if map_id is not None and map_name is None:
            raise CommunityProfileError("Unknown favorite map.")

        return self.repository.update_profile(
            discord_id=discord_id,
            bio=bio,
            country=country,
            favorite_vehicle_id=vehicle_id,
            favorite_map_id=map_id,
            profile_public=bool(payload.profile_public),
            show_country=bool(payload.show_country),
            show_bio=bool(payload.show_bio),
            show_favorite_vehicle=bool(payload.show_favorite_vehicle),
            show_favorite_map=bool(payload.show_favorite_map),
            show_discord_username=bool(payload.show_discord_username),
            show_discord_avatar=bool(payload.show_discord_avatar),
        )

    def upload_banner(
        self,
        discord_id: str,
        content: bytes,
        cooldown_days: int = 7,
    ) -> dict[str, Any] | None:
        account = self.repository.get_by_discord_id(discord_id)
        if account is None:
            return None
        normalized, content_type = _normalize_banner(content)
        updated = self.repository.update_banner(
            discord_id,
            normalized,
            content_type,
            cooldown_days,
        )
        if updated is None:
            raise CommunityProfileError(
                f"Your banner can only be changed once every {cooldown_days} "
                f"{_cooldown_unit(cooldown_days)}.",
                409,
            )
        return updated

    def clear_banner(self, discord_id: str) -> dict[str, Any] | None:
        return self.repository.clear_banner(discord_id)

    def get_banner(self, user_id: int, viewer_discord_id: str | None) -> dict[str, Any] | None:
        banner = self.repository.get_banner(user_id)
        if banner is None:
            return None
        is_owner = viewer_discord_id is not None and banner["discord_id"] == viewer_discord_id
        if not is_owner and not banner["public"]:
            return None
        return banner

    def get_public_profile(
        self,
        user_id: int,
        viewer_discord_id: str | None,
    ) -> dict[str, Any] | None:
        account = self.repository.get_by_id(user_id)
        if account is None:
            return None
        is_owner = viewer_discord_id is not None and account["discord_id"] == viewer_discord_id
        if not is_owner and (not account["profile_public"] or account["admin_disabled"]):
            return None
        if not is_owner and account["username"] is None:
            return None
        return _public_profile(account, is_owner)

    def get_api_profile(self, discord_id: str) -> dict[str, Any] | None:
        """Full profile for API-key consumers, keyed by Discord ID.

        Discord ID rather than the internal ``community_user.id`` because the
        primary consumer is a Discord bot, which only ever holds snowflakes.

        Moderator-disabled accounts are still withheld: that is an admin
        decision rather than a member's own choice. Everything else is returned
        in full, with ``*_private`` markers where the member hid a field.
        """
        account = self.repository.get_by_discord_id(discord_id)
        if account is None or account["admin_disabled"]:
            return None
        return build_api_profile(account)

    def list_members(
        self,
        *,
        search: str | None,
        sort: str,
        country: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        if sort not in ("new", "name", "active"):
            sort = "new"
        if country is not None:
            country = country.strip().lower()
            if country not in COUNTRY_CODES:
                country = None
        if search is not None:
            search = search.strip()
            if len(search) > MAX_SEARCH_LENGTH:
                search = search[:MAX_SEARCH_LENGTH]
            if not search:
                search = None

        members, total = self.repository.list_members(
            search=search,
            sort=sort,
            country=country,
            limit=limit,
            offset=offset,
        )
        return {
            "members": [_trim_member(member) for member in members],
            "count": total,
            "limit": limit,
            "offset": offset,
            "search": search,
            "sort": sort,
        }


def _public_profile(account: dict[str, Any], is_owner: bool) -> dict[str, Any]:
    profile = {
        "id": account["id"],
        "username": account["username"],
        "created_at": account["created_at"],
        "updated_at": account["updated_at"],
        "bio": account["bio"] if is_owner or account["show_bio"] else None,
        "country": account["country"] if is_owner or account["show_country"] else None,
        "favorite_vehicle_id": (
            account["favorite_vehicle_id"]
            if is_owner or account["show_favorite_vehicle"]
            else None
        ),
        "favorite_vehicle_name": (
            account["favorite_vehicle_name"]
            if is_owner or account["show_favorite_vehicle"]
            else None
        ),
        "favorite_map_id": (
            account["favorite_map_id"] if is_owner or account["show_favorite_map"] else None
        ),
        "favorite_map_name": (
            account["favorite_map_name"] if is_owner or account["show_favorite_map"] else None
        ),
        "banner_updated_at": account["banner_updated_at"],
        "show_country": account["show_country"],
        "show_bio": account["show_bio"],
        "show_favorite_vehicle": account["show_favorite_vehicle"],
        "show_favorite_map": account["show_favorite_map"],
        "show_discord_username": account["show_discord_username"],
        "show_discord_avatar": account["show_discord_avatar"],
        "admin_disabled": account["admin_disabled"],
        "is_owner": is_owner,
    }
    if is_owner or account["show_discord_username"]:
        profile["discord_username"] = account["discord_username"]
    if is_owner or account["show_discord_avatar"]:
        profile["discord_avatar"] = discord_avatar_url(
            account["discord_id"], account["discord_avatar"]
        )
    return profile


def _trim_member(member: dict[str, Any]) -> dict[str, Any]:
    result = {
        "id": member["id"],
        "username": member["username"],
        "created_at": member["created_at"],
        "updated_at": member["updated_at"],
        "bio": member["bio"] if member["show_bio"] else None,
        "country": member["country"] if member["show_country"] else None,
        "favorite_vehicle_id": (
            member["favorite_vehicle_id"] if member["show_favorite_vehicle"] else None
        ),
        "favorite_vehicle_name": (
            member["favorite_vehicle_name"] if member["show_favorite_vehicle"] else None
        ),
        "favorite_map_id": member["favorite_map_id"] if member["show_favorite_map"] else None,
        "favorite_map_name": member["favorite_map_name"] if member["show_favorite_map"] else None,
        "banner_updated_at": member["banner_updated_at"],
    }
    if member["show_discord_username"]:
        result["discord_username"] = member["discord_username"]
    if member["show_discord_avatar"]:
        result["discord_avatar"] = discord_avatar_url(
            member["discord_id"], member["discord_avatar"]
        )
    return result


def _normalize_banner(content: bytes) -> tuple[bytes, str]:
    if not content:
        raise CommunityProfileError("No banner image was provided.")
    if len(content) > MAX_BANNER_RAW_BYTES:
        raise CommunityProfileError("Banner file is too large (maximum 10 MB).")

    previous_pixel_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = MAX_BANNER_PIXELS
    try:
        with Image.open(io.BytesIO(content)) as opened:
            image = ImageOps.exif_transpose(opened)
            image.load()
        if image.width > MAX_BANNER_DIMENSION or image.height > MAX_BANNER_DIMENSION:
            image.thumbnail((MAX_BANNER_DIMENSION, MAX_BANNER_DIMENSION))
        image = image.convert("RGBA")
        output = io.BytesIO()
        image.save(output, format="WEBP", quality=85, method=6)
    except (OSError, ValueError, DecompressionBombError):
        raise CommunityProfileError(
            "The uploaded file is not a valid PNG, JPEG or WebP image."
        ) from None
    finally:
        Image.MAX_IMAGE_PIXELS = previous_pixel_limit

    return output.getvalue(), "image/webp"