from app.core.config import Settings


def test_settings_parse_comma_separated_lists() -> None:
    settings = Settings(
        ALLOWED_DISCORD_IDS="111,222\n333",
        API_KEYS="alpha,beta",
        CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173",
    )

    assert settings.allowed_discord_ids == ["111", "222", "333"]
    assert settings.api_keys == ["alpha", "beta"]
    assert settings.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_settings_build_postgres_dsn_from_legacy_database_variables() -> None:
    settings = Settings(
        DB_HOST="db.example.test",
        DB_PORT="5432",
        DB_NAME="hcr2",
        DB_USER="user name",
        DB_PASS="pass word",
    )

    assert settings.postgres_dsn == "postgresql://user+name:pass+word@db.example.test:5432/hcr2"


def test_settings_database_url_takes_precedence() -> None:
    settings = Settings(
        DATABASE_URL="postgresql://direct.example.test/hcr2",
        DB_HOST="db.example.test",
        DB_PORT="5432",
        DB_NAME="hcr2",
        DB_USER="user",
        DB_PASS="pass",
    )

    assert settings.postgres_dsn == "postgresql://direct.example.test/hcr2"
