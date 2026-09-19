from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.repositories.changelog import PostgresChangelogRepository
from app.repositories.community_moderation import PostgresCommunityModerationRepository
from app.repositories.community_notification import PostgresCommunityNotificationRepository
from app.repositories.community_user import PostgresCommunityUserRepository
from app.repositories.news import PostgresNewsRepository
from app.repositories.public_data import PostgresPublicDataRepository
from app.services.activity_log_service import ActivityLogService
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.services.changelog_service import ChangelogService
from app.services.community_account_service import CommunityAccountService
from app.services.community_moderation_service import CommunityModerationService
from app.services.community_notification_service import CommunityNotificationService
from app.services.news_service import NewsService
from app.services.public_data_service import PublicDataService
from app.services.public_submission_service import PublicSubmissionService
from app.services.share_service import ShareService
from app.services.stats_service import StatsService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_public_data_service() -> PublicDataService:
    return PublicDataService(PostgresPublicDataRepository())


def get_news_service() -> NewsService:
    return NewsService(PostgresNewsRepository())


def get_changelog_service() -> ChangelogService:
    return ChangelogService(PostgresChangelogRepository())


def get_auth_service(settings: SettingsDep) -> AuthService:
    return AuthService(
        shared_secret=settings.auth_shared_secret,
        allowed_discord_ids=settings.allowed_discord_ids,
        beta_discord_ids=settings.beta_discord_ids,
    )


def get_community_account_service() -> CommunityAccountService:
    return CommunityAccountService(PostgresCommunityUserRepository())


def get_community_notification_service() -> CommunityNotificationService:
    return CommunityNotificationService(PostgresCommunityNotificationRepository())


def get_community_moderation_service(settings: SettingsDep) -> CommunityModerationService:
    return CommunityModerationService(
        moderation_repository=PostgresCommunityModerationRepository(),
        community_repository=PostgresCommunityUserRepository(),
        activity_log=get_activity_log_service(),
        hcaptcha_secret_key=settings.hcaptcha_secret_key,
        notification_service=get_community_notification_service(),
    )


def get_admin_service() -> AdminService:
    return AdminService(activity_log=get_activity_log_service())


def get_activity_log_service() -> ActivityLogService:
    return ActivityLogService()


def get_public_submission_service(settings: SettingsDep) -> PublicSubmissionService:
    return PublicSubmissionService(settings)


def get_stats_service() -> StatsService:
    return StatsService()


def get_share_service() -> ShareService:
    return ShareService()
