from typing import Any

from app.repositories.community_user import PostgresCommunityUserRepository


class _Cursor:
    def __init__(self) -> None:
        self.query = ""
        self.params: dict[str, Any] = {}

    def __enter__(self) -> "_Cursor":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def execute(self, query: str, params: dict[str, Any] | None = None) -> None:
        self.query = " ".join(query.split())
        self.params = params or {}

    def fetchall(self) -> list[dict[str, Any]]:
        return []


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> "_Connection":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def cursor(self) -> _Cursor:
        return self._cursor


def test_world_record_query_marks_records_beaten_by_another_player(
    monkeypatch: Any,
) -> None:
    cursor = _Cursor()
    connection = _Connection(cursor)
    monkeypatch.setattr(
        "app.repositories.community_user.open_connection",
        lambda *_args, **_kwargs: connection,
    )

    rows = PostgresCommunityUserRepository().list_world_records_for_player(7)

    assert rows == []
    assert cursor.params == {"player_id": 7}
    assert "LEAD(wr.id_player) OVER" in cursor.query
    assert "PARTITION BY wr.id_map, wr.id_vehicle, wr.is_mythic" in cursor.query
    assert "ORDER BY wr.id_record" in cursor.query
    assert "AS beaten_by_other" in cursor.query
