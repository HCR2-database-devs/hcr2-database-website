import re
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError

from app.core.config import REPO_ROOT, Settings
from app.core.progression_rules import AWARD_METHODS, BADGE_TYPES, RARITIES, REQUIREMENT_TYPES
from app.repositories.badge import BadgeError, BadgeRepository
from app.repositories.progression import ProgressionRepository

IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
MAX_ICON_BYTES = 2_000_000
BADGE_ICON_DIR = REPO_ROOT / "frontend" / "public" / "img" / "badges"


def _clean(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    return value.strip()[:limit]


class BadgeService:
    def __init__(
        self,
        repository: BadgeRepository,
        settings: Settings,
        progression_repository: ProgressionRepository | None = None,
        notification_service: Any = None,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.progression_repository = progression_repository
        self.notification_service = notification_service

    def _maybe_refresh_time_based(self, community_user_id: int | None) -> None:
        if community_user_id is None or self.progression_repository is None:
            return
        try:
            if self.progression_repository.claim_evaluation(
                community_user_id,
                "membership_duration_days",
            ):
                self.progression_repository.refresh_badges(community_user_id)
        except Exception:
            return

    def _notify(self, community_user_id: int, notification_type: str, message: str) -> None:
        if self.notification_service is None:
            return
        try:
            self.notification_service.notify(community_user_id, notification_type, message)
        except Exception:
            return

    def get_catalog(
        self,
        *,
        community_user_id: int | None = None,
        category: str | None = None,
        badge_type: str | None = None,
        scope: str = "all",
    ) -> dict[str, Any]:
        self._maybe_refresh_time_based(community_user_id)
        definitions = self.repository.list_definitions(
            category=category,
            badge_type=badge_type,
            include_admin=False,
        )
        owned: dict[int, dict[str, Any]] = {}
        progress: dict[int, dict[str, Any]] = {}
        if community_user_id is not None:
            owned = {
                int(row["badge_id"]): row
                for row in self.repository.list_user_badges(community_user_id)
            }
            progress = {
                int(row["badge_id"]): row
                for row in self.repository.list_progress(community_user_id)
            }
        items: list[dict[str, Any]] = []
        for definition in definitions:
            badge_id = int(definition["id"])
            user_badge = owned.get(badge_id)
            unlocked = user_badge is not None
            if scope == "owned" and not unlocked:
                continue
            if scope == "locked" and unlocked:
                continue
            progress_row = progress.get(badge_id)
            progress_value = int(progress_row["progress_value"]) if progress_row else 0
            target_value = int(progress_row["target_value"]) if progress_row else 1
            requirement_type = definition.get("requirement_type")
            can_earn = (
                definition.get("award_method") == "automatic" and requirement_type is not None
            )
            hidden = bool(definition.get("hidden_until_unlocked")) and not unlocked
            item = {
                "id": badge_id,
                "identifier": definition["identifier"],
                "category": {
                    "id": definition["category_id"],
                    "identifier": definition["category_identifier"],
                    "name": definition["category_name"],
                },
                "name": "Hidden badge" if hidden else definition["name"],
                "description": (
                    "This badge is revealed once it has been unlocked."
                    if hidden
                    else definition["description"]
                ),
                "icon_url": None if hidden else definition["icon_path"],
                "badge_type": definition["badge_type"],
                "award_method": definition["award_method"],
                "rarity": definition["rarity"],
                "hidden_until_unlocked": bool(definition["hidden_until_unlocked"]),
                "featureable": bool(definition["featureable"]),
                "revocable": bool(definition["revocable"]),
                "permanent": bool(definition["permanent"]),
                "sort_order": definition["sort_order"],
                "unlocked": unlocked,
                "awarded_at": user_badge["awarded_at"] if user_badge else None,
                "public_reason": user_badge["public_reason"] if user_badge else None,
                "can_earn": can_earn,
                "requirement_type": None if hidden else requirement_type,
                "progress": (
                    {
                        "current": progress_value,
                        "target": target_value,
                        "percent": min(100, round(progress_value / target_value * 100)),
                    }
                    if can_earn and not hidden
                    else None
                ),
            }
            items.append(item)
        return {
            "badges": items,
            "count": len(items),
            "categories": self.repository.list_categories(),
        }

    def get_detail(
        self,
        identifier: str,
        *,
        community_user_id: int | None = None,
    ) -> dict[str, Any] | None:
        self._maybe_refresh_time_based(community_user_id)
        definition = self.repository.get_definition_by_identifier(identifier)
        if definition is None or not definition["enabled"] or definition["archived_at"]:
            return None
        catalog = self.get_catalog(community_user_id=community_user_id)
        for item in catalog["badges"]:
            if item["identifier"] == identifier:
                return item
        return None

    def get_profile_badges(self, community_user_id: int) -> dict[str, Any]:
        self._maybe_refresh_time_based(community_user_id)
        badges = self.repository.list_user_badges(community_user_id)
        featured = self.repository.list_featured(community_user_id)
        return {
            "badges": badges,
            "featured": featured,
            "count": len(badges),
        }

    def set_featured(
        self,
        community_user_id: int,
        badge_ids: list[int],
    ) -> list[dict[str, Any]]:
        if len(badge_ids) > 5:
            raise BadgeError("You can feature at most 5 badges.", 400)
        if len(set(badge_ids)) != len(badge_ids):
            raise BadgeError("A badge can only be featured once.", 400)
        validated: list[int] = []
        for badge_id in badge_ids:
            row = self.repository.get_user_badge_by_badge(community_user_id, badge_id)
            if row is None or not row["active"] or not row["featureable"]:
                raise BadgeError("You can only feature badges you own.", 400)
            validated.append(int(row["id"]))
        return self.repository.replace_featured(community_user_id, validated)

    def award_manual(
        self,
        *,
        badge_identifier: str | None,
        badge_id: int | None,
        user_ids: list[int],
        actor: str,
        reason: str,
        public_reason: str | None = None,
    ) -> dict[str, Any]:
        definition = (
            self.repository.get_definition_by_identifier(badge_identifier)
            if badge_identifier
            else self.repository.get_definition(badge_id or 0)
        )
        if definition is None:
            raise BadgeError("Badge not found.", 404)
        if not definition["enabled"] or definition["archived_at"] is not None:
            raise BadgeError("Badge is not available.", 409)
        if not user_ids:
            raise BadgeError("Select at least one user.", 400)
        clean_reason = _clean(reason, 1000) or ""
        clean_public = _clean(public_reason, 1000)
        results: list[dict[str, Any]] = []
        for user_id in dict.fromkeys(user_ids):
            badge, created = self.repository.award_badge(
                community_user_id=user_id,
                badge_id=int(definition["id"]),
                source="manual",
                actor=actor,
                reason=clean_reason or None,
                public_reason=clean_public or None,
            )
            if created and badge is not None:
                self._notify(
                    user_id,
                    "badge_awarded",
                    f"You were awarded the {definition['name']} badge.",
                )
            results.append(
                {
                    "community_user_id": user_id,
                    "badge_id": definition["id"],
                    "awarded": created,
                }
            )
        return {
            "badge": definition,
            "results": results,
            "awarded_count": sum(1 for result in results if result["awarded"]),
        }

    def revoke(
        self,
        *,
        user_badge_id: int,
        actor: str,
        reason: str,
    ) -> dict[str, Any]:
        clean_reason = _clean(reason, 1000) or "Badge revoked by an administrator."
        row = self.repository.revoke_badge(
            user_badge_id=user_badge_id,
            actor=actor,
            reason=clean_reason,
        )
        if row is None:
            raise BadgeError("Badge award not found.", 404)
        self._notify(
            int(row["community_user_id"]),
            "badge_revoked",
            f"The {row['badge_name']} badge was removed from your profile.",
        )
        return row

    def list_history(
        self,
        *,
        community_user_id: int | None,
        badge_id: int | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        rows, total = self.repository.list_history(
            community_user_id=community_user_id,
            badge_id=badge_id,
            limit=limit,
            offset=offset,
        )
        return {
            "history": rows,
            "count": total,
            "limit": limit,
            "offset": offset,
        }

    def create_definition(self, payload: Any) -> dict[str, Any]:
        values = self._definition_values(payload, creating=True)
        return self.repository.create_definition(values)

    def update_definition(self, badge_id: int, payload: Any) -> dict[str, Any] | None:
        changes = self._definition_values(payload, creating=False, badge_id=badge_id)
        if "icon_path" in changes and changes["icon_path"] is None:
            changes.pop("icon_path")
        return self.repository.update_definition(badge_id, changes)

    def archive_definition(self, badge_id: int) -> dict[str, Any] | None:
        return self.repository.archive_definition(badge_id)

    def create_category(self, payload: Any) -> dict[str, Any]:
        if not IDENTIFIER_PATTERN.fullmatch(payload.identifier):
            raise BadgeError("Invalid category identifier.", 400)
        return self.repository.create_category(payload)

    def update_category(self, category_id: int, payload: Any) -> dict[str, Any] | None:
        return self.repository.update_category(category_id, payload)

    def upload_icon(
        self,
        *,
        identifier: str,
        filename: str | None,
        content_type: str | None,
        content: bytes | None,
    ) -> dict[str, Any]:
        definition = self.repository.get_definition_by_identifier(identifier)
        if definition is None:
            raise BadgeError("Badge not found.", 404)
        if not content:
            raise BadgeError("A WebP icon is required.", 400)
        if len(content) > MAX_ICON_BYTES:
            raise BadgeError("Icon file is too large (max 2 MB).", 413)
        if filename and not filename.lower().endswith(".webp"):
            raise BadgeError("Only WebP icon uploads are supported.", 415)
        if content_type and content_type not in {
            "image/webp",
            "application/octet-stream",
            "binary/octet-stream",
        }:
            raise BadgeError("Only WebP icon uploads are supported.", 415)
        try:
            with Image.open(BytesIO(content)) as image:
                if image.format != "WEBP":
                    raise BadgeError("The uploaded icon does not look like a WebP image.", 415)
                image.verify()
        except BadgeError:
            raise
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            raise BadgeError("The uploaded icon is not a valid WebP image.", 415) from None
        BADGE_ICON_DIR.mkdir(parents=True, exist_ok=True)
        target = BADGE_ICON_DIR / f"{definition['identifier']}.webp"
        target.write_bytes(content)
        icon_path = f"/img/badges/{target.name}"
        updated = self.repository.update_definition(
            int(definition["id"]),
            {"icon_path": icon_path},
        )
        return {"icon_path": icon_path, "badge": updated}

    def _definition_values(
        self,
        payload: Any,
        *,
        creating: bool,
        badge_id: int | None = None,
    ) -> dict[str, Any]:
        raw = payload.model_dump(exclude_unset=True)
        existing = (
            self.repository.get_definition(badge_id)
            if not creating and badge_id is not None
            else None
        )
        values: dict[str, Any] = {}
        if "identifier" in raw and raw["identifier"] is not None:
            identifier = str(raw["identifier"]).strip()
            if not IDENTIFIER_PATTERN.fullmatch(identifier):
                raise BadgeError("Invalid badge identifier.", 400)
            values["identifier"] = identifier
        elif creating:
            raise BadgeError("Identifier is required.", 400)

        category_identifier = raw.pop("category_identifier", None)
        category_id = raw.pop("category_id", None)
        if category_identifier:
            categories = self.repository.list_categories(include_disabled=True)
            match = next(
                (row for row in categories if row["identifier"] == category_identifier),
                None,
            )
            if match is None:
                raise BadgeError("Unknown badge category.", 400)
            values["category_id"] = int(match["id"])
        elif category_id:
            values["category_id"] = int(category_id)
        elif creating:
            raise BadgeError("Category is required.", 400)

        if "badge_type" in raw and raw["badge_type"] is not None:
            if raw["badge_type"] not in BADGE_TYPES:
                raise BadgeError("Unknown badge type.", 400)
            values["badge_type"] = raw["badge_type"]
        elif creating:
            raise BadgeError("Badge type is required.", 400)

        if "award_method" in raw and raw["award_method"] is not None:
            if raw["award_method"] not in AWARD_METHODS:
                raise BadgeError("Unknown award method.", 400)
            values["award_method"] = raw["award_method"]
        if "rarity" in raw and raw["rarity"] is not None:
            if raw["rarity"] not in RARITIES:
                raise BadgeError("Unknown rarity.", 400)
            values["rarity"] = raw["rarity"]
        if "requirement_type" in raw and raw["requirement_type"] is not None:
            if raw["requirement_type"] not in REQUIREMENT_TYPES:
                raise BadgeError("Unknown requirement type.", 400)
            values["requirement_type"] = raw["requirement_type"]
        elif creating:
            values["requirement_type"] = None
        if "requirement_config" in raw and raw["requirement_config"] is not None:
            if not isinstance(raw["requirement_config"], dict):
                raise BadgeError("Requirement config must be an object.", 400)
            values["requirement_config"] = raw["requirement_config"]

        for key in (
            "name",
            "description",
            "enabled",
            "hidden_until_unlocked",
            "revocable",
            "featureable",
            "permanent",
            "expires_at",
            "discord_role_id",
            "discord_sync_enabled",
            "sort_order",
        ):
            if key in raw and raw[key] is not None:
                values[key] = raw[key]
        if "icon_path" in raw and raw["icon_path"] is not None:
            icon_path = str(raw["icon_path"]).strip()
            if icon_path and not icon_path.startswith("/img/"):
                raise BadgeError("Icon path must point under /img/.", 400)
            values["icon_path"] = icon_path
        elif creating:
            identifier = values.get("identifier", "")
            values["icon_path"] = f"/img/badges/{identifier}.webp"

        method = values.get(
            "award_method",
            "manual" if creating else (existing or {}).get("award_method"),
        )
        requirement = values.get(
            "requirement_type",
            (existing or {}).get("requirement_type"),
        )
        if method == "automatic" and not requirement:
            raise BadgeError("Automatic badges need a requirement type.", 400)
        if creating:
            values.setdefault("award_method", "manual")
            values.setdefault("rarity", "common")
            values.setdefault("requirement_config", {})
            values.setdefault("enabled", True)
            values.setdefault("hidden_until_unlocked", False)
            values.setdefault("revocable", True)
            values.setdefault("featureable", True)
            values.setdefault("permanent", True)
            values.setdefault("discord_sync_enabled", False)
            values.setdefault("sort_order", 0)
            values.setdefault("description", "")
        return values
