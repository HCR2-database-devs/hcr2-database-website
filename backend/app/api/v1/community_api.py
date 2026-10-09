from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    ApiKeyAuthorizedDep,
    get_community_account_service,
)
from app.services.community_account_service import CommunityAccountService

router = APIRouter(prefix="/community-api", tags=["community-api"])
CommunityAccountServiceDep = Annotated[
    CommunityAccountService,
    Depends(get_community_account_service),
]

UNAUTHORIZED_MESSAGE = "Unauthorized: invalid API key"


@router.get(
    "/users/{discord_id}",
    response_model=None,
    summary="Fetch a community profile by Discord ID (API key required)",
)
def community_profile_api(
    request: Request,
    authorized: ApiKeyAuthorizedDep,
    community_service: CommunityAccountServiceDep,
    discord_id: Annotated[str, Path(pattern=r"^[0-9]{17,20}$")],
) -> Any:
    """Return the full profile for the Discord ID ``discord_id``.

    The identifier is the Discord user snowflake, not the internal
    ``community_user.id`` sequence value. Consumers are primarily Discord bots,
    which only ever hold snowflakes.

    It is taken as a string on purpose: snowflakes exceed JavaScript's safe
    integer range, so a numeric path parameter would silently lose precision for
    any client using JSON.parse. Ids that are not 17-20 digits are rejected with
    422 rather than looked up.

    Authenticate with the ``X-API-Key`` header or an ``api_key`` query parameter,
    using a key from ``API_KEYS``.

    The key grants trusted access, so every profile field is returned even when
    the member marked it private on their settings page. Each such field is
    accompanied by a ``<field>_private`` boolean (``true`` means the member
    chose not to publish it), so consumers can distinguish hidden data from
    genuinely empty data instead of silently dropping fields.

    Fields marked private are currently ``discord_username``, ``discord_avatar``,
    ``bio``, ``country``, ``favorite_vehicle_id``, ``favorite_vehicle_name``,
    ``favorite_map_id`` and ``favorite_map_name``. The member's ``show_*`` flags
    are echoed in the response.

    Returns 404 when no account exists for the ID, or when the account has been
    disabled by a moderator.

    ``response_model`` is intentionally unset: the payload is generated from the
    ``API_PROFILE_FIELDS`` table in ``app/services/community_account_service.py``,
    so adding a profile field there requires no change here.
    """
    if not authorized:
        return JSONResponse({"error": UNAUTHORIZED_MESSAGE}, status_code=401)

    profile = community_service.get_api_profile(discord_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Not found")
    return profile