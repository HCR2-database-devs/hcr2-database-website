from app.core.config import Settings
from app.core.features import (
    FEATURE_FIELDS,
    FeatureState,
    can_use_feature,
    get_feature_state,
    is_beta_user,
)


def _settings(**kwargs) -> Settings:
    return Settings(
        _env_file=None,
        BETA_DISCORD_IDS="beta-user",
        ALLOWED_DISCORD_IDS="admin-user",
        **kwargs,
    )


def test_get_feature_state_reads_settings() -> None:
    settings = _settings(
        FEATURE_DISCORD_ACCOUNTS="ENABLED",
        FEATURE_COMMUNITY_PROFILES="DISABLED",
    )

    assert get_feature_state("discord_accounts", settings) is FeatureState.ENABLED
    assert get_feature_state("community_profiles", settings) is FeatureState.DISABLED
    assert get_feature_state("community_members", settings) is FeatureState.BETA


def test_get_feature_state_falls_back_to_beta_for_unknown_feature() -> None:
    settings = _settings()

    assert get_feature_state("not_a_feature", settings) is FeatureState.BETA


def test_feature_registry_covers_all_known_features() -> None:
    settings = _settings()

    for feature_name in ("discord_accounts", "community_profiles", "profile_customization",
                         "community_members", "profile_reporting"):
        assert feature_name in FEATURE_FIELDS
        assert get_feature_state(feature_name, settings) is not None


def test_is_beta_user_matches_discord_allowlist() -> None:
    settings = _settings()

    assert is_beta_user("beta-user", settings) is True
    assert is_beta_user("admin-user", settings) is False
    assert is_beta_user("other", settings) is False
    assert is_beta_user(None, settings) is False


def test_can_use_feature_when_enabled_allows_everyone() -> None:
    settings = _settings(FEATURE_DISCORD_ACCOUNTS="ENABLED")

    assert can_use_feature(None, "discord_accounts", settings) is True
    assert can_use_feature("beta-user", "discord_accounts", settings) is True
    assert can_use_feature("admin-user", "discord_accounts", settings) is True
    assert can_use_feature("other", "discord_accounts", settings) is True


def test_can_use_feature_when_disabled_denies_everyone() -> None:
    settings = _settings(FEATURE_COMMUNITY_PROFILES="DISABLED")

    assert can_use_feature(None, "community_profiles", settings) is False
    assert can_use_feature("beta-user", "community_profiles", settings) is False
    assert can_use_feature("admin-user", "community_profiles", settings) is False


def test_can_use_feature_when_beta_only_allows_beta_and_admin() -> None:
    settings = _settings()

    assert can_use_feature(None, "community_members", settings) is False
    assert can_use_feature("other", "community_members", settings) is False
    assert can_use_feature("beta-user", "community_members", settings) is True
    assert can_use_feature("admin-user", "community_members", settings) is True