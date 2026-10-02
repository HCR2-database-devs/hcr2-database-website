import asyncio
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from app.api.responses import DATABASE_ERROR_TYPES, database_error_response
from app.core.network import trusted_client_ip
from app.services.auth_service import AuthService
from app.services.community_account_service import CommunityAccountService
from app.services.public_submission_service import (
    DISABLED_SUBMISSION_ERROR,
    PublicSubmissionService,
    SubmissionResult,
)
from app.services.submission_identity import (
    UNRESOLVED_IDENTITY_ERROR,
    SubmissionIdentityError,
    resolve_submission_identity,
)


async def read_submission_data(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        try:
            data = await request.json()
        except (ValueError, TypeError):
            return {}
    else:
        form = await request.form()
        data = dict(form)
    return data if isinstance(data, dict) else {}


def _submit(
    service: PublicSubmissionService,
    data: dict[str, Any],
    submitter_ip: str | None,
    identity: Any,
) -> SubmissionResult:
    submit_with_identity = getattr(service, "submit_with_identity", None)
    if callable(submit_with_identity):
        return submit_with_identity(data, submitter_ip, identity)
    if identity is not None:
        return service.submit(data, submitter_ip, identity=identity)
    return service.submit(data, submitter_ip or "")


async def handle_public_submission(
    request: Request,
    service: PublicSubmissionService,
    auth_service: AuthService,
    community_service: CommunityAccountService,
) -> JSONResponse:
    data = await read_submission_data(request)
    try:
        identity = await asyncio.to_thread(
            resolve_submission_identity,
            request,
            auth_service,
            community_service,
        )
    except SubmissionIdentityError:
        return JSONResponse({"error": UNRESOLVED_IDENTITY_ERROR}, status_code=403)
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)

    if identity is not None and getattr(identity, "admin_disabled", False):
        return JSONResponse({"error": DISABLED_SUBMISSION_ERROR}, status_code=403)

    try:
        result = await asyncio.to_thread(
            _submit,
            service,
            data,
            trusted_client_ip(request),
            identity,
        )
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)
    headers = {}
    retry_after = getattr(result, "retry_after", None)
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return JSONResponse(content=result.payload, status_code=result.status_code, headers=headers)
