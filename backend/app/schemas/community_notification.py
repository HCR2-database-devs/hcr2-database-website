from datetime import datetime

from pydantic import BaseModel


class CommunityNotification(BaseModel):
    id: int
    community_user_id: int
    type: str
    message: str
    created_at: datetime
    read_at: datetime | None = None


class CommunityNotificationListResponse(BaseModel):
    notifications: list[CommunityNotification]
    count: int
    unread: int
    limit: int
    offset: int


class NotificationReadResult(BaseModel):
    updated: int


class NotificationReadRequest(BaseModel):
    notification_ids: list[int] = []
