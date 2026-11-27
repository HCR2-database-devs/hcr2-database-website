import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.compat import router as compatibility_router
from app.api.share_short import router as share_short_router
from app.api.v1.router import api_router
from app.core.config import get_settings

logger = logging.getLogger("hcr2")
access_logger = logging.getLogger("hcr2.access")

ALLOWED_CORS_METHODS = ["GET", "POST", "OPTIONS"]
ALLOWED_CORS_HEADERS = ["Content-Type", "X-API-Key"]


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=ALLOWED_CORS_METHODS,
            allow_headers=ALLOWED_CORS_HEADERS,
        )

    @app.middleware("http")
    async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.monotonic()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        access_logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((time.monotonic() - started) * 1000, 2),
            },
        )
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", uuid.uuid4().hex)
        logger.error(
            "Unhandled exception",
            exc_info=(type(exc), exc, exc.__traceback__),
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )
        return JSONResponse(
            {"error": "Internal Server Error"},
            status_code=500,
            headers={"X-Request-ID": request_id},
        )

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(compatibility_router)
    # Root-level short links such as /u/1234. Nginx must proxy this prefix.
    app.include_router(share_short_router)

    @app.get("/health", tags=["health"])
    def root_health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
        }

    return app


app = create_app()
