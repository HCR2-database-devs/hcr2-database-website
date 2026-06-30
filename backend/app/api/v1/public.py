from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_news_service,
    get_public_data_service,
    get_public_submission_service,
)
from app.api.responses import DATABASE_ERROR_TYPES, database_error_response, error_response
from app.core.config import Settings, get_settings
from app.services.admin_service import maintenance_flag_path
from app.services.news_service import NewsService
from app.services.public_data_service import PublicDataService
from app.services.public_submission_service import PublicSubmissionService


def _check_maintenance() -> None:
    if maintenance_flag_path().exists():
        raise HTTPException(status_code=503, detail="Service is under maintenance")


router = APIRouter(tags=["public"], dependencies=[Depends(_check_maintenance)])

PublicDataServiceDep = Annotated[PublicDataService, Depends(get_public_data_service)]
NewsServiceDep = Annotated[NewsService, Depends(get_news_service)]
PublicSubmissionServiceDep = Annotated[
    PublicSubmissionService,
    Depends(get_public_submission_service),
]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _load_or_database_error(
    service: PublicDataService,
    data_type: str,
) -> list[dict[str, Any]] | JSONResponse:
    try:
        return service.load_data(data_type)
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)  # type: ignore[return-value]


@router.get("/maps", response_model=None)
def list_maps(service: PublicDataServiceDep) -> Any:
    return _load_or_database_error(service, "maps")


@router.get("/vehicles", response_model=None)
def list_vehicles(service: PublicDataServiceDep) -> Any:
    return _load_or_database_error(service, "vehicles")


@router.get("/players", response_model=None)
def list_players(service: PublicDataServiceDep) -> Any:
    return _load_or_database_error(service, "players")


@router.get("/tuning-parts", response_model=None)
def list_tuning_parts(service: PublicDataServiceDep) -> Any:
    return _load_or_database_error(service, "tuning_parts")


@router.get("/tuning-setups", response_model=None)
def list_tuning_setups(service: PublicDataServiceDep) -> Any:
    return _load_or_database_error(service, "tuning_setups")


@router.get("/records", response_model=None)
def list_records(
    service: PublicDataServiceDep,
    q: Annotated[str | None, Query()] = None,
    maps: Annotated[list[str] | None, Query(alias="map")] = None,
    vehicles: Annotated[list[str] | None, Query(alias="vehicle")] = None,
    tuning_parts: Annotated[list[str] | None, Query(alias="tuning_part")] = None,
    sort: Annotated[str | None, Query()] = None,
    questionable: Annotated[str | None, Query()] = None,
    min_distance: Annotated[str | None, Query()] = None,
    max_distance: Annotated[str | None, Query()] = None,
    limit: Annotated[str | None, Query()] = None,
    offset: Annotated[str | None, Query()] = None,
    export: Annotated[str | None, Query()] = None,
    mythic: Annotated[str | None, Query()] = None,
) -> Any:
    filters = {
        "q": q,
        "maps": maps or [],
        "vehicles": vehicles or [],
        "tuning_parts": tuning_parts or [],
        "sort": sort,
        "questionable": questionable,
        "min_distance": min_distance,
        "max_distance": max_distance,
        "limit": limit,
        "offset": offset,
        "export": export,
        "mythic": mythic,
    }
    try:
        return service.list_records_paginated(filters)
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)  # type: ignore[return-value]


@router.get("/records/search", response_model=None)
def search_records(
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
        return database_error_response(exc)  # type: ignore[return-value]


@router.get("/news", response_model=None)
def list_news(
    service: NewsServiceDep,
    limit: Annotated[str | None, Query()] = None,
) -> Any:
    try:
        return service.list_news(limit)
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)  # type: ignore[return-value]


@router.get("/hcaptcha/sitekey", response_model=None)
def get_hcaptcha_sitekey(settings: SettingsDep) -> Any:
    if not settings.hcaptcha_site_key:
        return error_response("hCaptcha is not configured", status_code=500)  # type: ignore[return-value]
    return {"sitekey": settings.hcaptcha_site_key}


@router.post("/submissions", response_model=None)
async def submit_public_record(
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
