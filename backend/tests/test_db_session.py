import pytest

from app.db.session import DatabaseConfig, DatabaseNotConfigured, open_connection


def test_open_connection_requires_database_configuration() -> None:
    with pytest.raises(DatabaseNotConfigured):
        open_connection(DatabaseConfig(dsn=""))
