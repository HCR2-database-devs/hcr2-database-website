from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NewsItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    title: str
    content: str
    author: str | None = None
    created_at: datetime | str


class NewsList(BaseModel):
    news: list[NewsItem]
