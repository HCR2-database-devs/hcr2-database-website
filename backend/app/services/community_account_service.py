import io
from dataclasses import dataclass
from typing import Any

from PIL import Image, ImageOps
from PIL.Image import DecompressionBombError

from app.repositories.community_user import CommunityUserRepository

MAX_BIO_LENGTH = 500
MAX_BANNER_RAW_BYTES = 10 * 1024 * 1024
MAX_BANNER_DIMENSION = 2048
MAX_BANNER_PIXELS = 50_000_000
MAX_SEARCH_LENGTH = 50

COUNTRY_CODES = frozenset(
    """
    ad ae af ag ai al am ao aq ar as at au aw ax az ba bb bd be bf bg bh bi bj bl
    bm bn bo bq br bs bt bv bw by bz ca cc cd cf cg ch ci ck cl cm cn co cr cu cv
    cw cx cy cz de dj dk dm do dz ec ee eg eh er es et eu fi fj fk fm fo fr ga gb
    gd ge gf gg gh gi gl gm gn gp gq gr gs gt gu gw gy hk hm hn hr ht hu id ie il
    im in io iq ir is it je jm jo jp ke kg kh ki km kn kp kr kw ky kz la lb lc li
    lk lr ls lt lu lv ly ma mc md me mf mg mh mk ml mm mn mo mp mq mr ms mt mu mv
    mw mx my mz na nc ne nf ng ni nl no np nr nu nz om pa pe pf pg ph pk pl pm pn
    pr ps pt pw py qa re ro rs ru rw sa sb sc sd se sg sh si sj sk sl sm sn so sr
    ss st sv sx sy sz tc td tf tg th tj tk tl tm tn to tr tt tv tw tz ua ug um us
    uy uz va vc ve vg vi vn vu wf ws ye yt za zm zw
    """.split()
)


class CommunityProfileError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


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
            discord_avatar=discord_avatar,
        )

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
        )

    def upload_banner(self, discord_id: str, content: bytes) -> dict[str, Any] | None:
        normalized, content_type = _normalize_banner(content)
        return self.repository.update_banner(discord_id, normalized, content_type)

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
        return {**account, "is_owner": is_owner}

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


def _trim_member(member: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": member["id"],
        "discord_username": member["discord_username"],
        "discord_avatar": member["discord_avatar"],
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