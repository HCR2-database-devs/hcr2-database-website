from app.core.config import Settings


def test_settings_parse_comma_separated_lists() -> None:
    settings = Settings(
        _env_file=None,
        ALLOWED_DISCORD_IDS="111,222\n333",
        BETA_DISCORD_IDS="beta-1,beta-2",
        API_KEYS="alpha,beta",
        CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173",
    )

    assert settings.allowed_discord_ids == ["111", "222", "333"]
    assert settings.beta_discord_ids == ["beta-1", "beta-2"]
    assert settings.api_keys == ["alpha", "beta"]
    assert settings.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_settings_feature_flags_default_to_enabled() -> None:
    settings = Settings(_env_file=None)

    assert settings.feature_discord_accounts == "ENABLED"
    assert settings.feature_community_profiles == "ENABLED"
    assert settings.feature_profile_customization == "ENABLED"
    assert settings.feature_community_members == "ENABLED"
    assert settings.feature_profile_reporting == "ENABLED"
    assert settings.feature_community_notifications == "ENABLED"


def test_settings_profile_cooldowns_default_to_seven_days() -> None:
    settings = Settings(_env_file=None)

    assert settings.username_change_cooldown_days == 7
    assert settings.banner_change_cooldown_days == 7


def test_settings_profile_cooldowns_accept_environment_values() -> None:
    settings = Settings(
        _env_file=None,
        USERNAME_CHANGE_COOLDOWN_DAYS="14",
        BANNER_CHANGE_COOLDOWN_DAYS="3",
    )

    assert settings.username_change_cooldown_days == 14
    assert settings.banner_change_cooldown_days == 3


def test_settings_feature_flags_accept_valid_and_normalize_invalid_values() -> None:
    settings = Settings(
        _env_file=None,
        FEATURE_DISCORD_ACCOUNTS="enabled",
        FEATURE_COMMUNITY_PROFILES="DISABLED",
        FEATURE_PROFILE_CUSTOMIZATION="garbage",
        FEATURE_COMMUNITY_MEMBERS="beta",
        FEATURE_PROFILE_REPORTING="",
        FEATURE_COMMUNITY_NOTIFICATIONS="disabled",
    )

    assert settings.feature_discord_accounts == "ENABLED"
    assert settings.feature_community_profiles == "DISABLED"
    assert settings.feature_profile_customization == "BETA"
    assert settings.feature_community_members == "BETA"
    assert settings.feature_profile_reporting == "BETA"
    assert settings.feature_community_notifications == "DISABLED"


def test_settings_parse_comma_separated_lists_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("ALLOWED_DISCORD_IDS", "dev-admin,qa-admin")
    monkeypatch.setenv("API_KEYS", "dev-api-key")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    settings = Settings(_env_file=None)

    assert settings.allowed_discord_ids == ["dev-admin", "qa-admin"]
    assert settings.api_keys == ["dev-api-key"]
    assert settings.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_settings_build_postgres_dsn_from_database_variables() -> None:
    settings = Settings(
        _env_file=None,
        DB_HOST="db.example.test",
        DB_PORT="5432",
        DB_NAME="hcr2",
        DB_USER="user name",
        DB_PASS="pass word",
    )

    assert settings.postgres_dsn == "postgresql://user+name:pass+word@db.example.test:5432/hcr2"


def test_settings_database_url_takes_precedence() -> None:
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://direct.example.test/hcr2",
        DB_HOST="db.example.test",
        DB_PORT="5432",
        DB_NAME="hcr2",
        DB_USER="user",
        DB_PASS="pass",
    )

    assert settings.postgres_dsn == "postgresql://direct.example.test/hcr2"


def test_settings_support_pg_environment_aliases() -> None:
    settings = Settings(
        _env_file=None,
        PGHOST="pg.example.test",
        PGPORT="5433",
        PGDATABASE="hcr2",
        PGUSER="pg user",
        PGPASSWORD="pg pass",
    )

    assert settings.postgres_dsn == "postgresql://pg+user:pg+pass@pg.example.test:5433/hcr2"


def test_settings_exposes_schema_aliases() -> None:
    assert Settings(_env_file=None, DB_SCHEMA="rehearsal").postgres_schema == "rehearsal"
    assert Settings(_env_file=None, PGSCHEMA="fallback").postgres_schema == "fallback"


def test_settings_exposes_database_connect_timeout() -> None:
    assert Settings(_env_file=None).db_connect_timeout == 5
    assert Settings(_env_file=None, DB_CONNECT_TIMEOUT="12").db_connect_timeout == 12
