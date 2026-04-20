from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import get_admin_service, get_auth_service
from app.schemas.admin import (
    AddMapRequest,
    AddTuningPartRequest,
    AddTuningSetupRequest,
    AddVehicleRequest,
    AssignSetupRequest,
    DeleteRecordRequest,
    PendingActionRequest,
    PostNewsRequest,
    SetMaintenanceRequest,
    SetQuestionableRequest,
    SubmitRecordRequest,
)
from app.services.admin_service import (
    AdminConflictError,
    AdminNotFoundError,
    AdminService,
    AdminServiceError,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["admin"])

AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def _admin_status(request: Request, auth_service: AuthService) -> dict[str, Any]:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not status.get("allowed"):
        raise HTTPException(status_code=403, detail="Permission denied")
    return status


def _error_response(exc: AdminServiceError) -> JSONResponse:
    return JSONResponse({"error": str(exc)}, status_code=exc.status_code)


@router.get("/records", response_model=None)
def list_admin_records(
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    return service.list_records()


@router.post("/records", response_model=None)
def submit_record(
    payload: SubmitRecordRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.submit_record(payload)
    except (AdminServiceError, AdminNotFoundError, AdminConflictError) as exc:
        return _error_response(exc)


@router.delete("/records/{record_id}", response_model=None)
def delete_record_by_path(
    record_id: int,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    return service.delete_record(DeleteRecordRequest(recordId=record_id))


@router.post("/records/delete", response_model=None)
def delete_record(
    payload: DeleteRecordRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    return service.delete_record(payload)


@router.patch("/records/{record_id}/questionable", response_model=None)
def set_questionable_by_path(
    record_id: int,
    payload: SetQuestionableRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    payload.record_id = record_id
    try:
        return service.set_questionable(payload)
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _error_response(exc)


@router.patch("/records/questionable", response_model=None)
def set_questionable(
    payload: SetQuestionableRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.set_questionable(payload)
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _error_response(exc)


@router.patch("/records/{record_id}/tuning-setup", response_model=None)
def assign_tuning_setup_by_path(
    record_id: int,
    payload: AssignSetupRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    payload.record_id = record_id
    try:
        return service.assign_setup(payload)
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _error_response(exc)


@router.patch("/records/tuning-setup", response_model=None)
def assign_tuning_setup(
    payload: AssignSetupRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.assign_setup(payload)
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _error_response(exc)


@router.post("/maps", response_model=None)
def add_map(
    payload: AddMapRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.add_map(payload)
    except (AdminServiceError, AdminConflictError) as exc:
        return _error_response(exc)


@router.post("/vehicles", response_model=None)
def add_vehicle(
    payload: AddVehicleRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.add_vehicle(payload)
    except (AdminServiceError, AdminConflictError) as exc:
        return _error_response(exc)


@router.post("/tuning-parts", response_model=None)
def add_tuning_part(
    payload: AddTuningPartRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.add_tuning_part(payload)
    except (AdminServiceError, AdminConflictError) as exc:
        return _error_response(exc)


@router.post("/tuning-setups", response_model=None)
def add_tuning_setup(
    payload: AddTuningSetupRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.add_tuning_setup(payload)
    except (AdminServiceError, AdminNotFoundError, AdminConflictError) as exc:
        return _error_response(exc)


@router.get("/pending", response_model=None)
def list_pending(
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    return service.list_pending()


@router.post("/pending/{submission_id}/approve", response_model=None)
def approve_pending_by_path(
    submission_id: int,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.approve_submission(submission_id)
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _error_response(exc)


@router.post("/pending/{submission_id}/reject", response_model=None)
def reject_pending_by_path(
    submission_id: int,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.reject_submission(submission_id)
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _error_response(exc)


@router.post("/pending/approve", response_model=None)
def approve_pending(
    payload: PendingActionRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.approve_submission(payload.id)
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _error_response(exc)


@router.post("/pending/reject", response_model=None)
def reject_pending(
    payload: PendingActionRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    try:
        return service.reject_submission(payload.id)
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _error_response(exc)


@router.post("/news", response_model=None)
def post_news(
    payload: PostNewsRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    try:
        return service.post_news(payload, str(admin.get("username") or ""))
    except AdminServiceError as exc:
        return _error_response(exc)


@router.get("/maintenance", response_model=None)
def maintenance_status(
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    return service.maintenance_status(bool(status.get("allowed")))


@router.patch("/maintenance", response_model=None)
def set_maintenance(
    payload: SetMaintenanceRequest,
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    return service.set_maintenance(payload.action, payload.maintenance)


@router.get("/integrity", response_model=None)
def integrity_check(
    request: Request,
    service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    return service.integrity_check()
