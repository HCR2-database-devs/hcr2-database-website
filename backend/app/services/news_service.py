from dataclasses import dataclass
from typing import Any

from app.repositories.news import NewsRepository


def normalize_news_limit(raw_limit: str | int | None) -> int:
    if raw_limit is None:
        return 10
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        limit = 0
    if limit <= 0 or limit > 100:
        return 10
    return limit


@dataclass(frozen=True, slots=True)
class NewsService:
    repository: NewsRepository

    def list_news(self, raw_limit: str | int | None = None) -> dict[str, list[dict[str, Any]]]:
        return {"news": self.repository.list_news(normalize_news_limit(raw_limit))}
