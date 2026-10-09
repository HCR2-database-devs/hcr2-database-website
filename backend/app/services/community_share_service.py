"""Server-rendered share pages for community profiles.

Discord does not execute JavaScript, so a SPA route pasted into a channel
renders as a bare URL. This module renders a small HTML document carrying both
Open Graph tags (the fallback card) and a ``discord:component-embed`` script
tag (the richer card), then redirects to the real SPA profile route.

The payload mirrors ``frontend/scripts/generate-discord-embed.mjs``, which does
the same for the static site embed. Keep the component type numbers in sync
with ``ComponentType`` in the ``discord-component-embed`` package.
"""

from __future__ import annotations

import html
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.services.community_account_service import (
    CommunityAccountService,
    discord_avatar_url,
)
from app.services.countries import country_name

# Discord component type numbers (ComponentType in discord-component-embed).
_ACTION_ROW = 1
_LINK_BUTTON = 2
_SECTION = 9
_TEXT_DISPLAY = 10
_THUMBNAIL = 11
_SEPARATOR = 14
_CONTAINER = 17

_LINK_BUTTON_STYLE = 5
_EMBED_ACCENT = 0x0F766E

#: Discord truncates beyond these; staying under keeps the card intact.
_MAX_TEXT = 400
_MAX_DESCRIPTION = 4000

_SITE_NAME = "hcr2.xyz"
_FALLBACK_LOGO = "/img/hcrdatabaselogo.png"

#: Seconds to cache an avatar reachability result. Discord rotates avatar
#: hashes when a member changes their avatar, which makes the stored URL 404 and
#: breaks the embed, so we verify before embedding and fall back to the logo.
_AVATAR_CHECK_TTL_SECONDS = 3600

#: Maps each emoji-prefixed detail line to the short label used in the
#: Open Graph description, which has no room for emoji or full sentences.
_OG_LABELS = {
    "🌍": "Country",
    "💬": "Bio",
    "🚗": "Favorite vehicle",
    "🗺": "Favorite map",
}


class ProfileNotFound(ValueError):
    pass


def _clip(value: str, limit: int) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _text(*lines: str) -> dict[str, Any]:
    return {"type": _TEXT_DISPLAY, "content": "\n".join(lines)}


def _thumbnail(url: str, description: str) -> dict[str, Any]:
    return {
        "type": _THUMBNAIL,
        "media": {"url": url},
        "description": description,
    }


def _link(url: str, label: str, emoji: str) -> dict[str, Any]:
    return {
        "type": _LINK_BUTTON,
        "style": _LINK_BUTTON_STYLE,
        "url": url,
        "label": label,
        "emoji": {"name": emoji},
    }


