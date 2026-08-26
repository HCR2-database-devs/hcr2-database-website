from pydantic import BaseModel


class ActivityLogEntry(BaseModel):
    id: int
    admin_username: str
    action: str
    entity_type: str
    entity_id: int | None = None
    entity_name: str | None = None
    created_at: str


class ActivityLogFilter(BaseModel):
    admin_username: str | None = None
    action: str | None = None
    entity_type: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    limit: int = 50
    offset: int = 0


class ActivityLogListResponse(BaseModel):
    entries: list[ActivityLogEntry]
    total: int
