from hashlib import sha1
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse

from app.api.dependencies import get_share_service
from app.api.responses import DATABASE_ERROR_TYPES, database_error_response
from app.services.admin_service import maintenance_flag_path
from app.services.share_service import RecordNotFound, ShareService


def _check_maintenance() -> None:
    if maintenance_flag_path().exists():
        raise HTTPException(status_code=503, detail="Service is under maintenance")


router = APIRouter(prefix="/share", tags=["share"], dependencies=[Depends(_check_maintenance)])

ShareServiceDep = Annotated[ShareService, Depends(get_share_service)]


@router.get("/records/{record_id}.png")
def share_record_image(record_id: int, request: Request, service: ShareServiceDep) -> Any:
    try:
        png = service.og_image(record_id)
    except RecordNotFound:
        raise HTTPException(status_code=404, detail="Record not found") from None
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)  # type: ignore[return-value]

    etag = '"' + sha1(png).hexdigest() + '"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})

    return Response(
        content=png,
        media_type="image/png",
        headers={"ETag": etag, "Cache-Control": "public, max-age=86400"},
    )


@router.get("/records/{record_id}", response_class=HTMLResponse)
def share_record_page(record_id: int, service: ShareServiceDep) -> Any:
    try:
        page = service.share_page(record_id)
    except RecordNotFound:
        raise HTTPException(status_code=404, detail="Record not found") from None
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)  # type: ignore[return-value]
    return HTMLResponse(content=page)