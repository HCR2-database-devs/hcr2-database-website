from typing import Any
from uuid import uuid4

from app.core.config import Settings
from app.core.progression_rules import (
    XP_BADGE_UNLOCKED,
    XP_HCR2_IDENTITY_VERIFIED,
    XP_MANUAL_ADJUSTMENT,
    XP_RECORD_MILESTONE_REACHED,
    XP_RECORD_VERIFIED,
    XP_SUBMISSION_ACCEPTED,
    xp_amount_for_event,
)
from app.repositories.progression import ProgressionError, ProgressionRepository

EVENT_REASONS = {
    XP_SUBMISSION_ACCEPTED: "Accepted record submission",
    XP_RECORD_VERIFIED: "Verified world record added",
    XP_RECORD_MILESTONE_REACHED: "World record milestone reached",
    XP_BADGE_UNLOCKED: "Badge unlocked",
    XP_HCR2_IDENTITY_VERIFIED: "HCR2 identity verified",
    "bug_report_confirmed": "Confirmed useful bug report",
    "helpful_report": "Helpful community report",
    "community_event_completed": "Community event completed",
    XP_MANUAL_ADJUSTMENT: "Manual XP adjustment",
}


class ProgressionService:
    def __init__(
        self,
        repository: ProgressionRepository,
        settings: Settings,
        notification_service: Any = None,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.notification_service = notification_service

    def emit(
        self,
        *,
        event_key: str,
        community_user_id: int,
        event_type: str,
        payload: dict[str, Any] | None = None,
        xp_amount: int | None = None,
    ) -> dict[str, Any]:
        """Event entry point for other services; failures must not break them."""
        try:
            return self.process_event(
                event_key=event_key,
                community_user_id=community_user_id,
                event_type=event_type,
                payload=payload or {},
                xp_amount=xp_amount,
            )
        except Exception:
            return {"ignored": True, "reason": "progression_error"}

    def process_event(
        self,
        *,
        event_key: str,
        community_user_id: int,
        event_type: str,
        payload: dict[str, Any] | None = None,
        xp_amount: int | None = None,
    ) -> dict[str, Any]:
        body = dict(payload or {})
        amount = (
            xp_amount
            if xp_amount is not None
            else xp_amount_for_event(self.settings, event_type, body)
        )
        result = self.repository.process_event(
            event_key=event_key,
            community_user_id=community_user_id,
            event_type=event_type,
            payload=body,
            xp_amount=int(amount),
            xp_reason=EVENT_REASONS.get(event_type, "Community contribution"),
            level_divisor=self.settings.xp_level_divisor,
        )
        if result.get("duplicate") or result.get("ignored"):
            return result
        for badge in result.get("awarded", []):
            self._notify(
                community_user_id,
                "badge_unlocked",
                f"Badge unlocked: {badge['badge_name']}",
            )
        for badge in result.get("revoked", []):
            self._notify(
                community_user_id,
                "badge_revoked",
                f"The {badge['badge_name']} badge was removed from your profile.",
            )
        before = result.get("level_before")
        after = result.get("level_after")
        if before is not None and after is not None and after > before:
            self._notify(
                community_user_id,
                "level_up",
                f"You reached community level {after}.",
            )
        return result

    def get_summary(self, community_user_id: int) -> dict[str, Any]:
        return self.repository.get_summary(community_user_id, self.settings.xp_level_divisor)

    def list_transactions(
        self,
        community_user_id: int,
        *,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        rows, total = self.repository.list_transactions(
            community_user_id,
            limit=limit,
            offset=offset,
        )
        return {
            "transactions": rows,
            "count": total,
            "limit": limit,
            "offset": offset,
        }

    def adjust_xp(
        self,
        *,
        community_user_id: int,
        amount: int,
        reason: str,
        actor: str,
    ) -> dict[str, Any]:
        if amount == 0:
            raise ProgressionError("XP adjustment cannot be zero.")
        return self.process_event(
            event_key=f"manual:{uuid4().hex}",
            community_user_id=community_user_id,
            event_type=XP_MANUAL_ADJUSTMENT,
            payload={"actor": actor, "reason": reason},
            xp_amount=amount,
        )

    def refresh(self, community_user_id: int) -> dict[str, Any]:
        changes = self.repository.refresh_badges(community_user_id)
        for badge in changes.get("awarded", []):
            self._notify(
                community_user_id,
                "badge_unlocked",
                f"Badge unlocked: {badge['badge_name']}",
            )
        for badge in changes.get("revoked", []):
            self._notify(
                community_user_id,
                "badge_revoked",
                f"The {badge['badge_name']} badge was removed from your profile.",
            )
        return changes

    def _notify(self, community_user_id: int, notification_type: str, message: str) -> None:
        if self.notification_service is None:
            return
        try:
            self.notification_service.notify(community_user_id, notification_type, message)
        except Exception:
            return
