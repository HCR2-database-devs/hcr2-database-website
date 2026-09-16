from dataclasses import dataclass
from typing import Any

from app.core.username_rules import (
    UsernameModerationError,
    UsernameValidationError,
    username_key,
    validate_username,
)
from app.repositories.community_moderation import (
    REPORT_CATEGORIES,
    CommunityModerationRepository,
)
from app.repositories.community_user import CommunityUserRepository, UsernameConflictError
from app.services.activity_log_service import ActivityLogService
from app.services.community_account_service import (
    COUNTRY_CODES,
    MAX_BIO_LENGTH,
    CommunityProfileError,
)
from app.services.community_notification_service import CommunityNotificationService
from app.services.hcaptcha import verify_hcaptcha

VALID_REPORT_STATUSES = ("open", "resolved", "rejected")


@dataclass(frozen=True, slots=True)
class CommunityModerationService:
    moderation_repository: CommunityModerationRepository
    community_repository: CommunityUserRepository
    activity_log: ActivityLogService | None = None
    hcaptcha_secret_key: str | None = None
    notification_service: CommunityNotificationService | None = None

    def _log(
        self,
        admin_username: str,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        entity_name: str | None = None,
        note: str | None = None,
    ) -> None:
        if self.activity_log:
            self.activity_log.log_action(
                admin_username,
                action,
                entity_type,
                entity_id,
                entity_name,
                note=note,
            )

    def _notify(
        self,
        community_user_id: int,
        notification_type: str,
        message: str,
    ) -> None:
        if self.notification_service:
            self.notification_service.notify(
                community_user_id,
                notification_type,
                message,
            )

    @staticmethod
    def _reason_suffix(note: str | None) -> str:
        return f" Reason: {note}" if note else ""

    @staticmethod
    def _changed_labels(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
        """Return human-readable labels for profile fields that differ."""
        labels: list[str] = []

        def field(key: str, label: str) -> None:
            if old.get(key) != new.get(key):
                labels.append(label)

        field("bio", "bio")
        field("country", "country")
        field("favorite_vehicle_id", "favorite vehicle")
        field("favorite_map_id", "favorite map")
        field("profile_public", "profile visibility")
        field("show_country", "country visibility")
        field("show_bio", "bio visibility")
        field("show_favorite_vehicle", "favorite vehicle visibility")
        field("show_favorite_map", "favorite map visibility")
        field("show_discord_username", "Discord username visibility")
        field("show_discord_avatar", "Discord avatar visibility")
        return labels

    def _validate_fields(
        self,
        *,
        bio: str,
        country: str | None,
        favorite_vehicle_id: int | None,
        favorite_map_id: int | None,
    ) -> tuple[str, str | None, int | None, int | None]:
        bio = bio or ""
        if len(bio) > MAX_BIO_LENGTH:
            raise CommunityProfileError(f"Bio must be at most {MAX_BIO_LENGTH} characters.")
        if country is not None:
            country = country.strip().lower()
            if country and country not in COUNTRY_CODES:
                raise CommunityProfileError("Unknown country code.")
            if not country:
                country = None
        vehicle_name, map_name = self.community_repository.favorite_names(
            favorite_vehicle_id,
            favorite_map_id,
        )
        if favorite_vehicle_id is not None and vehicle_name is None:
            raise CommunityProfileError("Unknown favorite vehicle.")
        if favorite_map_id is not None and map_name is None:
            raise CommunityProfileError("Unknown favorite map.")
        return bio, country, favorite_vehicle_id, favorite_map_id

    def list_profiles(
        self,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        if search is not None:
            search = search.strip()[:MAX_BIO_LENGTH] or None
        profiles, total = self.moderation_repository.list_profiles(
            search=search,
            limit=limit,
            offset=offset,
        )
        return {
            "profiles": profiles,
            "count": total,
            "limit": limit,
            "offset": offset,
            "search": search,
        }

    def get_profile(self, user_id: int) -> dict[str, Any] | None:
        return self.moderation_repository.get_profile(user_id)

    def update_profile(
        self,
        user_id: int,
        payload: Any,
        admin_username: str = "",
        note: str | None = None,
    ) -> dict[str, Any] | None:
        bio, country, vehicle_id, map_id = self._validate_fields(
            bio=payload.bio or "",
            country=payload.country,
            favorite_vehicle_id=payload.favorite_vehicle_id,
            favorite_map_id=payload.favorite_map_id,
        )
        old = self.get_profile(user_id)
        new_fields = {
            "bio": bio,
            "country": country,
            "favorite_vehicle_id": vehicle_id,
            "favorite_map_id": map_id,
            "profile_public": bool(payload.profile_public),
            "show_country": bool(payload.show_country),
            "show_bio": bool(payload.show_bio),
            "show_favorite_vehicle": bool(payload.show_favorite_vehicle),
            "show_favorite_map": bool(payload.show_favorite_map),
            "show_discord_username": bool(payload.show_discord_username),
            "show_discord_avatar": bool(payload.show_discord_avatar),
        }
        updated = self.moderation_repository.admin_update_profile(
            user_id,
            **new_fields,
        )
        if updated is not None:
            self._log(
                admin_username,
                "updated",
                "community_user",
                user_id,
                updated.get("discord_username"),
                note=note,
            )
            changed = self._changed_labels(old or {}, new_fields)
            if changed:
                message = (
                    "An administrator updated your community profile: "
                    + ", ".join(changed)
                    + "."
                    + self._reason_suffix(note)
                )
            else:
                message = (
                    "An administrator updated your community profile."
                    + self._reason_suffix(note)
                )
            self._notify(user_id, "profile_updated", message)
        return updated

    def reset_profile(
        self,
        user_id: int,
        admin_username: str,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        updated = self.moderation_repository.admin_clear_customization(user_id)
        if updated is not None:
            self._log(
                admin_username,
                "reset",
                "community_user",
                user_id,
                updated.get("discord_username"),
                note=note,
            )
            self._notify(
                user_id,
                "profile_reset",
                "An administrator reset your community profile."
                + self._reason_suffix(note),
            )
        return updated

    def set_username(
        self,
        user_id: int,
        raw_username: str,
        admin_username: str,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        try:
            username = validate_username(raw_username)
        except (UsernameValidationError, UsernameModerationError) as exc:
            raise CommunityProfileError(exc.message) from None
        try:
            updated = self.moderation_repository.admin_set_username(
                user_id,
                username,
                username_key(username),
                admin_username,
            )
        except UsernameConflictError:
            raise CommunityProfileError(
                "This username isn't available. Please choose another one.",
                409,
            ) from None
        if updated is not None:
            self._log(
                admin_username,
                "username_set",
                "community_user",
                user_id,
                updated.get("discord_username"),
                note=note,
            )
            self._notify(
                user_id,
                "username_set",
                f'An administrator set your community username to "{username}".'
                + self._reason_suffix(note),
            )
        return updated

    def reset_username(
        self,
        user_id: int,
        admin_username: str,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        updated = self.moderation_repository.admin_reset_username(user_id, admin_username)
        if updated is not None:
            self._log(
                admin_username,
                "username_reset",
                "community_user",
                user_id,
                updated.get("discord_username"),
                note=note,
            )
            self._notify(
                user_id,
                "username_reset",
                "An administrator removed your community username."
                + self._reason_suffix(note),
            )
        return updated

    def get_username_history(self, user_id: int) -> list[dict[str, Any]]:
        return self.moderation_repository.list_username_history(user_id)

    def set_disabled(
        self,
        user_id: int,
        disabled: bool,
        admin_username: str,
        note: str | None = None,
    ) -> dict[str, Any] | None:
        updated = self.moderation_repository.set_admin_disabled(user_id, disabled)
        if updated is not None:
            self._log(
                admin_username,
                "enabled" if not disabled else "disabled",
                "community_user",
                user_id,
                updated.get("discord_username"),
                note=note,
            )
            if disabled:
                self._notify(
                    user_id,
                    "profile_disabled",
                    "Your community profile has been disabled."
                    + self._reason_suffix(note),
                )
            else:
                self._notify(
                    user_id,
                    "profile_enabled",
                    "Your community profile has been enabled."
                    + self._reason_suffix(note),
                )
        return updated

    def create_report(
        self,
        target_id: int,
        reporter_id: int,
        payload: Any,
    ) -> dict[str, Any]:
        if reporter_id == target_id:
            raise CommunityProfileError("You cannot report your own profile.")
        category = (payload.category or "").strip().lower()
        if category not in REPORT_CATEGORIES:
            raise CommunityProfileError("Unknown report category.")
        reason = (payload.reason or "").strip()
        if len(reason) > MAX_BIO_LENGTH:
            raise CommunityProfileError(f"Reason must be at most {MAX_BIO_LENGTH} characters.")
        if not self._verify_hcaptcha(str(getattr(payload, "h_captcha_response", "") or "")):
            raise CommunityProfileError(
                "hCaptcha verification failed. Please try again.",
                400,
            )
        created = self.moderation_repository.create_report(
            target_id,
            reporter_id,
            category,
            reason,
        )
        if created is None:
            raise CommunityProfileError(
                "You have already reported this profile.",
                status_code=409,
            )
        return created

    def list_reports(
        self,
        *,
        status: str | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        if status is not None and status not in VALID_REPORT_STATUSES:
            status = None
        reports, total = self.moderation_repository.list_reports(
            status=status,
            limit=limit,
            offset=offset,
        )
        return {
            "reports": reports,
            "count": total,
            "limit": limit,
            "offset": offset,
            "status": status,
        }

    def resolve_report(
        self,
        report_id: int,
        resolved: bool,
        admin_username: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        target_status = "resolved" if resolved else "rejected"
        updated = self.moderation_repository.resolve_report(
            report_id,
            target_status,
            admin_username,
            note,
        )
        if updated is None:
            raise CommunityProfileError(
                "Report is not open or does not exist.",
                status_code=404,
            )
        self._log(
            admin_username,
            "report_resolved" if resolved else "report_rejected",
            "community_profile_report",
            report_id,
            None,
            note=note,
        )
        return updated

    def _verify_hcaptcha(self, token: str) -> bool:
        return verify_hcaptcha(token, self.hcaptcha_secret_key)