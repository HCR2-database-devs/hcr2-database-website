from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ProgressionPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class BadgeDefinitionPayload(ProgressionPayload):
    identifier: str | None = Field(
        default=None,
        min_length=2,
        max_length=64,
        validation_alias=AliasChoices("identifier"),
    )
    category_identifier: str | None = Field(
        default=None,
        validation_alias=AliasChoices("categoryIdentifier", "category_identifier"),
    )
    category_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("categoryId", "category_id"),
    )
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    icon_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices("iconPath", "icon_path"),
    )
    badge_type: str | None = Field(
        default=None,
        validation_alias=AliasChoices("badgeType", "badge_type"),
    )
    award_method: str | None = Field(
        default=None,
        validation_alias=AliasChoices("awardMethod", "award_method"),
    )
    rarity: str | None = Field(default=None, max_length=40)
    requirement_type: str | None = Field(
        default=None,
        validation_alias=AliasChoices("requirementType", "requirement_type"),
    )
    requirement_config: dict[str, Any] | None = Field(
        default=None,
        validation_alias=AliasChoices("requirementConfig", "requirement_config"),
    )
    enabled: bool | None = None
    hidden_until_unlocked: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("hiddenUntilUnlocked", "hidden_until_unlocked"),
    )
    revocable: bool | None = None
    featureable: bool | None = None
    permanent: bool | None = None
    expires_at: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("expiresAt", "expires_at"),
    )
    discord_role_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("discordRoleId", "discord_role_id"),
    )
    discord_sync_enabled: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("discordSyncEnabled", "discord_sync_enabled"),
    )
    sort_order: int | None = Field(
        default=None,
        validation_alias=AliasChoices("sortOrder", "sort_order"),
    )


class BadgeDefinitionCreate(BadgeDefinitionPayload):
    identifier: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    badge_type: str = Field(min_length=2, max_length=40)


class BadgeDefinitionUpdate(BadgeDefinitionPayload):
    pass


class BadgeCategoryCreate(ProgressionPayload):
    identifier: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    sort_order: int = Field(default=0, validation_alias=AliasChoices("sortOrder", "sort_order"))


class BadgeCategoryUpdate(ProgressionPayload):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    sort_order: int | None = Field(
        default=None,
        validation_alias=AliasChoices("sortOrder", "sort_order"),
    )
    enabled: bool | None = None


class FeaturedBadgesUpdate(ProgressionPayload):
    badge_ids: list[int] = Field(
        default_factory=list,
        max_length=5,
        validation_alias=AliasChoices("badgeIds", "badge_ids"),
    )


class BadgeAwardRequest(ProgressionPayload):
    badge_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("badgeId", "badge_id"),
    )
    badge_identifier: str | None = Field(
        default=None,
        validation_alias=AliasChoices("badgeIdentifier", "badge_identifier"),
    )
    user_ids: list[int] = Field(
        default_factory=list,
        max_length=100,
        validation_alias=AliasChoices("userIds", "user_ids"),
    )
    reason: str = Field(default="", max_length=1000)
    public_reason: str | None = Field(
        default=None,
        validation_alias=AliasChoices("publicReason", "public_reason"),
    )


class BadgeRevokeRequest(ProgressionPayload):
    reason: str = Field(default="", max_length=1000)


class XpAdjustmentRequest(ProgressionPayload):
    amount: int = Field(..., ge=-100000, le=100000)
    reason: str = Field(..., min_length=1, max_length=1000)
