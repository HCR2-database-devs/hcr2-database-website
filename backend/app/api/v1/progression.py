from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_auth_service,
    get_community_account_service,
    get_progression_service,
)
from app.core.config import Settings, get_settings
from app.core.features import Feature, can_use_feature
from app.repositories.progression import ProgressionError
from app.schemas.badges import XpAdjustmentRequest
from app.services.auth_service import AuthService
from app.services.community_account_service import CommunityAccountService
from app.services.progression_service import ProgressionService

router = APIRouter(prefix="/progression", tags=["progression"])
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
ProgressionServiceDep = Annotated[ProgressionService, Depends(get_progression_service)]
CommunityServiceDep = Annotated[
    CommunityAccountService,
    Depends(get_community_account_service),
]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _status(request: Request, auth_service: AuthService) -> dict[str, Any]:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return status


def _require_feature(
    request: Request,
    auth_service: AuthService,
    settings: Settings,
) -> str | None:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    discord_id = str(status["id"]) if status.get("logged") else None
    if not can_use_feature(discord_id, Feature.COMMUNITY_XP, settings):
        raise HTTPException(status_code=403, detail="This feature is currently disabled")
    return discord_id


def _admin_status(
    request: Request,
    auth_service: AuthService,
    settings: Settings,
) -> dict[str, Any]:
    status = _status(request, auth_service)
    if not status.get("allowed"):
        raise HTTPException(status_code=403, detail="Permission denied")
    _require_feature(request, auth_service, settings)
    return status


def _own_user_id(
    request: Request,
    auth_service: AuthService,
    community_service: CommunityAccountService,
    settings: Settings,
) -> int:
    discord_id = _require_feature(request, auth_service, settings)
    if discord_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    account = community_service.get_account(discord_id)
    if account is None or not account.get("username"):
        raise HTTPException(
            status_code=403,
            detail="You need to choose a username before you can use this feature.",
        )
    return int(account["id"])


def _error(exc: ProgressionError) -> JSONResponse:
    return JSONResponse({"error": exc.message}, status_code=exc.status_code)


@router.get("/me", response_model=None)
def own_progression(
    request: Request,
    auth_service: AuthServiceDep,
    progression_service: ProgressionServiceDep,
    community_service: CommunityServiceDep,
    settings: SettingsDep,
) -> Any:
    user_id = _own_user_id(request, auth_service, community_service, settings)
    return progression_service.get_summary(user_id)


@router.get("/me/transactions", response_model=None)
def own_xp_transactions(
    request: Request,
    auth_service: AuthServiceDep,
    progression_service: ProgressionServiceDep,
    community_service: CommunityServiceDep,
    settings: SettingsDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
    user_id = _own_user_id(request, auth_service, community_service, settings)
    return progression_service.list_transactions(user_id, limit=limit, offset=offset)


@router.get("/members/{user_id}", response_model=None)
def member_progression(
    user_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    progression_service: ProgressionServiceDep,
    community_service: CommunityServiceDep,
    settings: SettingsDep,
) -> Any:
    discord_id = _require_feature(request, auth_service, settings)
    profile = community_service.get_public_profile(user_id, discord_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Not found")
    if not profile.get("is_owner") and not profile.get("show_xp"):
        raise HTTPException(status_code=403, detail="This member hides their XP.")
    return progression_service.get_summary(user_id)


@router.get("/admin/transactions", response_model=None)
def admin_xp_transactions(
    request: Request,
    auth_service: AuthServiceDep,
    progression_service: ProgressionServiceDep,
    settings: SettingsDep,
    community_user_id: Annotated[int | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
    _admin_status(request, auth_service, settings)
    if community_user_id is None:
        raise HTTPException(status_code=400, detail="community_user_id is required.")
    try:
        return progression_service.list_transactions(
            community_user_id,
            limit=limit,
            offset=offset,
        )
    except ProgressionError as exc:
        return _error(exc)


@router.post("/admin/adjust", response_model=None)
def admin_adjust_xp(
    payload: XpAdjustmentRequest,
    request: Request,
    auth_service: AuthServiceDep,
    progression_service: ProgressionServiceDep,
    community_service: CommunityServiceDep,
    settings: SettingsDep,
    community_user_id: Annotated[int | None, Query()] = None,
) -> Any:
    admin = _admin_status(request, auth_service, settings)
    if community_user_id is None:
        raise HTTPException(status_code=400, detail="community_user_id is required.")
    if community_service.get_account_by_id(community_user_id) is None:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        return progression_service.adjust_xp(
            community_user_id=community_user_id,
            amount=payload.amount,
            reason=payload.reason,
            actor=str(admin.get("username") or ""),
        )
    except ProgressionError as exc:
        return _error(exc)


@router.post("/admin/refresh/{user_id}", response_model=None)
def admin_refresh_badges(
    user_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    progression_service: ProgressionServiceDep,
    community_service: CommunityServiceDep,
    settings: SettingsDep,
) -> Any:
    _admin_status(request, auth_service, settings)
    if community_service.get_account_by_id(user_id) is None:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        return progression_service.refresh(user_id)
    except ProgressionError as exc:
        return _error(exc)


@router.get("/admin/evaluations", response_model=None)
def admin_evaluations(
    request: Request,
    auth_service: AuthServiceDep,
    progression_service: ProgressionServiceDep,
    settings: SettingsDep,
    community_user_id: Annotated[int | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
    _admin_status(request, auth_service, settings)
    return progression_service.repository.list_evaluations(
        community_user_id=community_user_id,
        limit=limit,
        offset=offset,
    )
