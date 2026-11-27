from types import SimpleNamespace

from app.core.progression_rules import (
    XP_RECORD_MILESTONE_REACHED,
    XP_SUBMISSION_ACCEPTED,
    level_summary,
    xp_amount_for_event,
)


def test_xp_amount_for_event_uses_config_and_payload() -> None:
    settings = SimpleNamespace(
        xp_accepted_submission=25,
        xp_first_submission_bonus=25,
        xp_record_milestone_bonus=25,
    )

    assert xp_amount_for_event(settings, XP_SUBMISSION_ACCEPTED, {}) == 25
    assert (
        xp_amount_for_event(
            settings,
            XP_SUBMISSION_ACCEPTED,
            {"first_submission": True},
        )
        == 50
    )
    assert xp_amount_for_event(settings, XP_RECORD_MILESTONE_REACHED, {}) == 25


def test_level_summary_uses_squared_thresholds() -> None:
    summary = level_summary(99, 100)
    assert summary["level"] == 1
    assert summary["next_level_xp"] == 100
    assert summary["xp_to_next"] == 1

    summary = level_summary(100, 100)
    assert summary["level"] == 2
    assert summary["current_level_xp"] == 100
    assert summary["next_level_xp"] == 400
    assert summary["xp_to_next"] == 300
