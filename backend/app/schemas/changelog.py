from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChangelogItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    version: str
    title: str | None = None
    added: list[str] = []
    changed: list[str] = []
    fixed: list[str] = []
    author: str | None = None
    created_at: datetime | str


class ChangelogList(BaseModel):
    changelog: list[ChangelogItem]