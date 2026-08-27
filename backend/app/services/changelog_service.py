from dataclasses import dataclass
from typing import Any

from app.repositories.changelog import ChangelogRepository


def normalize_changelog_limit(raw_limit: str | int | None) -> int:
    if raw_limit is None:
        return 50
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        limit = 0
    if limit <= 0 or limit > 500:
        return 50
    return limit


@dataclass(frozen=True, slots=True)
class ChangelogService:
    repository: ChangelogRepository

    def list_changelog(self, raw_limit: str | int | None = None) -> dict[str, list[dict[str, Any]]]:
        return {"changelog": self.repository.list_changelog(normalize_changelog_limit(raw_limit))}