"""Central configuration for Phase 5 badges and progression."""

from typing import Any

BADGE_TYPES = frozenset(
    {"achievement", "special_recognition", "team", "community"}
)
AWARD_METHODS = frozenset({"automatic", "manual"})
RARITIES = frozenset({"common", "uncommon", "rare", "epic", "legendary"})
REQUIREMENT_TYPES = frozenset(
    {
        "world_records_current_count",
        "world_records_ever_count",
        "approved_submissions_count",
        "hcr2_identity_verified",
        "membership_duration_days",
        "xp_total",
    }
)

XP_SUBMISSION_ACCEPTED = "submission_accepted"
XP_RECORD_VERIFIED = "record_verified"
XP_RECORD_MILESTONE_REACHED = "record_milestone_reached"
XP_BADGE_UNLOCKED = "badge_unlocked"
XP_BUG_REPORT_CONFIRMED = "bug_report_confirmed"
XP_HELPFUL_REPORT = "helpful_report"
XP_COMMUNITY_EVENT_COMPLETED = "community_event_completed"
XP_HCR2_IDENTITY_VERIFIED = "hcr2_identity_verified"
XP_MANUAL_ADJUSTMENT = "manual_xp_adjustment"

XP_EVENT_TYPES = frozenset(
    {
        XP_SUBMISSION_ACCEPTED,
        XP_RECORD_VERIFIED,
        XP_RECORD_MILESTONE_REACHED,
        XP_BADGE_UNLOCKED,
        XP_BUG_REPORT_CONFIRMED,
        XP_HELPFUL_REPORT,
        XP_COMMUNITY_EVENT_COMPLETED,
        XP_HCR2_IDENTITY_VERIFIED,
        XP_MANUAL_ADJUSTMENT,
    }
)


def xp_amount_for_event(settings: Any, event_type: str, payload: dict[str, Any]) -> int:
    """Resolve the configured XP reward for one event type."""
    if event_type == XP_SUBMISSION_ACCEPTED:
        return settings.xp_accepted_submission + (
            settings.xp_first_submission_bonus if payload.get("first_submission") else 0
        )
    if event_type == XP_RECORD_VERIFIED:
        return settings.xp_record_verified
    if event_type == XP_RECORD_MILESTONE_REACHED:
        return settings.xp_record_milestone_bonus
    if event_type == XP_BUG_REPORT_CONFIRMED:
        return settings.xp_bug_report_confirmed
    if event_type == XP_HELPFUL_REPORT:
        return settings.xp_helpful_report
    if event_type == XP_COMMUNITY_EVENT_COMPLETED:
        return settings.xp_community_event
    return 0


def level_summary(total_xp: int, divisor: int) -> dict[str, int | float]:
    """Simple level curve: thresholds are divisor * level²."""
    total_xp = max(0, int(total_xp))
    divisor = max(1, int(divisor))
    level = int((total_xp / divisor) ** 0.5) + 1
    current_level_xp = divisor * (level - 1) ** 2
    next_level_xp = divisor * level**2
    xp_to_next = max(0, next_level_xp - total_xp)
    span = max(1, next_level_xp - current_level_xp)
    progress = min(100.0, max(0.0, round((total_xp - current_level_xp) / span * 100, 2)))
    return {
        "total_xp": total_xp,
        "level": level,
        "current_level_xp": current_level_xp,
        "next_level_xp": next_level_xp,
        "xp_to_next": xp_to_next,
        "progress_percent": progress,
    }
