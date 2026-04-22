from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.core.config import Settings, get_settings


class DatabaseNotConfigured(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    dsn: str
    schema: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.dsn)


def get_database_config(settings: Settings | None = None) -> DatabaseConfig:
    active_settings = settings or get_settings()
    return DatabaseConfig(
        dsn=active_settings.postgres_dsn,
        schema=active_settings.postgres_schema,
    )


def open_connection(
    config: DatabaseConfig | None = None,
) -> psycopg.Connection[dict[str, Any]]:
    active_config = config or get_database_config()
    if not active_config.is_configured:
        raise DatabaseNotConfigured("Database connection settings are not configured.")
    connection = psycopg.connect(active_config.dsn, row_factory=dict_row)
    if active_config.schema:
        schema_name = active_config.schema
        valid_schema = schema_name.replace("_", "a").isalnum() and not schema_name[0].isdigit()
        if not valid_schema:
            connection.close()
            raise DatabaseNotConfigured("Invalid database schema name.")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT set_config('search_path', %s, false)",
                (f"{schema_name}, public",),
            )
    return connection
