from dataclasses import dataclass
from typing import Any

from app.repositories.community_notification import (
    CommunityNotificationRepository,
)


@dataclass(frozen=True, slots=True)
class CommunityNotificationService:
    notification_repository: CommunityNotificationRepository

    def notify(
        self,
        community_user_id: int,
        notification_type: str,
        message: str,
    ) -> dict[str, Any] | None:
        return self.notification_repository.create_notification(
            community_user_id,
            notification_type,
            message,
        )

    def list_for_user(
        self,
        community_user_id: int,
        *,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        notifications, total = self.notification_repository.list_notifications(
            community_user_id,
            limit=limit,
            offset=offset,
        )
        return {
            "notifications": notifications,
            "unread": self.unread_count(community_user_id),
            "count": total,
            "limit": limit,
            "offset": offset,
        }

    def unread_count(self, community_user_id: int) -> int:
        return self.notification_repository.unread_count(community_user_id)

    def mark_read(
        self,
        notification_id: int,
        community_user_id: int,
    ) -> dict[str, Any] | None:
        return self.notification_repository.mark_read(
            notification_id,
            community_user_id,
        )

    def mark_all_read(self, community_user_id: int) -> int:
        return self.notification_repository.mark_all_read(community_user_id)
