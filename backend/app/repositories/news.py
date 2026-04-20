from typing import Any, Protocol

from app.db.session import DatabaseConfig, open_connection


class NewsRepository(Protocol):
    def list_news(self, limit: int) -> list[dict[str, Any]]: ...


class PostgresNewsRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def list_news(self, limit: int) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, title, content, author, created_at
                    FROM News
                    ORDER BY created_at DESC
                    LIMIT %(limit)s
                    """,
                    {"limit": limit},
                )
                return [dict(row) for row in cursor.fetchall()]
