from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.dependencies import (
    get_auth_service,
    get_news_service,
    get_public_data_service,
    get_public_submission_service,
)
from app.api.responses import DATABASE_ERROR_TYPES, database_error_response, legacy_error_response
from app.core.config import Settings, get_settings
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
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/php/load_data.php", response_model=None)
def legacy_load_data(
    service: PublicDataServiceDep,
    data_type: Annotated[str | None, Query(alias="type")] = None,
) -> Any:
    try:
        return service.load_data(data_type)
    except MissingLoadDataType as exc:
        return legacy_error_response(str(exc))
    except InvalidLoadDataType as exc:
        return legacy_error_response(str(exc))
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)


@router.get("/php/get_news.php", response_model=None)
def legacy_get_news(
    service: NewsServiceDep,
    limit: Annotated[str | None, Query()] = None,
) -> Any:
    try:
        return service.list_news(limit)
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)


@router.get("/php/get_hcaptcha_sitekey.php", response_model=None)
def legacy_get_hcaptcha_sitekey(settings: SettingsDep) -> Any:
    if not settings.hcaptcha_site_key:
        return legacy_error_response("hCaptcha is not configured", status_code=500)
    return {"sitekey": settings.hcaptcha_site_key}


@router.post("/php/public_submit.php", response_model=None)
async def legacy_public_submit(
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


@router.get("/auth/status.php", response_model=None)
def legacy_auth_status(
    request: Request,
    service: AuthServiceDep,
) -> dict[str, Any]:
    return service.status_from_cookie(request.cookies.get("WC_TOKEN"))


@router.get("/auth/logout.php")
def legacy_auth_logout(
    oauth_state: Annotated[str | None, Query()] = None,
    code: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    if oauth_state or code:
        return RedirectResponse(url="/", status_code=302)

    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("PHPSESSID", path="/", domain=".hcr2.xyz", secure=True, httponly=True)
    response.delete_cookie("WC_TOKEN", path="/", domain=".hcr2.xyz", secure=True, httponly=True)
    return response
