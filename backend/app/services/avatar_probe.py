"""Reachability probe for Discord CDN avatars.

Kept out of ``community_share_service`` so the share page has no hard httpx
dependency and stays trivially testable: the service takes a ``avatar_check``
callable and this module supplies the real one.
"""

from __future__ import annotations

import httpx

TIMEOUT_SECONDS = 3.0


def avatar_reachable(url: str, timeout: float = TIMEOUT_SECONDS) -> bool:
    """Return True when ``url`` resolves.

    Uses HEAD because we only care whether the object exists. A stale Discord
    avatar hash answers 404 while a live one answers 200.
    """
    try:
        response = httpx.head(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "hcr2.xyz-share/1.0"},
        )
    except (httpx.HTTPError, OSError):
        return False

    # Some CDNs answer HEAD with 405 while still serving GET.
    if response.status_code == httpx.codes.METHOD_NOT_ALLOWED:
        try:
            response = httpx.get(
                url,
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": "hcr2.xyz-share/1.0"},
            )
        except (httpx.HTTPError, OSError):
            return False

    return response.status_code < 400