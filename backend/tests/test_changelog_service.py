from typing import Any

import pytest

from app.schemas.admin import ChangelogPayload
from app.services.admin_service import AdminService, AdminServiceError
from app.services.changelog_service import ChangelogService, normalize_changelog_limit


class FakeChangelogRepository:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def list_changelog(self, limit: int) -> list[dict[str, Any]]:
        return self._rows[:limit]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, 50),
        ("50", 50),
        ("0", 50),
        ("-4", 50),
        ("501", 50),
        ("1000", 50),
        ("100", 100),
        ("not-a-number", 50),
        (5, 5),
    ],
)
def test_normalize_changelog_limit(raw: str | int | None, expected: int) -> None:
    assert normalize_changelog_limit(raw) == expected


def test_changelog_service_list_changelog() -> None:
    rows = [{"id": 1, "version": "0.2.0", "added": ["a"], "changed": [], "fixed": []}]
    service = ChangelogService(FakeChangelogRepository(rows))

    assert service.list_changelog(10) == {"changelog": rows}


def test_changelog_service_limit_is_applied() -> None:
    rows = [{"id": i, "version": f"v{i}"} for i in range(5)]
    service = ChangelogService(FakeChangelogRepository(rows))

    assert len(service.list_changelog("2")["changelog"]) == 2


def test_clean_bullets_strips_tags_and_empties() -> None:
    service = AdminService()

    assert service._clean_bullets(["<b>New map</b>", "  vehicle  ", "", "<i></i>"]) == [
        "New map",
        "vehicle",
    ]


def test_clean_bullets_rejects_too_many_entries() -> None:
    service = AdminService()
    with pytest.raises(AdminServiceError):
        service._clean_bullets([f"entry {i}" for i in range(51)])


def test_clean_bullets_rejects_long_entry() -> None:
    service = AdminService()
    with pytest.raises(AdminServiceError):
        service._clean_bullets(["x" * 301])


def test_post_changelog_requires_version() -> None:
    service = AdminService()
    with pytest.raises(AdminServiceError):
        service.post_changelog(
            ChangelogPayload(version="  ", added=["New map"]),
            "Dev Admin",
            "Dev Admin",
        )


def test_post_changelog_requires_at_least_one_entry() -> None:
    service = AdminService()
    with pytest.raises(AdminServiceError):
        service.post_changelog(
            ChangelogPayload(version="0.1.0", added=[], changed=[], fixed=[]),
            "Dev Admin",
            "Dev Admin",
        )