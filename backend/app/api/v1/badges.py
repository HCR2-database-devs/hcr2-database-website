from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_auth_service,
    get_badge_service,
    get_community_account_service,
)
from app.core.config import Settings, get_settings
from app.core.features import Feature, can_use_feature
from app.repositories.badge import BadgeError
from app.schemas.badges import (
    BadgeAwardRequest,
    BadgeCategoryCreate,
    BadgeCategoryUpdate,
    BadgeDefinitionCreate,
    BadgeDefinitionUpdate,
    BadgeRevokeRequest,
    FeaturedBadgesUpdate,
)
from app.services.auth_service import AuthService
from app.services.badge_service import BadgeService
from app.services.community_account_service import CommunityAccountService

router = APIRouter(prefix="/badges", tags=["badges"])
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
BadgeServiceDep = Annotated[BadgeService, Depends(get_badge_service)]
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
    if not can_use_feature(discord_id, Feature.COMMUNITY_BADGES, settings):
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


def _error(exc: BadgeError) -> JSONResponse:
    return JSONResponse({"error": exc.message}, status_code=exc.status_code)


@router.get("/catalog", response_model=None)
def badge_catalog(
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    community_service: CommunityServiceDep,
    settings: SettingsDep,
    category: Annotated[str | None, Query()] = None,
    badge_type: Annotated[str | None, Query(alias="badgeType")] = None,
    scope: Annotated[str, Query(pattern="^(all|owned|locked)$")] = "all",
) -> Any:
    discord_id = _require_feature(request, auth_service, settings)
    user_id = None
    if discord_id is not None:
        account = community_service.get_account(discord_id)
        if account is not None:
            user_id = int(account["id"])
    if scope in {"owned", "locked"} and user_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        return badge_service.get_catalog(
            community_user_id=user_id,
            category=category,
            badge_type=badge_type,
            scope=scope,
        )
    except BadgeError as exc:
        return _error(exc)


@router.get("/categories", response_model=None)
def badge_categories(
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
) -> Any:
    _require_feature(request, auth_service, settings)
    return {"categories": badge_service.repository.list_categories()}


