from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_auth_service, get_community_account_service
from app.services.auth_service import AuthService
from app.services.community_account_service import CommunityAccountService

router = APIRouter(tags=["auth"])
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CommunityAccountServiceDep = Annotated[
    CommunityAccountService,
    Depends(get_community_account_service),
]


@router.get("/auth/status", response_model=None)
def auth_status(
    request: Request,
    service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
) -> dict[str, Any]:
    status = service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        return status

    status["community"] = _resolve_community(status, community_service)
    return status


def _resolve_community(
    status: dict[str, Any],
    community_service: CommunityAccountService,
) -> dict[str, Any] | None:
    try:
        return community_service.get_or_create(
            discord_id=str(status["id"]),
            discord_username=status.get("username"),
            discord_avatar=status.get("avatar"),
        )
    except Exception:
        return None


@router.get("/auth/logout")
def auth_logout() -> RedirectResponse:
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(
        "PHPSESSID",
        path="/",
        domain=".hcr2.xyz",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        "WC_TOKEN",
        path="/",
        domain=".hcr2.xyz",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    return response
