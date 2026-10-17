from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import get_auth_service, get_hcr2_link_service
from app.schemas.hcr2_link import (
    AdminAppointmentRequest,
    AdminLinkStatusRequest,
    AdminNoteRequest,
    AdminRejectRequest,
)
from app.services.auth_service import AuthService
from app.services.community_account_service import CommunityProfileError
from app.services.hcr2_link_service import Hcr2LinkService

router = APIRouter(prefix="/admin/hcr2-link", tags=["admin-hcr2-link"])
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
Hcr2LinkServiceDep = Annotated[Hcr2LinkService, Depends(get_hcr2_link_service)]


def _admin_status(request: Request, auth_service: AuthService) -> dict[str, Any]:
    """Reuse the existing hcr2.xyz admin check (``ALLOWED_DISCORD_IDS``).

    The administrator identity always comes from the verified ``WC_TOKEN``
    cookie, never from a request body, so a caller cannot forge it.
    """
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not status.get("allowed"):
        raise HTTPException(status_code=403, detail="Permission denied")
    return status


def _link_error_response(exc: CommunityProfileError) -> JSONResponse:
    return JSONResponse({"error": exc.message}, status_code=exc.status_code)


@router.get("/requests", response_model=None)
def admin_list_requests(
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    status: Annotated[str | None, Query()] = None,
    method: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return link_service.list_requests(
            status=status,
            method=method,
            search=q,
            limit=limit,
            offset=offset,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.get("/requests/{request_id}", response_model=None)
def admin_get_request(
    request_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
) -> Any:
    """Full review payload for one request.

    Includes the exact generated verification code (for team verification), the
    Discord identity, previous attempts, per-step timestamps, admin notes and
    any conflicting claims. None of this is reachable from a user-facing or
    public endpoint.
    """
    _admin_status(request, auth_service)
    detail = link_service.get_request_detail(request_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Not found")
    return detail


@router.post("/requests/{request_id}/approve", response_model=None)
def admin_approve_request(
    request_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    payload: Annotated[AdminNoteRequest | None, Body()] = None,
) -> Any:
    """Approve a submitted request and create the active link.

    Runs in a database transaction that locks the request row, so two admins
    cannot both create a link, and the partial unique indexes are the final
    guard on duplicate active links.
    """
    admin = _admin_status(request, auth_service)
    try:
        return link_service.approve_request(
            request_id,
            admin_username=str(admin.get("username") or ""),
            note=(payload.note if payload else None) or None,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/requests/{request_id}/reject", response_model=None)
def admin_reject_request(
    request_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    payload: Annotated[AdminRejectRequest, Body()],
) -> Any:
    admin = _admin_status(request, auth_service)
    try:
        return link_service.reject_request(
            request_id,
            admin_username=str(admin.get("username") or ""),
            category=payload.category,
            reason=payload.reason,
            note=payload.note,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/requests/{request_id}/retry", response_model=None)
def admin_request_retry(
    request_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    payload: Annotated[AdminNoteRequest | None, Body()] = None,
) -> Any:
    """Send the request back for another attempt without deciding it."""
    admin = _admin_status(request, auth_service)
    try:
        return link_service.request_retry(
            request_id,
            admin_username=str(admin.get("username") or ""),
            note=(payload.note if payload else None) or None,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/requests/{request_id}/appointment", response_model=None)
def admin_set_appointment(
    request_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    payload: Annotated[AdminAppointmentRequest, Body()],
) -> Any:
    """Schedule or update a Discord screen-share appointment.

    Discord DMs and screen sharing are never automated: the owner arranges the
    time in Discord and records the outcome here.
    """
    admin = _admin_status(request, auth_service)
    try:
        return link_service.set_appointment(
            request_id,
            admin_username=str(admin.get("username") or ""),
            appointment_status=payload.appointment_status,
            appointment_at=payload.appointment_at,
            note=payload.note,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/requests/{request_id}/cancel", response_model=None)
def admin_cancel_request(
    request_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    payload: Annotated[AdminNoteRequest | None, Body()] = None,
) -> Any:
    admin = _admin_status(request, auth_service)
    try:
        return link_service.set_terminal_status(
            request_id,
            status="cancelled",
            admin_username=str(admin.get("username") or ""),
            note=(payload.note if payload else None) or None,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.post("/requests/{request_id}/expire", response_model=None)
def admin_expire_request(
    request_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    payload: Annotated[AdminNoteRequest | None, Body()] = None,
) -> Any:
    admin = _admin_status(request, auth_service)
    try:
        return link_service.set_terminal_status(
            request_id,
            status="expired",
            admin_username=str(admin.get("username") or ""),
            note=(payload.note if payload else None) or None,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.get("/links", response_model=None)
def admin_list_links(
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    status: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Any:
    _admin_status(request, auth_service)
    return link_service.list_links(status=status, search=q, limit=limit, offset=offset)


@router.post("/links/{link_id}/status", response_model=None)
def admin_set_link_status(
    link_id: int,
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    payload: Annotated[AdminLinkStatusRequest, Body()],
) -> Any:
    """Revoke, suspend or restore an existing link. Always requires a reason."""
    admin = _admin_status(request, auth_service)
    try:
        return link_service.set_link_status(
            link_id,
            status=payload.status,
            admin_username=str(admin.get("username") or ""),
            reason=payload.reason,
        )
    except CommunityProfileError as exc:
        return _link_error_response(exc)


@router.get("/conflicts", response_model=None)
def admin_conflicts(
    request: Request,
    auth_service: AuthServiceDep,
    link_service: Hcr2LinkServiceDep,
    player_name: Annotated[str, Query()],
) -> Any:
    """Duplicate / competing linking claims for one player name."""
    _admin_status(request, auth_service)
    return link_service.find_conflicts(player_name)