from typing import Any, Protocol

from app.db.session import DatabaseConfig, open_connection

NOTIFICATION_COLUMNS = """
    id, community_user_id, type, message,
    created_at, read_at
"""


class CommunityNotificationRepository(Protocol):
    def create_notification(
        self,
        community_user_id: int,
        notification_type: str,
        message: str,
    ) -> dict[str, Any] | None: ...

    def list_notifications(
        self,
        community_user_id: int,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]: ...

    def unread_count(self, community_user_id: int) -> int: ...

    def mark_read(
        self,
        notification_id: int,
        community_user_id: int,
    ) -> dict[str, Any] | None: ...

    def mark_all_read(self, community_user_id: int) -> int: ...


class PostgresCommunityNotificationRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def create_notification(
        self,
        community_user_id: int,
        notification_type: str,
        message: str,
    ) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO community_user_notification
                        (community_user_id, type, message)
                    VALUES (%(community_user_id)s, %(note_type)s, %(message)s)
                    RETURNING {NOTIFICATION_COLUMNS}
                    """,
                    {
                        "community_user_id": community_user_id,
                        "note_type": notification_type,
                        "message": message,
                    },
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def list_notifications(
        self,
        community_user_id: int,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {NOTIFICATION_COLUMNS}
                    FROM community_user_notification
                    WHERE community_user_id = %(community_user_id)s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    {
                        "community_user_id": community_user_id,
                        "limit": limit,
                        "offset": offset,
                    },
                )
                rows = [dict(row) for row in cursor.fetchall()]

                cursor.execute(
                    """
                    SELECT count(*)::int AS count
                    FROM community_user_notification
                    WHERE community_user_id = %(community_user_id)s
                    """,
                    {"community_user_id": community_user_id},
                )
                total = int(cursor.fetchone()["count"])
                return rows, total

    def unread_count(self, community_user_id: int) -> int:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT count(*)::int AS count
                    FROM community_user_notification
                    WHERE community_user_id = %(community_user_id)s
                      AND read_at IS NULL
                    """,
                    {"community_user_id": community_user_id},
                )
                return int(cursor.fetchone()["count"])

    def mark_read(
        self,
        notification_id: int,
        community_user_id: int,
    ) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE community_user_notification SET
                        read_at = CURRENT_TIMESTAMP
                    WHERE id = %(notification_id)s
                      AND community_user_id = %(community_user_id)s
                      AND read_at IS NULL
                    RETURNING {NOTIFICATION_COLUMNS}
                    """,
                    {
                        "notification_id": notification_id,
                        "community_user_id": community_user_id,
                    },
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def mark_all_read(self, community_user_id: int) -> int:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE community_user_notification SET
                        read_at = CURRENT_TIMESTAMP
                    WHERE community_user_id = %(community_user_id)s
                      AND read_at IS NULL
                    """,
                    {"community_user_id": community_user_id},
                )
                return cursor.rowcount
