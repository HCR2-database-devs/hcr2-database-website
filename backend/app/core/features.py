from enum import StrEnum

from app.core.config import Settings
from app.core.security import is_allowed_admin

VALID_FEATURE_STATES = ("DISABLED", "BETA", "ENABLED")


class FeatureState(StrEnum):
    DISABLED = "DISABLED"
    BETA = "BETA"
    ENABLED = "ENABLED"


class Feature:
    DISCORD_ACCOUNTS = "discord_accounts"
    COMMUNITY_PROFILES = "community_profiles"
    PROFILE_CUSTOMIZATION = "profile_customization"
    COMMUNITY_MEMBERS = "community_members"
    PROFILE_REPORTING = "profile_reporting"


FEATURE_FIELDS: dict[str, str] = {
    Feature.DISCORD_ACCOUNTS: "feature_discord_accounts",
    Feature.COMMUNITY_PROFILES: "feature_community_profiles",
    Feature.PROFILE_CUSTOMIZATION: "feature_profile_customization",
    Feature.COMMUNITY_MEMBERS: "feature_community_members",
    Feature.PROFILE_REPORTING: "feature_profile_reporting",
}


def get_feature_state(feature_name: str, settings: Settings) -> FeatureState:
    field_name = FEATURE_FIELDS.get(feature_name)
    raw = getattr(settings, field_name, "BETA") if field_name else None
    try:
        return FeatureState(str(raw).strip().upper())
    except ValueError:
        return FeatureState.BETA


def is_beta_user(discord_id: str | None, settings: Settings) -> bool:
    if discord_id is None:
        return False
    return str(discord_id) in settings.beta_discord_ids


def can_use_feature(
    discord_id: str | None,
    feature_name: str,
    settings: Settings,
) -> bool:
    state = get_feature_state(feature_name, settings)
    if state is FeatureState.DISABLED:
        return False
    if state is FeatureState.ENABLED:
        return True
    if discord_id is None:
        return False
    return is_beta_user(discord_id, settings) or is_allowed_admin(
        discord_id,
        settings.allowed_discord_ids,
    )