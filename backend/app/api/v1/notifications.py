from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import (
    get_auth_service,
    get_community_account_service,
    get_community_notification_service,
    get_settings,
)
from app.core.config import Settings
from app.core.features import can_use_feature
from app.schemas.community_notification import (
    CommunityNotificationListResponse,
    NotificationReadRequest,
    NotificationReadResult,
)
from app.services.auth_service import AuthService
from app.services.community_account_service import CommunityAccountService
from app.services.community_notification_service import CommunityNotificationService

router = APIRouter(prefix="/community/notifications", tags=["community notifications"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CommunityAccountServiceDep = Annotated[
    CommunityAccountService,
    Depends(get_community_account_service),
]
CommunityNotificationServiceDep = Annotated[
    CommunityNotificationService,
    Depends(get_community_notification_service),
]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _require_status(request: Request, auth_service: AuthService) -> dict[str, Any]:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    if not status.get("logged"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return status


def _require_feature(
    request: Request,
    auth_service: AuthService,
    settings: Settings,
    feature_name: str,
) -> None:
    status = auth_service.status_from_cookie(request.cookies.get("WC_TOKEN"))
    discord_id = str(status["id"]) if status.get("logged") else None
    if not can_use_feature(discord_id, feature_name, settings):
        raise HTTPException(status_code=403, detail="This feature is currently in beta")


def _require_account(
    status: dict[str, Any],
    account_service: CommunityAccountService,
) -> dict[str, Any]:
    account = account_service.get_account(str(status["id"]))
    if account is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account


@router.get("", response_model=CommunityNotificationListResponse)
def list_notifications_route(
    request: Request,
    auth_service: AuthServiceDep,
    account_service: CommunityAccountServiceDep,
    notification_service: CommunityNotificationServiceDep,
    settings: SettingsDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, Any]:
    status = _require_status(request, auth_service)
    _require_feature(request, auth_service, settings, "community_notifications")
    account = _require_account(status, account_service)
    return notification_service.list_for_user(int(account["id"]), limit=limit, offset=offset)


@router.post("/read", response_model=NotificationReadResult)
def read_notification_route(
    payload: NotificationReadRequest,
    request: Request,
    auth_service: AuthServiceDep,
    account_service: CommunityAccountServiceDep,
    notification_service: CommunityNotificationServiceDep,
    settings: SettingsDep,
) -> dict[str, Any]:
    status = _require_status(request, auth_service)
    _require_feature(request, auth_service, settings, "community_notifications")
    account = _require_account(status, account_service)
    community_user_id = int(account["id"])
    if payload.notification_ids:
        updated = 0
        for notification_id in payload.notification_ids:
            if notification_service.mark_read(notification_id, community_user_id) is not None:
                updated += 1
    else:
        updated = notification_service.mark_all_read(community_user_id)
    return {"updated": updated}