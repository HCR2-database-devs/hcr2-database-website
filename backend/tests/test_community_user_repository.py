from typing import Any

from app.repositories.community_user import (
    PostgresCommunityUserRepository,
    _public_filters,
)


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


def test_public_filters_apply_favorite_and_visible_hcr2_filters() -> None:
    where_sql, params = _public_filters(
        None,
        None,
        favorite_vehicle_id=7,
        favorite_map_id=9,
        has_hcr2=True,
    )

    assert "cu.show_favorite_vehicle = TRUE" in where_sql
    assert "cu.favorite_vehicle_id = %(favorite_vehicle_id)s" in where_sql
    assert "cu.show_favorite_map = TRUE" in where_sql
    assert "cu.favorite_map_id = %(favorite_map_id)s" in where_sql
    assert "cu.show_hcr2_player_name = TRUE" in where_sql
    assert "l.status = 'active'" in where_sql
    assert params == {"favorite_vehicle_id": 7, "favorite_map_id": 9}

    where_sql, params = _public_filters(None, None, has_hcr2=False)

    assert "cu.show_hcr2_player_name = FALSE OR NOT EXISTS" in where_sql
    assert params == {}
