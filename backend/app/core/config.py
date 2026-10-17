import re
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import quote_plus

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _split_env_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[\n,]+", value) if item.strip()]
    return [str(value).strip()] if str(value).strip() else []


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_ROOT / ".env"),
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="HCR2 Records API", validation_alias="APP_NAME")
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    db_host: str | None = Field(default=None, validation_alias="DB_HOST")
    db_port: str | None = Field(default=None, validation_alias="DB_PORT")
    db_name: str | None = Field(default=None, validation_alias="DB_NAME")
    db_user: str | None = Field(default=None, validation_alias="DB_USER")
    db_pass: str | None = Field(default=None, validation_alias="DB_PASS")
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    pg_host: str | None = Field(default=None, validation_alias="PGHOST")
    pg_port: str | None = Field(default=None, validation_alias="PGPORT")
    pg_database: str | None = Field(default=None, validation_alias="PGDATABASE")
    pg_user: str | None = Field(default=None, validation_alias="PGUSER")
    pg_password: str | None = Field(default=None, validation_alias="PGPASSWORD")
    db_schema: str | None = Field(default=None, validation_alias="DB_SCHEMA")
    pg_schema: str | None = Field(default=None, validation_alias="PGSCHEMA")
    db_connect_timeout: int = Field(default=5, validation_alias="DB_CONNECT_TIMEOUT")

    auth_shared_secret: str | None = Field(default=None, validation_alias="AUTH_SHARED_SECRET")
    allowed_discord_ids: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        validation_alias="ALLOWED_DISCORD_IDS",
    )
    beta_discord_ids: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        validation_alias="BETA_DISCORD_IDS",
    )
    api_keys: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        validation_alias="API_KEYS",
    )

    hcaptcha_site_key: str | None = Field(default=None, validation_alias="HCAPTCHA_SITE_KEY")
    hcaptcha_secret_key: str | None = Field(default=None, validation_alias="HCAPTCHA_SECRET_KEY")

    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        validation_alias="CORS_ORIGINS",
    )

    # Feature flags. Valid values: DISABLED, BETA, ENABLED (see app/core/features.py).
    feature_discord_accounts: str = Field(
        default="BETA",
        validation_alias="FEATURE_DISCORD_ACCOUNTS",
    )
    feature_community_profiles: str = Field(
        default="BETA",
        validation_alias="FEATURE_COMMUNITY_PROFILES",
    )
    feature_profile_customization: str = Field(
        default="BETA",
        validation_alias="FEATURE_PROFILE_CUSTOMIZATION",
    )
    feature_community_members: str = Field(
        default="BETA",
        validation_alias="FEATURE_COMMUNITY_MEMBERS",
    )
    feature_profile_reporting: str = Field(
        default="BETA",
        validation_alias="FEATURE_PROFILE_REPORTING",
    )
    feature_community_notifications: str = Field(
        default="BETA",
        validation_alias="FEATURE_COMMUNITY_NOTIFICATIONS",
    )
    # Phase 4 ships in BETA: linking is reviewed by a human, so it starts
    # restricted to BETA_DISCORD_IDS and admins while the review queue is
    # exercised. Promote to ENABLED once the flow is comfortable.
    feature_hcr2_account_linking: str = Field(
        default="BETA",
        validation_alias="FEATURE_HCR2_ACCOUNT_LINKING",
    )

    username_change_cooldown_days: int = Field(
        default=30,
        validation_alias="USERNAME_CHANGE_COOLDOWN_DAYS",
    )

    # Phase 4: HCR2 player account linking.
    #
    # There is no official Fingersoft API available to us, so nothing here is
    # ever verified automatically. The team name/password are only shown to
    # authenticated users who already passed the feature gate, and are never
    # written to the database or to the activity log.
    hcr2_link_verification_team_name: str = Field(
        default="",
        validation_alias="HCR2_LINK_VERIFICATION_TEAM_NAME",
    )
    hcr2_link_verification_team_password: str = Field(
        default="",
        validation_alias="HCR2_LINK_VERIFICATION_TEAM_PASSWORD",
    )
    hcr2_link_verification_team_details: str = Field(
        default="",
        validation_alias="HCR2_LINK_VERIFICATION_TEAM_DETAILS",
    )
    hcr2_link_discord_invite_url: str = Field(
        default="https://discord.gg/GGQPunUbHj",
        validation_alias="HCR2_LINK_DISCORD_INVITE_URL",
    )
    hcr2_link_owner_handles: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["nipatsuyt", "titaniumhcr2", "yazi.arod"],
        validation_alias="HCR2_LINK_OWNER_HANDLES",
    )

    # Method C: playhcr.com jeep challenge. Off unless an operator turns it on,
    # so a deployment cannot start offering a method whose instructions nobody
    # has written yet.
    hcr2_link_challenge_enabled: bool = Field(
        default=False,
        validation_alias="HCR2_LINK_CHALLENGE_ENABLED",
    )
    hcr2_link_challenge_instructions: str = Field(
        default="",
        validation_alias="HCR2_LINK_CHALLENGE_INSTRUCTIONS",
    )
    hcr2_link_challenge_max_distance_m: int = Field(
        default=2000,
        validation_alias="HCR2_LINK_CHALLENGE_MAX_DISTANCE_M",
    )

    hcr2_link_code_ttl_seconds: int = Field(
        default=900,
        validation_alias="HCR2_LINK_CODE_TTL_SECONDS",
    )
    hcr2_link_code_reroll_cooldown_seconds: int = Field(
        default=10,
        validation_alias="HCR2_LINK_CODE_REROLL_COOLDOWN_SECONDS",
    )
    hcr2_link_request_ttl_days: int = Field(
        default=30,
        validation_alias="HCR2_LINK_REQUEST_TTL_DAYS",
    )
    hcr2_link_code_rate_limit: int = Field(
        default=6,
        validation_alias="HCR2_LINK_CODE_RATE_LIMIT",
    )
    hcr2_link_code_rate_window_seconds: int = Field(
        default=300,
        validation_alias="HCR2_LINK_CODE_RATE_WINDOW_SECONDS",
    )
    hcr2_link_request_rate_limit: int = Field(
        default=5,
        validation_alias="HCR2_LINK_REQUEST_RATE_LIMIT",
    )
    hcr2_link_request_rate_window_seconds: int = Field(
        default=3600,
        validation_alias="HCR2_LINK_REQUEST_RATE_WINDOW_SECONDS",
    )
    hcr2_link_admin_action_rate_limit: int = Field(
        default=60,
        validation_alias="HCR2_LINK_ADMIN_ACTION_RATE_LIMIT",
    )
    hcr2_link_admin_action_rate_window_seconds: int = Field(
        default=3600,
        validation_alias="HCR2_LINK_ADMIN_ACTION_RATE_WINDOW_SECONDS",
    )
    hcr2_link_max_open_requests: int = Field(
        default=3,
        validation_alias="HCR2_LINK_MAX_OPEN_REQUESTS",
    )

    @property
    def hcr2_link_code_secret(self) -> str:
        """HMAC pepper for hashing verification code tokens.

        Reuses the auth secret so no new secret variable is required. A
        missing value still produces a working (if unkeyed) hash, which keeps
        local development simple.
        """
        return self.auth_shared_secret or ""

    @field_validator(
        "allowed_discord_ids",
        "api_keys",
        "cors_origins",
        "beta_discord_ids",
        "hcr2_link_owner_handles",
        mode="before",
    )
    @classmethod
    def parse_env_lists(cls, value: Any) -> list[str]:
        return _split_env_list(value)

    @field_validator(
        "feature_discord_accounts",
        "feature_community_profiles",
        "feature_profile_customization",
        "feature_community_members",
        "feature_profile_reporting",
        "feature_community_notifications",
        "feature_hcr2_account_linking",
        mode="before",
    )
    @classmethod
    def normalize_feature_flag(cls, value: Any) -> str:
        raw = str(value).strip().upper() if value is not None else ""
        if raw not in ("DISABLED", "BETA", "ENABLED"):
            return "BETA"
        return raw

    @property
    def postgres_dsn(self) -> str:
        if self.database_url:
            return self.database_url
        host = self.db_host or self.pg_host
        port = self.db_port or self.pg_port or "5432"
        name = self.db_name or self.pg_database
        user_name = self.db_user or self.pg_user
        password_value = self.db_pass or self.pg_password
        required = [host, port, name, user_name, password_value]
        if any(value in (None, "") for value in required):
            return ""
        user = quote_plus(str(user_name))
        password = quote_plus(str(password_value))
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    @property
    def postgres_schema(self) -> str | None:
        return self.db_schema or self.pg_schema


@lru_cache
def get_settings() -> Settings:
    return Settings()
