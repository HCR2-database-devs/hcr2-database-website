from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.dependencies import (
    get_admin_service,
    get_auth_service,
    get_news_service,
    get_public_data_service,
    get_public_submission_service,
)
from app.api.responses import DATABASE_ERROR_TYPES, database_error_response, error_response
from app.core.config import Settings, get_settings
from app.schemas.admin import (
    AddMapRequest,
    AddTuningPartRequest,
    AddTuningSetupRequest,
    AddVehicleRequest,
    AssignSetupRequest,
    DeleteNewsRequest,
    DeleteRecordRequest,
    PostNewsRequest,
    SetMaintenanceRequest,
    SetQuestionableRequest,
    SubmitRecordRequest,
    UpdateNewsRequest,
)
from app.services.admin_service import (
    AdminConflictError,
    AdminNotFoundError,
    AdminService,
    AdminServiceError,
    AdminUnsupportedMediaError,
)
from app.services.auth_service import AuthService
from app.services.news_service import NewsService
from app.services.public_data_service import (
    InvalidLoadDataType,
    MissingLoadDataType,
    PublicDataService,
)
from app.services.public_submission_service import PublicSubmissionService

router = APIRouter()

PublicDataServiceDep = Annotated[PublicDataService, Depends(get_public_data_service)]
NewsServiceDep = Annotated[NewsService, Depends(get_news_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
PublicSubmissionServiceDep = Annotated[
    PublicSubmissionService,
    Depends(get_public_submission_service),
]
AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _admin_status(request: Request, auth_service: AuthService) -> dict[str, Any] | JSONResponse:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    if not status.get("allowed"):
        return JSONResponse({"error": "Permission denied"}, status_code=403)
    return status


def _admin_error(exc: AdminServiceError) -> JSONResponse:
    return JSONResponse({"error": str(exc)}, status_code=exc.status_code)


async def _request_data(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        data = await request.json()
        return data if isinstance(data, dict) else {}
    form = await request.form()
    return dict(form)


@router.get("/php/load_data.php", response_model=None)
def compatibility_load_data(
    service: PublicDataServiceDep,
    data_type: Annotated[str | None, Query(alias="type")] = None,
) -> Any:
    try:
        return service.load_data(data_type)
    except MissingLoadDataType as exc:
        return error_response(str(exc))
    except InvalidLoadDataType as exc:
        return error_response(str(exc))
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)


@router.get("/php/api_records.php", response_model=None)
def compatibility_api_records(
    request: Request,
    service: PublicDataServiceDep,
    settings: SettingsDep,
) -> Any:
    api_key = request.query_params.get("api_key") or request.headers.get("X-API-Key")
    if not api_key or api_key not in settings.api_keys:
        return JSONResponse({"error": "Unauthorized: invalid API key"}, status_code=401)
    try:
        return service.search_records(dict(request.query_params))
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)


@router.get("/php/get_news.php", response_model=None)
def compatibility_get_news(
    service: NewsServiceDep,
    limit: Annotated[str | None, Query()] = None,
) -> Any:
    try:
        return service.list_news(limit)
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)


@router.get("/php/get_hcaptcha_sitekey.php", response_model=None)
def compatibility_get_hcaptcha_sitekey(settings: SettingsDep) -> Any:
    if not settings.hcaptcha_site_key:
        return error_response("hCaptcha is not configured", status_code=500)
    return {"sitekey": settings.hcaptcha_site_key}


@router.get("/php/maintenance_status.php", response_model=None)
def compatibility_maintenance_status(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    return admin_service.maintenance_status(bool(status.get("allowed")))


@router.post("/php/public_submit.php", response_model=None)
async def compatibility_public_submit(
    request: Request,
    service: PublicSubmissionServiceDep,
) -> JSONResponse:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)
    if not isinstance(data, dict):
        data = {}

    result = service.submit(data, request.client.host if request.client else "")
    return JSONResponse(content=result.payload, status_code=result.status_code)