@router.get("/detail/{identifier}", response_model=None)
def badge_detail(
    identifier: str,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    community_service: CommunityServiceDep,
    settings: SettingsDep,
) -> Any:
    discord_id = _require_feature(request, auth_service, settings)
    user_id = None
    if discord_id is not None:
        account = community_service.get_account(discord_id)
        if account is not None:
            user_id = int(account["id"])
    detail = badge_service.get_detail(identifier, community_user_id=user_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Not found")
    return detail


@router.get("/me/featured", response_model=None)
def own_featured_badges(
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    community_service: CommunityServiceDep,
    settings: SettingsDep,
) -> Any:
    user_id = _own_user_id(request, auth_service, community_service, settings)
    return {"featured": badge_service.repository.list_featured(user_id)}


@router.put("/me/featured", response_model=None)
def update_own_featured_badges(
    payload: FeaturedBadgesUpdate,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    community_service: CommunityServiceDep,
    settings: SettingsDep,
) -> Any:
    user_id = _own_user_id(request, auth_service, community_service, settings)
    try:
        return {"featured": badge_service.set_featured(user_id, payload.badge_ids)}
    except BadgeError as exc:
        return _error(exc)


@router.get("/members/{user_id}", response_model=None)
def member_badges(
    user_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    community_service: CommunityServiceDep,
    settings: SettingsDep,
) -> Any:
    discord_id = _require_feature(request, auth_service, settings)
    viewer = community_service.get_public_profile(user_id, discord_id)
    if viewer is None:
        raise HTTPException(status_code=404, detail="Not found")
    if not viewer.get("is_owner") and not viewer.get("show_badges"):
        raise HTTPException(status_code=403, detail="This member hides their badges.")
    return badge_service.get_profile_badges(user_id)


@router.get("/admin/definitions", response_model=None)
def admin_list_definitions(
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
    include_admin: Annotated[bool, Query()] = True,
) -> Any:
    _admin_status(request, auth_service, settings)
    return {
        "badges": badge_service.repository.list_definitions(include_admin=include_admin),
        "categories": badge_service.repository.list_categories(include_disabled=True),
    }


@router.post("/admin/definitions", response_model=None)
def admin_create_definition(
    payload: BadgeDefinitionCreate,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
) -> Any:
    _admin_status(request, auth_service, settings)
    try:
        return badge_service.create_definition(payload)
    except BadgeError as exc:
        return _error(exc)


@router.patch("/admin/definitions/{badge_id}", response_model=None)
def admin_update_definition(
    badge_id: int,
    payload: BadgeDefinitionUpdate,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
) -> Any:
    _admin_status(request, auth_service, settings)
    try:
        updated = badge_service.update_definition(badge_id, payload)
    except BadgeError as exc:
        return _error(exc)
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.post("/admin/definitions/{badge_id}/archive", response_model=None)
def admin_archive_definition(
    badge_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
) -> Any:
    _admin_status(request, auth_service, settings)
    archived = badge_service.archive_definition(badge_id)
    if archived is None:
        raise HTTPException(status_code=404, detail="Not found")
    return archived


@router.post("/admin/definitions/{badge_id}/icon", response_model=None)
async def admin_upload_badge_icon(
    badge_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
    upload: Annotated[UploadFile, File(...)],
) -> Any:
    _admin_status(request, auth_service, settings)
    definition = badge_service.repository.get_definition(badge_id)
    if definition is None:
        raise HTTPException(status_code=404, detail="Not found")
    content = await upload.read()
    try:
        return badge_service.upload_icon(
            identifier=str(definition["identifier"]),
            filename=upload.filename,
            content_type=upload.content_type,
            content=content,
        )
    except BadgeError as exc:
        return _error(exc)


@router.post("/admin/categories", response_model=None)
def admin_create_category(
    payload: BadgeCategoryCreate,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
) -> Any:
    _admin_status(request, auth_service, settings)
    try:
        return badge_service.create_category(payload)
    except BadgeError as exc:
        return _error(exc)


@router.patch("/admin/categories/{category_id}", response_model=None)
def admin_update_category(
    category_id: int,
    payload: BadgeCategoryUpdate,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
) -> Any:
    _admin_status(request, auth_service, settings)
    try:
        updated = badge_service.update_category(category_id, payload)
    except BadgeError as exc:
        return _error(exc)
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.post("/admin/award", response_model=None)
def admin_award_badge(
    payload: BadgeAwardRequest,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
) -> Any:
    admin = _admin_status(request, auth_service, settings)
    try:
        return badge_service.award_manual(
            badge_identifier=payload.badge_identifier,
            badge_id=payload.badge_id,
            user_ids=payload.user_ids,
            actor=str(admin.get("username") or ""),
            reason=payload.reason,
            public_reason=payload.public_reason,
        )
    except BadgeError as exc:
        return _error(exc)


@router.post("/admin/user-badges/{user_badge_id}/revoke", response_model=None)
def admin_revoke_badge(
    user_badge_id: int,
    payload: BadgeRevokeRequest,
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
) -> Any:
    admin = _admin_status(request, auth_service, settings)
    try:
        return badge_service.revoke(
            user_badge_id=user_badge_id,
            actor=str(admin.get("username") or ""),
            reason=payload.reason,
        )
    except BadgeError as exc:
        return _error(exc)


@router.get("/admin/history", response_model=None)
def admin_badge_history(
    request: Request,
    auth_service: AuthServiceDep,
    badge_service: BadgeServiceDep,
    settings: SettingsDep,
    community_user_id: Annotated[int | None, Query()] = None,
    badge_id: Annotated[int | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
    _admin_status(request, auth_service, settings)
    try:
        return badge_service.list_history(
            community_user_id=community_user_id,
            badge_id=badge_id,
            limit=limit,
            offset=offset,
        )
    except BadgeError as exc:
        return _error(exc)
