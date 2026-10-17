"""Short, human-friendly share URLs.

These live at the site root (``/u/{user_id}``) rather than under ``/api/v1`` so
the link a member pastes into Discord reads like a profile page instead of an
API path. Nginx must proxy this prefix to the backend; see DEPLOY.md.

The canonical embed URL stays ``/api/v1/share/profiles/{user_id}``. This module
is the friendly alias, and it permanently redirects so links converge on one
canonical URL.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import HTMLResponse, RedirectResponse

from app.api.dependencies import get_community_share_service
from app.api.responses import DATABASE_ERROR_TYPES, database_error_response
from app.services.community_share_service import CommunityShareService, ProfileNotFound

router = APIRouter(tags=["share-short"])

CommunityShareServiceDep = Annotated[CommunityShareService, Depends(get_community_share_service)]


@router.get(
    "/u/{user_id}",
    response_class=HTMLResponse,
    include_in_schema=False,
    summary="Short profile share link (redirects to the canonical share URL)",
)
def short_profile_link(
    user_id: Annotated[int, Path(ge=1)],
    service: CommunityShareServiceDep,
) -> Any:
    """Redirect ``/u/{user_id}`` to the canonical share page.

    Kept as a redirect rather than rendering the page twice so that links
    shared in different places carry one canonical ``og:url``.
    """
    try:
        # Validate before redirecting, so a bad id 404s here instead of at the
        # canonical URL and so we do not redirect to a guaranteed 404.
        service.profile_page(user_id)
    except ProfileNotFound:
        raise HTTPException(status_code=404, detail="Profile not found") from None
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)  # type: ignore[return-value]

    return RedirectResponse(
        url=service.share_url(user_id),
        status_code=301,
    )