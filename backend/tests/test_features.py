from app.core.config import Settings
from app.core.features import (
    FEATURE_FIELDS,
    Feature,
    FeatureState,
    can_use_feature,
    get_feature_state,
    is_beta_user,
)

_ALL_FEATURES = tuple(FEATURE_FIELDS)

#: Phase 4 (HCR2 player account linking) ships restricted on purpose, because
#: verification is reviewed by a human and the review queue has to be exercised
#: before it is opened up. Every Phase 1-3 feature is public by default.
_ALL_BETA_FLAGS = {f"FEATURE_{name.upper()}": "BETA" for name in _ALL_FEATURES}


def _settings(**kwargs) -> Settings:
    return Settings(
        _env_file=None,
        BETA_DISCORD_IDS="beta-user",
        ALLOWED_DISCORD_IDS="admin-user",
        **{**_ALL_BETA_FLAGS, **kwargs},
    )


def test_community_features_default_to_public() -> None:
    settings = Settings(
        _env_file=None,
        BETA_DISCORD_IDS="beta-user",
        ALLOWED_DISCORD_IDS="admin-user",
    )

    for feature_name in _ALL_FEATURES:
        if feature_name is Feature.HCR2_ACCOUNT_LINKING:
            continue
        assert get_feature_state(feature_name, settings) is FeatureState.ENABLED
        assert can_use_feature("other", feature_name, settings) is True


def test_every_feature_can_be_forced_to_beta() -> None:
    settings = _settings()

    for feature_name in _ALL_FEATURES:
        assert get_feature_state(feature_name, settings) is FeatureState.BETA
        assert can_use_feature("other", feature_name, settings) is False


def test_hcr2_account_linking_defaults_to_beta() -> None:
    settings = Settings(
        _env_file=None,
        BETA_DISCORD_IDS="beta-user",
        ALLOWED_DISCORD_IDS="admin-user",
    )

    assert get_feature_state(Feature.HCR2_ACCOUNT_LINKING, settings) is FeatureState.BETA
    assert can_use_feature("other", Feature.HCR2_ACCOUNT_LINKING, settings) is False
    assert can_use_feature("beta-user", Feature.HCR2_ACCOUNT_LINKING, settings) is True
    assert can_use_feature("admin-user", Feature.HCR2_ACCOUNT_LINKING, settings) is True


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

    for feature_name in _ALL_FEATURES:
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