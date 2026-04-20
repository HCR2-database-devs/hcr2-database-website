from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import (
    get_news_service,
    get_public_data_service,
    get_public_submission_service,
)
from app.api.responses import DATABASE_ERROR_TYPES, database_error_response, error_response
from app.core.config import Settings, get_settings
from app.services.news_service import NewsService
from app.services.public_data_service import PublicDataService
from app.services.public_submission_service import PublicSubmissionService

router = APIRouter(tags=["public"])

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
def list_records(service: PublicDataServiceDep) -> Any:
    return _load_or_database_error(service, "records")


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
