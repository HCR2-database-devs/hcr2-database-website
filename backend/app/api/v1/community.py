from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from app.api.dependencies import (
    get_auth_service,
    get_community_account_service,
    get_community_moderation_service,
)
from app.schemas.community import (
    CommunityAccount,
    CommunityProfileUpdate,
    CommunityReportCreate,
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


def _require_user(request: Request, auth_service: AuthService) -> dict[str, Any]:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return status


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
) -> Any:
    status = _require_user(request, auth_service)

    account = community_service.get_account(str(status["id"]))
    if account is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return account


@router.get("/members", response_model=None)
def community_members(
    community_service: CommunityAccountServiceDep,
    q: Annotated[str | None, Query()] = None,
    sort: Annotated[str | None, Query()] = None,
    country: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
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
) -> Any:
    status = _require_user(request, auth_service)
    try:
        account = community_service.update_profile(str(status["id"]), payload)
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
    banner: Annotated[UploadFile | None, File()] = None,
) -> Any:
    status = _require_user(request, auth_service)
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
) -> Any:
    status = _require_user(request, auth_service)
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
) -> Any:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    viewer_id = str(status["id"]) if status.get("logged") else None
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
) -> Any:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    viewer_id = str(status["id"]) if status.get("logged") else None
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
) -> Any:
    status = _require_user(request, auth_service)

    reporter = community_service.get_account(str(status["id"]))
    if reporter is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
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