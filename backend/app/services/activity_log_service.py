from typing import Any

from app.db.session import DatabaseConfig, open_connection
from app.schemas.activity_log import ActivityLogEntry, ActivityLogFilter, ActivityLogListResponse


class ActivityLogService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def log_action(
        self,
        admin_username: str,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        entity_name: str | None = None,
        note: str | None = None,
    ) -> None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO activity_log
                        (admin_username, action, entity_type, entity_id, entity_name, note)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (admin_username, action, entity_type, entity_id, entity_name, note),
                )

    def get_logs(self, filters: ActivityLogFilter) -> ActivityLogListResponse:
        where_clauses: list[str] = []
        params: list[Any] = []

        if filters.admin_username:
            where_clauses.append("admin_username = %s")
            params.append(filters.admin_username)
        if filters.action:
            where_clauses.append("action = %s")
            params.append(filters.action)
        if filters.entity_type:
            where_clauses.append("entity_type = %s")
            params.append(filters.entity_type)
        if filters.date_from:
            where_clauses.append("created_at >= %s")
            params.append(filters.date_from)
        if filters.date_to:
            where_clauses.append("created_at <= %s")
            params.append(filters.date_to + " 23:59:59")

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT count(*) AS count FROM activity_log{where_sql}",
                    params,
                )
                total = int(cursor.fetchone()["count"])

                cursor.execute(
                    f"""
                    SELECT id, admin_username, action, entity_type, entity_id,
                           entity_name, note, created_at
                    FROM activity_log
                    {where_sql}
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    params + [filters.limit, filters.offset],
                )
                entries = [
                    ActivityLogEntry(
                        id=row["id"],
                        admin_username=row["admin_username"],
                        action=row["action"],
                        entity_type=row["entity_type"],
                        entity_id=row["entity_id"],
                        entity_name=row["entity_name"],
                        note=row["note"],
                        created_at=str(row["created_at"]),
                    )
                    for row in cursor.fetchall()
                ]

        return ActivityLogListResponse(entries=entries, total=total)

    def cleanup_old_logs(self, days: int = 90) -> int:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM activity_log WHERE created_at < NOW() - INTERVAL '%s days'",
                    (days,),
                )
                return cursor.rowcount

    def get_distinct_admins(self) -> list[str]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT DISTINCT admin_username FROM activity_log ORDER BY admin_username"
                )
                return [row["admin_username"] for row in cursor.fetchall()]
