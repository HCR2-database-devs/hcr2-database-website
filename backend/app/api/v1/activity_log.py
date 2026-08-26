from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_activity_log_service, get_auth_service
from app.schemas.activity_log import ActivityLogFilter
from app.services.activity_log_service import ActivityLogService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])

ActivityLogServiceDep = Annotated[ActivityLogService, Depends(get_activity_log_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def _admin_status(request: Request, auth_service: AuthService) -> dict[str, Any]:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not status.get("allowed"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Permission denied")
    return status


@router.get("", response_model=None)
def list_activity_logs(
    request: Request,
    service: ActivityLogServiceDep,
    auth_service: AuthServiceDep,
    admin_username: str | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Any:
    _admin_status(request, auth_service)
    filters = ActivityLogFilter(
        admin_username=admin_username,
        action=action,
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return service.get_logs(filters)


@router.get("/admins", response_model=None)
def list_admins(
    request: Request,
    service: ActivityLogServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    _admin_status(request, auth_service)
    return {"admins": service.get_distinct_admins()}


@router.post("/cleanup", response_model=None)
def cleanup_logs(
    request: Request,
    service: ActivityLogServiceDep,
    auth_service: AuthServiceDep,
    days: int = 90,
) -> Any:
    _admin_status(request, auth_service)
    deleted = service.cleanup_old_logs(days)
    return {"success": True, "deleted": deleted}
