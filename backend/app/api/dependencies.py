from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.repositories.news import PostgresNewsRepository
from app.repositories.public_data import PostgresPublicDataRepository
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.services.news_service import NewsService
from app.services.public_data_service import PublicDataService
from app.services.public_submission_service import PublicSubmissionService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_public_data_service() -> PublicDataService:
    return PublicDataService(PostgresPublicDataRepository())


def get_news_service() -> NewsService:
    return NewsService(PostgresNewsRepository())


def get_auth_service(settings: SettingsDep) -> AuthService:
    return AuthService(
        shared_secret=settings.auth_shared_secret,
        allowed_discord_ids=settings.allowed_discord_ids,
    )


def get_admin_service() -> AdminService:
    return AdminService()


def get_public_submission_service(settings: SettingsDep) -> PublicSubmissionService:
    return PublicSubmissionService(settings)
