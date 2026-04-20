from dataclasses import dataclass

from app.core.config import Settings, get_settings


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    dsn: str

    @property
    def is_configured(self) -> bool:
        return bool(self.dsn)


def get_database_config(settings: Settings | None = None) -> DatabaseConfig:
    active_settings = settings or get_settings()
    return DatabaseConfig(dsn=active_settings.postgres_dsn)