@router.post("/php/submit_record.php", response_model=None)
async def compatibility_submit_record(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    try:
        return admin_service.submit_record(SubmitRecordRequest(**await _request_data(request)))
    except (AdminServiceError, AdminNotFoundError, AdminConflictError) as exc:
        return _admin_error(exc)


@router.post("/php/delete_record.php", response_model=None)
async def compatibility_delete_record(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    try:
        return admin_service.delete_record(DeleteRecordRequest(**await _request_data(request)))
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _admin_error(exc)


@router.post("/php/set_questionable.php", response_model=None)
async def compatibility_set_questionable(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    try:
        payload = SetQuestionableRequest(**await _request_data(request))
        return admin_service.set_questionable(payload)
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _admin_error(exc)


@router.post("/php/assign_setup.php", response_model=None)
async def compatibility_assign_setup(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    try:
        return admin_service.assign_setup(AssignSetupRequest(**await _request_data(request)))
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _admin_error(exc)


async def _catalog_icon(data: dict[str, Any]) -> tuple[str | None, str | None, bytes | None]:
    upload = data.get("icon")
    if upload is None or not getattr(upload, "filename", None):
        return None, None, None
    return (
        getattr(upload, "filename", None),
        getattr(upload, "content_type", None),
        await upload.read(),
    )


@router.post("/php/add_map.php", response_model=None)
async def compatibility_add_map(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    data = await _request_data(request)
    name = str(data.get("mapName") or data.get("map_name") or data.get("name") or "")
    filename, content_type, content = await _catalog_icon(data)
    try:
        admin_service.validate_icon_upload(filename, content_type, content)
        result = admin_service.add_map(AddMapRequest(mapName=name))
        result["iconMessage"] = admin_service.save_icon(
            "map_icons",
            name,
            filename,
            content_type,
            content,
        )
        return result
    except (AdminServiceError, AdminConflictError, AdminUnsupportedMediaError) as exc:
        return _admin_error(exc)


@router.post("/php/add_vehicle.php", response_model=None)
async def compatibility_add_vehicle(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    data = await _request_data(request)
    name = str(data.get("vehicleName") or data.get("vehicle_name") or data.get("name") or "")
    filename, content_type, content = await _catalog_icon(data)
    try:
        admin_service.validate_icon_upload(filename, content_type, content)
        result = admin_service.add_vehicle(AddVehicleRequest(vehicleName=name))
        result["iconMessage"] = admin_service.save_icon(
            "vehicle_icons",
            name,
            filename,
            content_type,
            content,
        )
        return result
    except (AdminServiceError, AdminConflictError, AdminUnsupportedMediaError) as exc:
        return _admin_error(exc)


@router.post("/php/add_tuning_part.php", response_model=None)
async def compatibility_add_tuning_part(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    data = await _request_data(request)
    name = str(data.get("partName") or data.get("part_name") or data.get("name") or "")
    filename, content_type, content = await _catalog_icon(data)
    try:
        admin_service.validate_icon_upload(filename, content_type, content)
        result = admin_service.add_tuning_part(AddTuningPartRequest(partName=name))
        result["iconMessage"] = admin_service.save_icon(
            "tuning_parts_icons",
            name,
            filename,
            content_type,
            content,
        )
        return result
    except (AdminServiceError, AdminConflictError, AdminUnsupportedMediaError) as exc:
        return _admin_error(exc)


@router.post("/php/add_tuning_setup.php", response_model=None)
async def compatibility_add_tuning_setup(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    try:
        return admin_service.add_tuning_setup(AddTuningSetupRequest(**await _request_data(request)))
    except (AdminServiceError, AdminNotFoundError, AdminConflictError) as exc:
        return _admin_error(exc)


@router.post("/php/set_maintenance.php", response_model=None)
async def compatibility_set_maintenance(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    payload = SetMaintenanceRequest(**await _request_data(request))
    return admin_service.set_maintenance(payload.action, payload.maintenance)


@router.get("/auth/admin_pending.php", response_model=None)
def compatibility_admin_pending_get(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    return admin_service.list_pending()


@router.post("/auth/admin_pending.php", response_model=None)
async def compatibility_admin_pending_post(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    data = await _request_data(request)
    submission_id = int(data.get("id") or 0)
    try:
        if data.get("action") == "approve":
            return admin_service.approve_submission(submission_id)
        if data.get("action") == "reject":
            return admin_service.reject_submission(submission_id)
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _admin_error(exc)
    return {"error": "Unknown action"}


@router.post("/auth/post_news.php", response_model=None)
async def compatibility_post_news(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    try:
        return admin_service.post_news(
            PostNewsRequest(**await _request_data(request)),
            str(admin.get("username") or ""),
        )
    except AdminServiceError as exc:
        return _admin_error(exc)


@router.post("/auth/edit_news.php", response_model=None)
async def compatibility_edit_news(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    data = await _request_data(request)
    try:
        news_id = int(data.get("id") or 0)
        payload = UpdateNewsRequest(
            title=str(data.get("title") or ""),
            content=str(data.get("content") or ""),
        )
        return admin_service.update_news(news_id, payload)
    except (ValueError, AdminServiceError) as exc:
        if isinstance(exc, ValueError):
            return _admin_error(AdminServiceError("News ID, title, and content are required."))
        return _admin_error(exc)


@router.post("/auth/delete_news.php", response_model=None)
async def compatibility_delete_news(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    data = await _request_data(request)
    try:
        return admin_service.delete_news(DeleteNewsRequest(id=int(data.get("id") or 0)))
    except (ValueError, AdminServiceError) as exc:
        if isinstance(exc, ValueError):
            return _admin_error(AdminServiceError("Invalid news ID."))
        return _admin_error(exc)


@router.get("/auth/admin_actions.php", response_model=None)
def compatibility_admin_actions_get(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
    action: Annotated[str | None, Query()] = None,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    if action == "download_db":
        return JSONResponse(
            {"error": "PostgreSQL database download via this endpoint is not supported."},
            status_code=501,
        )
    return admin_service.list_backups()


@router.post("/auth/admin_actions.php", response_model=None)
async def compatibility_admin_actions_post(
    request: Request,
    admin_service: AdminServiceDep,
    auth_service: AuthServiceDep,
) -> Any:
    admin = _admin_status(request, auth_service)
    if isinstance(admin, JSONResponse):
        return admin
    data = await _request_data(request)
    action = data.get("action")
    try:
        if action == "create_backup":
            return admin_service.create_backup()
        if action == "list_backups":
            return admin_service.list_backups()
        if action == "delete":
            return admin_service.delete_backup(str(data.get("filename") or ""))
        if action == "integrity":
            return admin_service.integrity_check()
    except (AdminServiceError, AdminNotFoundError) as exc:
        return _admin_error(exc)
    return {"error": "Unknown action"}


@router.get("/auth/status.php", response_model=None)
def compatibility_auth_status(
    request: Request,
    service: AuthServiceDep,
) -> dict[str, Any]:
    return service.status_from_cookie(request.cookies.get("WC_TOKEN"))


@router.get("/auth/logout.php")
def compatibility_auth_logout(
    oauth_state: Annotated[str | None, Query()] = None,
    code: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    if oauth_state or code:
        return RedirectResponse(url="/", status_code=302)

    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("PHPSESSID", path="/", domain=".hcr2.xyz", secure=True, httponly=True)
    response.delete_cookie("WC_TOKEN", path="/", domain=".hcr2.xyz", secure=True, httponly=True)
    return response
