from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.api.dependencies import get_news_service, get_public_data_service
from app.api.responses import DATABASE_ERROR_TYPES, database_error_response, legacy_error_response
from app.core.config import Settings, get_settings
from app.services.news_service import NewsService
from app.services.public_data_service import PublicDataService

router = APIRouter(tags=["public"])

PublicDataServiceDep = Annotated[PublicDataService, Depends(get_public_data_service)]
NewsServiceDep = Annotated[NewsService, Depends(get_news_service)]
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
        return legacy_error_response("hCaptcha is not configured", status_code=500)  # type: ignore[return-value]
    return {"sitekey": settings.hcaptcha_site_key}
