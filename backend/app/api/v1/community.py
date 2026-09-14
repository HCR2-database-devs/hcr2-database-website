from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from app.api.dependencies import (
    get_auth_service,
    get_community_account_service,
    get_community_moderation_service,
)
from app.core.config import Settings, get_settings
from app.core.features import can_use_feature
from app.schemas.community import (
    CommunityAccount,
    CommunityProfileUpdate,
    CommunityReportCreate,
    UsernameUpdate,
)
from app.services.auth_service import AuthService
from app.services.community_account_service import (
    CommunityAccountService,
    CommunityProfileError,
)
from app.services.community_moderation_service import CommunityModerationService

router = APIRouter(prefix="/community", tags=["community"])
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CommunityAccountServiceDep = Annotated[
    CommunityAccountService,
    Depends(get_community_account_service),
]
CommunityModerationServiceDep = Annotated[
    CommunityModerationService,
    Depends(get_community_moderation_service),
]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _require_user(request: Request, auth_service: AuthService) -> dict[str, Any]:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return status


def _require_feature(
    request: Request,
    auth_service: AuthService,
    settings: Settings,
    feature_name: str,
) -> None:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    discord_id = str(status["id"]) if status.get("logged") else None
    if not can_use_feature(discord_id, feature_name, settings):
        raise HTTPException(status_code=403, detail="This feature is currently in beta")


def _require_onboarded(
    request: Request,
    auth_service: AuthService,
    account: dict[str, Any] | None,
) -> None:
    if account is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not account.get("username"):
        raise HTTPException(
            status_code=403,
            detail="You need to choose a username before you can use this feature.",
        )


def _require_community_access(
    request: Request,
    auth_service: AuthService,
    community_service: CommunityAccountService,
) -> dict[str, Any] | None:
    """Require a signed-in user and return their community account (if any)."""
    status = _require_user(request, auth_service)
    return community_service.get_account(str(status["id"]))


async def _read_upload(upload: UploadFile | None) -> tuple[str | None, str | None, bytes | None]:
    if upload is None or not upload.filename:
        return None, None, None
    return upload.filename, upload.content_type, await upload.read()


def _profile_error_response(exc: CommunityProfileError) -> JSONResponse:
    return JSONResponse({"error": exc.message}, status_code=exc.status_code)


@router.get("/me", response_model=CommunityAccount)
def community_me(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    settings: SettingsDep,
) -> Any:
    status = _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "discord_accounts")

    account = community_service.get_account(str(status["id"]))
    if account is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return account


@router.get("/members", response_model=None)
def community_members(
    request: Request,
    community_service: CommunityAccountServiceDep,
    auth_service: AuthServiceDep,
    settings: SettingsDep,
    q: Annotated[str | None, Query()] = None,
    sort: Annotated[str | None, Query()] = None,
    country: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
    _require_feature(request, auth_service, settings, "community_members")
    account = _require_community_access(request, auth_service, community_service)
    if account is not None:
        _require_onboarded(request, auth_service, account)
    return community_service.list_members(
        search=q,
        sort=sort or "new",
        country=country,
        limit=limit,
        offset=offset,
    )


@router.patch("/profile", response_model=None)
def update_own_profile(
    payload: CommunityProfileUpdate,
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    settings: SettingsDep,
) -> Any:
    status = _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "profile_customization")
    _require_onboarded(
        request,
        auth_service,
        community_service.get_account(str(status["id"])),
    )
    try:
        account = community_service.update_profile(str(status["id"]), payload)
    except CommunityProfileError as exc:
        return _profile_error_response(exc)
    if account is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account


@router.post("/profile/username", response_model=None)
def set_community_username(
    payload: UsernameUpdate,
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    settings: SettingsDep,
) -> Any:
    status = _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "discord_accounts")
    try:
        account = community_service.set_username(
            str(status["id"]),
            payload.username,
            settings.username_change_cooldown_days,
        )
    except CommunityProfileError as exc:
        return _profile_error_response(exc)
    if account is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account


@router.post("/profile/banner", response_model=None)
async def upload_own_banner(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    settings: SettingsDep,
    banner: Annotated[UploadFile | None, File()] = None,
) -> Any:
    status = _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "profile_customization")
    _require_onboarded(
        request,
        auth_service,
        community_service.get_account(str(status["id"])),
    )
    _, _, content = await _read_upload(banner)
    try:
        account = community_service.upload_banner(str(status["id"]), content or b"")
    except CommunityProfileError as exc:
        return _profile_error_response(exc)
    if account is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account


@router.delete("/profile/banner", response_model=None)
def remove_own_banner(
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    settings: SettingsDep,
) -> Any:
    status = _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "profile_customization")
    _require_onboarded(
        request,
        auth_service,
        community_service.get_account(str(status["id"])),
    )
    account = community_service.clear_banner(str(status["id"]))
    if account is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account


@router.get("/{community_id}/banner", response_model=None)
def community_banner(
    community_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    settings: SettingsDep,
) -> Any:
    _require_feature(request, auth_service, settings, "community_profiles")
    account = _require_community_access(request, auth_service, community_service)
    if account is not None:
        _require_onboarded(request, auth_service, account)
    viewer_id = account["discord_id"] if account is not None else None
    banner = community_service.get_banner(community_id, viewer_id)
    if banner is None:
        raise HTTPException(status_code=404, detail="Not found")
    return Response(
        content=banner["content"],
        media_type=banner["content_type"],
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/{community_id}", response_model=None)
def community_profile(
    community_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    settings: SettingsDep,
) -> Any:
    _require_feature(request, auth_service, settings, "community_profiles")
    account = _require_community_access(request, auth_service, community_service)
    if account is not None:
        _require_onboarded(request, auth_service, account)
    viewer_id = account["discord_id"] if account is not None else None
    profile = community_service.get_public_profile(community_id, viewer_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Not found")
    return profile


@router.post("/{community_id}/report", response_model=None)
def report_community_profile(
    community_id: int,
    payload: CommunityReportCreate,
    request: Request,
    auth_service: AuthServiceDep,
    community_service: CommunityAccountServiceDep,
    moderation_service: CommunityModerationServiceDep,
    settings: SettingsDep,
) -> Any:
    status = _require_user(request, auth_service)
    _require_feature(request, auth_service, settings, "profile_reporting")

    reporter = community_service.get_account(str(status["id"]))
    if reporter is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    _require_onboarded(request, auth_service, reporter)
    if community_service.get_account_by_id(community_id) is None:
        raise HTTPException(status_code=404, detail="Not found")

    try:
        return moderation_service.create_report(
            community_id,
            int(reporter["id"]),
            payload,
        )
    except CommunityProfileError as exc:
        return _profile_error_response(exc)