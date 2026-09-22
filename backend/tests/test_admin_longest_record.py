from __future__ import annotations

from typing import Any

import pytest

from app.schemas.admin import SetLongestRecordRequest
from app.services.admin_service import AdminNotFoundError, AdminService


class FakeCursor:
    def __init__(self) -> None:
        self.queries: list[str] = []
        self.row: dict[str, Any] | None = None
        self.rows: list[dict[str, Any]] = []

    def execute(self, sql: str, params: Any = None) -> None:
        self.queries.append(sql.split()[0].upper())
        self.last_sql = sql
        self.last_params = params

    def fetchone(self) -> dict[str, Any] | None:
        return self.row

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.cursor_obj = cursor

    def cursor(self) -> FakeCursor:
        return self.cursor_obj

    def __enter__(self) -> FakeConnection:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


@pytest.fixture
def fake_cursor(monkeypatch: pytest.MonkeyPatch) -> FakeCursor:
    cursor = FakeCursor()
    monkeypatch.setattr(
        "app.services.admin_service.open_connection",
        lambda config: FakeConnection(cursor),
    )
    return cursor


def test_set_longest_record_validates_current_record(
    fake_cursor: FakeCursor,
) -> None:
    fake_cursor.row = None
    service = AdminService()

    with pytest.raises(AdminNotFoundError):
        service.set_longest_record(SetLongestRecordRequest(record_id=123), "admin")


def test_set_longest_record_upserts_selected_record(fake_cursor: FakeCursor) -> None:
    fake_cursor.row = {"1": 1}
    service = AdminService()

    result = service.set_longest_record(SetLongestRecordRequest(record_id=42), "admin")

    insert = [sql for sql in fake_cursor.queries if sql == "INSERT"][0]
    assert insert == "INSERT"
    assert "longest_standing_record" in fake_cursor.last_sql
    assert result == {"success": True, "recordId": 42}


def test_get_longest_record_unset(fake_cursor: FakeCursor) -> None:
    fake_cursor.row = {"recordId": None, "setBy": "", "setAt": None, "distance": None}
    service = AdminService()

    assert service.get_longest_record() == {"set": False}


def test_get_longest_record_set(fake_cursor: FakeCursor) -> None:
    fake_cursor.row = {
        "recordId": 7,
        "setBy": "admin",
        "setAt": "2026-09-22T10:00:00",
        "distance": 15000,
        "mapName": "Countryside",
        "vehicleName": "Jeep",
        "playerName": "Bilbo",
    }
    service = AdminService()

    result = service.get_longest_record()

    assert result["set"] is True
    assert result["recordId"] == 7
    assert result["vehicleName"] == "Jeep"


def test_clear_longest_record_runs_update(fake_cursor: FakeCursor) -> None:
    service = AdminService()

    result = service.clear_longest_record("admin")

    assert fake_cursor.queries.count("UPDATE") == 1
    assert result == {"success": True}