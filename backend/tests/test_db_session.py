import pytest

from app.core.config import Settings
from app.db.session import DatabaseConfig, DatabaseNotConfigured, get_database_config, open_connection


def test_open_connection_requires_database_configuration() -> None:
    with pytest.raises(DatabaseNotConfigured):
        open_connection(DatabaseConfig(dsn=""))


def test_database_config_uses_settings_connect_timeout() -> None:
    config = get_database_config(
        Settings(
            _env_file=None,
            DATABASE_URL="postgresql://db.example.test/hcr2",
            DB_CONNECT_TIMEOUT="9",
        )
    )

    assert config.connect_timeout == 9
