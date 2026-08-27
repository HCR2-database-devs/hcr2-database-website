from typing import Any, Protocol

from app.db.session import DatabaseConfig, open_connection


class ChangelogRepository(Protocol):
    def list_changelog(self, limit: int) -> list[dict[str, Any]]: ...


class PostgresChangelogRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def list_changelog(self, limit: int) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, version, title, added, changed, fixed, author, created_at
                    FROM changelog
                    ORDER BY created_at DESC, id DESC
                    LIMIT %(limit)s
                    """,
                    {"limit": limit},
                )
                return [dict(row) for row in cursor.fetchall()]