from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_auth_service
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.get("/auth/status", response_model=None)
def auth_status(
    request: Request,
    service: AuthServiceDep,
) -> dict[str, Any]:
    return service.status_from_cookie(request.cookies.get("WC_TOKEN"))


@router.get("/auth/logout")
def auth_logout() -> RedirectResponse:
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("PHPSESSID", path="/", domain=".hcr2.xyz", secure=True, httponly=True)
    response.delete_cookie("WC_TOKEN", path="/", domain=".hcr2.xyz", secure=True, httponly=True)
    return response
