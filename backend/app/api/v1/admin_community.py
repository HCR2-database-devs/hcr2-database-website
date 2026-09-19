from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import get_auth_service, get_community_moderation_service
from app.schemas.community import AdminNote, AdminProfileUpdate
from app.services.auth_service import AuthService
from app.services.community_account_service import CommunityProfileError
from app.services.community_moderation_service import CommunityModerationService

router = APIRouter(prefix="/admin/community", tags=["admin-community"])
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CommunityModerationServiceDep = Annotated[
    CommunityModerationService,
    Depends(get_community_moderation_service),
]


def _admin_status(request: Request, auth_service: AuthService) -> dict[str, Any]:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not status.get("allowed"):
        raise HTTPException(status_code=403, detail="Permission denied")
    return status


def _profile_error_response(exc: CommunityProfileError) -> JSONResponse:
    return JSONResponse({"error": exc.message}, status_code=exc.status_code)


def _require_or_404(
    moderation_service: CommunityModerationService,
    community_id: int,
) -> dict[str, Any]:
    profile = moderation_service.get_profile(community_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Not found")
    return profile


@router.get("/profiles", response_model=None)
def admin_list_profiles(
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
    q: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
    _admin_status(request, auth_service)
    return moderation_service.list_profiles(search=q, limit=limit, offset=offset)


@router.get("/profiles/{community_id}", response_model=None)
def admin_get_profile(
    community_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    profile = _require_or_404(moderation_service, community_id)
    history = moderation_service.get_username_history(community_id)
    return {**profile, "username_history": history}


@router.patch("/profiles/{community_id}", response_model=None)
def admin_update_profile(
    community_id: int,
    payload: AdminProfileUpdate,
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    _require_or_404(moderation_service, community_id)
    admin_username = str(admin.get("username") or "")
    try:
        if payload.username is not None:
            profile = moderation_service.get_profile(community_id)
            if profile and profile.get("username") != payload.username:
                moderation_service.set_username(
                    community_id,
                    payload.username,
                    admin_username,
                )
        updated = moderation_service.update_profile(
            community_id,
            payload,
            admin_username,
        )
    except CommunityProfileError as exc:
        return _profile_error_response(exc)
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.post("/profiles/{community_id}/username", response_model=None)
def admin_set_username(
    community_id: int,
    payload: AdminProfileUpdate,
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    _require_or_404(moderation_service, community_id)
    try:
        updated = moderation_service.set_username(
            community_id,
            payload.username or "",
            str(admin.get("username") or ""),
        )
    except CommunityProfileError as exc:
        return _profile_error_response(exc)
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.post("/profiles/{community_id}/reset-username", response_model=None)
def admin_reset_username(
    community_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
    payload: Annotated[AdminNote | None, Body()] = None,
) -> Any:
    admin = _admin_status(request, auth_service)
    _require_or_404(moderation_service, community_id)
    updated = moderation_service.reset_username(
        community_id,
        str(admin.get("username") or ""),
        note=(payload.note if payload else None) or None,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.post("/profiles/{community_id}/disable", response_model=None)
def admin_disable_profile(
    community_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
    payload: Annotated[AdminNote | None, Body()] = None,
) -> Any:
    admin = _admin_status(request, auth_service)
    _require_or_404(moderation_service, community_id)
    updated = moderation_service.set_disabled(
        community_id,
        True,
        str(admin.get("username") or ""),
        note=(payload.note if payload else None) or None,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.post("/profiles/{community_id}/enable", response_model=None)
def admin_enable_profile(
    community_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
    payload: Annotated[AdminNote | None, Body()] = None,
) -> Any:
    admin = _admin_status(request, auth_service)
    _require_or_404(moderation_service, community_id)
    updated = moderation_service.set_disabled(
        community_id,
        False,
        str(admin.get("username") or ""),
        note=(payload.note if payload else None) or None,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.post("/profiles/{community_id}/reset", response_model=None)
def admin_reset_profile(
    community_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
    payload: Annotated[AdminNote | None, Body()] = None,
) -> Any:
    admin = _admin_status(request, auth_service)
    _require_or_404(moderation_service, community_id)
    updated = moderation_service.reset_profile(
        community_id,
        str(admin.get("username") or ""),
        note=(payload.note if payload else None) or None,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.post("/profiles/{community_id}/reset-banner", response_model=None)
def admin_reset_banner(
    community_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
    payload: Annotated[AdminNote | None, Body()] = None,
) -> Any:
    admin = _admin_status(request, auth_service)
    _require_or_404(moderation_service, community_id)
    updated = moderation_service.reset_banner(
        community_id,
        str(admin.get("username") or ""),
        note=(payload.note if payload else None) or None,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Not found")
    return updated


@router.get("/reports", response_model=None)
def admin_list_reports(
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
    status: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
    _admin_status(request, auth_service)
    return moderation_service.list_reports(status=status, limit=limit, offset=offset)


@router.post("/reports/{report_id}/resolve", response_model=None)
def admin_resolve_report(
    report_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
    payload: Annotated[AdminNote | None, Body()] = None,
) -> Any:
    admin = _admin_status(request, auth_service)
    try:
        return moderation_service.resolve_report(
            report_id,
            True,
            str(admin.get("username") or ""),
            note=(payload.note if payload else None) or None,
        )
    except CommunityProfileError as exc:
        return _profile_error_response(exc)


@router.post("/reports/{report_id}/reject", response_model=None)
def admin_reject_report(
    report_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    moderation_service: CommunityModerationServiceDep,
    payload: Annotated[AdminNote | None, Body()] = None,
) -> Any:
    admin = _admin_status(request, auth_service)
    try:
        return moderation_service.resolve_report(
            report_id,
            False,
            str(admin.get("username") or ""),
            note=(payload.note if payload else None) or None,
        )
    except CommunityProfileError as exc:
        return _profile_error_response(exc)