@dataclass(frozen=True, slots=True)
class CommunityShareService:
    community_service: CommunityAccountService
    site_url: str = "https://hcr2.xyz"
    avatar_check: Callable[[str], bool] | None = None
    _avatar_cache: dict[str, tuple[float, bool]] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )

    def avatar_reachable(self, url: str) -> bool:
        """Return True when ``url`` still resolves on Discord's CDN.

        Discord avatar hashes change whenever a member updates their avatar, and
        the stored URL then 404s. Embedding a dead URL makes Discord report
        ``Unable to fetch component media metadata`` and render no image, so we
        verify once and fall back to the site logo.

        Results are cached for an hour: the share page is fetched by Discord's
        crawler, and without a cache every render would cost a network call.
        When no checker is injected (tests, offline) the URL is assumed good.
        """
        if self.avatar_check is None:
            return True

        cached = self._avatar_cache.get(url)
        if cached is not None:
            checked_at, reachable = cached
            if time.monotonic() - checked_at < _AVATAR_CHECK_TTL_SECONDS:
                return reachable

        try:
            reachable = bool(self.avatar_check(url))
        except Exception:
            # Never let a transient network fault break the page; the logo is a
            # better outcome than a 500 or a broken embed.
            reachable = False

        self._avatar_cache[url] = (time.monotonic(), reachable)
        return reachable

    def base_url(self) -> str:
        return self.site_url.rstrip("/")

    def profile_url(self, user_id: int) -> str:
        return f"{self.base_url()}/community/{user_id}"

    def share_url(self, user_id: int) -> str:
        return f"{self.base_url()}/api/v1/share/profiles/{user_id}"

    def profile_page(self, user_id: int) -> str:
        """Return the shareable HTML document for ``user_id``.

        Raises:
            ProfileNotFound: the profile is missing, private, or admin-disabled.
        """
        account = self.community_service.get_account_by_id(user_id)
        if account is None or account["admin_disabled"]:
            raise ProfileNotFound(str(user_id))

        # A share link is public, so it must honour the member's own privacy
        # choices. This intentionally does not use get_api_profile().
        if not account["profile_public"] or not account["username"]:
            raise ProfileNotFound(str(user_id))

        username = str(account["username"])
        member_since = _format_date(account["created_at"])
        profile_url = self.profile_url(user_id)

        details = self._detail_lines(account)

        heading = _text(f"# {username}")
        subheading = _text(f"-# {_clip(f'hcr2.xyz #{user_id} · Member since {member_since}', 200)}")

        children: list[dict[str, Any]] = []

        # A Section REQUIRES an accessory; Discord rejects the whole payload
        # otherwise (BASE_TYPE_REQUIRED) and falls back to a bare OG card.
        # Fall back to the site logo when the member hides their avatar.
        avatar = discord_avatar_url(account["discord_id"], account["discord_avatar"])
        if account["show_discord_avatar"] and avatar and self.avatar_reachable(avatar):
            accessory = _thumbnail(avatar, f"{username}'s avatar")
        else:
            accessory = _thumbnail(
                f"{self.base_url()}{_FALLBACK_LOGO}",
                f"{_SITE_NAME} logo",
            )

        children.append(
            {
                "type": _SECTION,
                "components": [heading, subheading],
                "accessory": accessory,
            }
        )

        if details:
            children.append(_text(*details))
            children.append({"type": _SEPARATOR, "divider": True, "spacing": 1})

        children.append(
            {
                "type": _ACTION_ROW,
                "components": [
                    _link(profile_url, "View profile", "👤"),
                    _link(f"{self.base_url()}/community", "Community", "🏆"),
                ],
            }
        )

        embed = {
            "component": {
                "type": _CONTAINER,
                "accent_color": _EMBED_ACCENT,
                "components": children,
            }
        }

        return self._document(
            title=f"{username} · {_SITE_NAME}",
            description=_clip(" · ".join(_OG_LABELS[line[0]] for line in details), _MAX_DESCRIPTION)
            if details
            else "HCR2 community profile",
            url=self.share_url(user_id),
            image=f"{self.base_url()}{_FALLBACK_LOGO}",
            profile_url=profile_url,
            embed=embed,
        )

    @staticmethod
    def _detail_lines(account: dict[str, Any]) -> list[str]:
        """Build embed detail lines, skipping anything the member hid."""
        lines: list[str] = []
        if account["show_country"] and account["country"]:
            name = country_name(account["country"])
            if name:
                lines.append(f"🌍 {name}")
        if account["show_bio"] and account["bio"]:
            lines.append(f"💬 {_clip(str(account['bio']), _MAX_TEXT)}")
        if account["show_favorite_vehicle"] and account["favorite_vehicle_name"]:
            lines.append(f"🚗 Favorite vehicle: {account['favorite_vehicle_name']}")
        if account["show_favorite_map"] and account["favorite_map_name"]:
            lines.append(f"🗺 Favorite map: {account['favorite_map_name']}")
        return lines

    @staticmethod
    def _document(
        *,
        title: str,
        description: str,
        url: str,
        image: str,
        profile_url: str,
        embed: dict[str, Any],
    ) -> str:
        safe_title = html.escape(title, quote=True)
        safe_description = html.escape(description, quote=True)
        safe_url = html.escape(url, quote=True)
        safe_image = html.escape(image, quote=True)
        safe_profile = html.escape(profile_url, quote=True)
        # ``ensure_ascii=False`` keeps emoji readable, matching the payload the
        # Node generator writes. Quotes and control characters are escaped by
        # json.dumps; ``</`` is neutralised separately because JSON escaping does
        # not cover it and it would otherwise close the script element early.
        payload = json.dumps(embed, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{safe_title}</title>
<meta property="og:type" content="profile">
<meta property="og:title" content="{safe_title}">
<meta property="og:description" content="{safe_description}">
<meta property="og:url" content="{safe_url}">
<meta property="og:image" content="{safe_image}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{safe_title}">
<meta name="twitter:description" content="{safe_description}">
<meta name="twitter:image" content="{safe_image}">
<script id="discord:component-embed" type="application/json">{payload}</script>
<script>window.location.replace('{safe_profile}');</script>
</head>
<body>
<p><a href="{safe_profile}">{safe_title}</a></p>
</body>
</html>"""


def _format_date(value: Any) -> str:
    if value is None:
        return "unknown"
    if hasattr(value, "strftime"):
        return value.strftime("%b %Y")
    return str(value)