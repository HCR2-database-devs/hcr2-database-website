from typing import Any

from app.core.config import Settings
from app.repositories.badge import BadgeError
from app.services.badge_service import BadgeService
from app.services.progression_service import ProgressionService


class _BadgeRepository:
    def get_definition(self, badge_id: int) -> dict[str, Any] | None:
        return {
            "id": badge_id,
            "identifier": "first_submission",
            "award_method": "automatic",
            "requirement_type": "approved_submissions_count",
        }

    def list_categories(self, include_disabled: bool = False) -> list[dict[str, Any]]:
        return [{"id": 1, "identifier": "hcr2"}]

    def update_definition(self, badge_id: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        return {"id": badge_id, **changes}


class _Payload:
    def __init__(self, **values: Any) -> None:
        self._values = values

    def model_dump(self, *, exclude_unset: bool = False) -> dict[str, Any]:
        assert exclude_unset
        return dict(self._values)


class _ProgressionRepository:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    def process_event(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return self.result


class _Notifications:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str, str]] = []

    def notify(self, user_id: int, notification_type: str, message: str) -> None:
        self.messages.append((user_id, notification_type, message))


def test_update_automatic_badge_keeps_existing_requirement() -> None:
    service = BadgeService(_BadgeRepository(), Settings(_env_file=None))

    values = service.update_definition(
        1,
        _Payload(description="Updated without changing the requirement."),
    )

    assert values is not None
    assert values["description"] == "Updated without changing the requirement."
    assert "requirement_type" not in values


def test_create_automatic_badge_requires_requirement() -> None:
    service = BadgeService(_BadgeRepository(), Settings(_env_file=None))

    try:
        service.create_definition(
            _Payload(
                identifier="manual_only",
                category_identifier="hcr2",
                name="Manual only",
                badge_type="achievement",
                award_method="automatic",
            )
        )
    except BadgeError as exc:
        assert "requirement type" in exc.message
    else:
        raise AssertionError("Expected BadgeError")


def test_progression_service_notifies_for_badge_and_level_changes() -> None:
    repository = _ProgressionRepository(
        {
            "duplicate": False,
            "awarded": [{"badge_name": "First Submission"}],
            "revoked": [],
            "level_before": 1,
            "level_after": 2,
        }
    )
    notifications = _Notifications()
    service = ProgressionService(
        repository,
        Settings(_env_file=None),
        notification_service=notifications,
    )

    result = service.process_event(
        event_key="submission:1",
        community_user_id=7,
        event_type="submission_accepted",
    )

    assert result["awarded"][0]["badge_name"] == "First Submission"
    assert [item[1] for item in notifications.messages] == ["badge_unlocked", "level_up"]
    assert repository.calls[0]["xp_amount"] == 25


def test_progression_service_ignores_duplicate_events() -> None:
    repository = _ProgressionRepository({"duplicate": True})
    notifications = _Notifications()
    service = ProgressionService(
        repository,
        Settings(_env_file=None),
        notification_service=notifications,
    )

    result = service.emit(
        event_key="submission:1",
        community_user_id=7,
        event_type="submission_accepted",
    )

    assert result == {"duplicate": True}
    assert notifications.messages == []
