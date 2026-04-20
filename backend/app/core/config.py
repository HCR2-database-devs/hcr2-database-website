import re
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

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

    auth_shared_secret: str | None = Field(default=None, validation_alias="AUTH_SHARED_SECRET")
    allowed_discord_ids: list[str] = Field(
        default_factory=list,
        validation_alias="ALLOWED_DISCORD_IDS",
    )
    api_keys: list[str] = Field(default_factory=list, validation_alias="API_KEYS")

    hcaptcha_site_key: str | None = Field(default=None, validation_alias="HCAPTCHA_SITE_KEY")
    hcaptcha_secret_key: str | None = Field(default=None, validation_alias="HCAPTCHA_SECRET_KEY")

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        validation_alias="CORS_ORIGINS",
    )

    @field_validator("allowed_discord_ids", "api_keys", "cors_origins", mode="before")
    @classmethod
    def parse_env_lists(cls, value: Any) -> list[str]:
        return _split_env_list(value)

    @property
    def postgres_dsn(self) -> str:
        if self.database_url:
            return self.database_url
        required = [self.db_host, self.db_port, self.db_name, self.db_user, self.db_pass]
        if any(value in (None, "") for value in required):
            return ""
        user = quote_plus(str(self.db_user))
        password = quote_plus(str(self.db_pass))
        return f"postgresql://{user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

