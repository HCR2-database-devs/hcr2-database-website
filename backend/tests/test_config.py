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


def test_hcr2_account_linking_flag_defaults_to_beta() -> None:
    settings = Settings(_env_file=None)

    assert settings.feature_hcr2_account_linking == "BETA"




def test_hcr2_link_configuration_defaults() -> None:
    settings = Settings(_env_file=None)

    # Team details ship empty so nothing is invented before an operator fills
    # them in; the wizard then reports the method as not configured.
    assert settings.hcr2_link_verification_team_name == ""
    assert settings.hcr2_link_verification_team_password == ""
    assert settings.hcr2_link_verification_team_details == ""
    assert settings.hcr2_link_discord_invite_url == "https://discord.gg/GGQPunUbHj"
    assert settings.hcr2_link_owner_handles == ["nipatsuyt", "titaniumhcr2", "yazi.arod"]
    assert settings.hcr2_link_code_ttl_seconds == 900
    assert settings.hcr2_link_code_reroll_cooldown_seconds == 10
    assert settings.hcr2_link_request_ttl_days == 30
    assert settings.hcr2_link_code_rate_limit == 6
    assert settings.hcr2_link_code_rate_window_seconds == 300
    assert settings.hcr2_link_request_rate_limit == 5
    assert settings.hcr2_link_request_rate_window_seconds == 3600
    assert settings.hcr2_link_admin_action_rate_limit == 60
    assert settings.hcr2_link_admin_action_rate_window_seconds == 3600
    assert settings.hcr2_link_max_open_requests == 3
    # Method C is off until an operator enables it.
    assert settings.hcr2_link_challenge_enabled is False
    assert settings.hcr2_link_challenge_instructions == ""
    assert settings.hcr2_link_challenge_max_distance_m == 2000




def test_hcr2_link_configuration_reads_the_environment() -> None:
    settings = Settings(
        _env_file=None,
        HCR2_LINK_VERIFICATION_TEAM_NAME="hcr2xyz verify",
        HCR2_LINK_VERIFICATION_TEAM_PASSWORD="swordfish",
        HCR2_LINK_DISCORD_INVITE_URL="https://discord.example/invite",
        HCR2_LINK_OWNER_HANDLES="one,two",
        HCR2_LINK_CODE_REROLL_COOLDOWN_SECONDS="25",
    )

    assert settings.hcr2_link_verification_team_name == "hcr2xyz verify"
    assert settings.hcr2_link_verification_team_password == "swordfish"
    assert settings.hcr2_link_discord_invite_url == "https://discord.example/invite"
    assert settings.hcr2_link_owner_handles == ["one", "two"]
    assert settings.hcr2_link_code_reroll_cooldown_seconds == 25




def test_hcr2_link_code_secret_falls_back_to_the_auth_secret() -> None:
    with_rate_secret = Settings(
        _env_file=None,
        AUTH_SHARED_SECRET="auth",
        SUBMISSION_RATE_LIMIT_HMAC_SECRET="rate",
    )
    with_auth_secret = Settings(_env_file=None, AUTH_SHARED_SECRET="auth")
    with_neither = Settings(_env_file=None)

    assert with_rate_secret.hcr2_link_code_secret == "rate"
    assert with_auth_secret.hcr2_link_code_secret == "auth"
    assert with_neither.hcr2_link_code_secret == ""




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
