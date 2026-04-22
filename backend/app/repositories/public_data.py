from typing import Any, Protocol

from app.db.session import DatabaseConfig, open_connection


class PublicDataRepository(Protocol):
    def list_maps(self) -> list[dict[str, Any]]: ...

    def list_vehicles(self) -> list[dict[str, Any]]: ...

    def list_players(self) -> list[dict[str, Any]]: ...

    def list_tuning_parts(self) -> list[dict[str, Any]]: ...

    def list_tuning_setups(self) -> list[dict[str, Any]]: ...

    def list_records(self) -> list[dict[str, Any]]: ...

    def search_records(self, filters: dict[str, Any]) -> list[dict[str, Any]]: ...


class PostgresPublicDataRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def _fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or {})
                return [dict(row) for row in cursor.fetchall()]

    def list_maps(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT id_map AS "idMap", name_map AS "nameMap", special
            FROM map
            ORDER BY name_map
            """
        )

    def list_vehicles(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT id_vehicle AS "idVehicle", name_vehicle AS "nameVehicle"
            FROM vehicle
            ORDER BY name_vehicle
            """
        )

    def list_players(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT id_player AS "idPlayer", name_player AS "namePlayer", country
            FROM player
            ORDER BY name_player
            """
        )

    def list_tuning_parts(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT
                id_tuning_part AS "idTuningPart",
                name_tuning_part AS "nameTuningPart"
            FROM tuning_part
            ORDER BY name_tuning_part
            """
        )

    def list_tuning_setups(self) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT
                ts.id_tuning_setup AS "idTuningSetup",
                string_agg(tp.name_tuning_part, ', ' ORDER BY tp.name_tuning_part) AS parts
            FROM tuning_setup ts
            LEFT JOIN tuning_setup_part tsp ON ts.id_tuning_setup = tsp.id_tuning_setup
            LEFT JOIN tuning_part tp ON tsp.id_tuning_part = tp.id_tuning_part
            GROUP BY ts.id_tuning_setup
            ORDER BY ts.id_tuning_setup
            """
        )
        for row in rows:
            parts = row.get("parts")
            if parts is None:
                row["parts"] = []
            else:
                row["parts"] = [{"nameTuningPart": name} for name in str(parts).split(", ")]
        return rows

    def list_records(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT
                wr.id_record AS "idRecord",
                wr.id_map AS "idMap",
                wr.id_vehicle AS "idVehicle",
                wr.id_player AS "idPlayer",
                wr.distance,
                wr.current,
                wr.id_tuning_setup AS "idTuningSetup",
                wr.questionable,
                COALESCE(wr.questionable_reason, '') AS questionable_reason,
                m.name_map AS map_name,
                v.name_vehicle AS vehicle_name,
                p.name_player AS player_name,
                COALESCE(p.country, '') AS player_country,
                string_agg(tp.name_tuning_part, ', ' ORDER BY tp.name_tuning_part) AS tuning_parts
            FROM world_record AS wr
            JOIN map AS m ON wr.id_map = m.id_map
            JOIN vehicle AS v ON wr.id_vehicle = v.id_vehicle
            LEFT JOIN player AS p ON wr.id_player = p.id_player
            LEFT JOIN tuning_setup_part tsp ON wr.id_tuning_setup = tsp.id_tuning_setup
            LEFT JOIN tuning_part tp ON tsp.id_tuning_part = tp.id_tuning_part
            WHERE wr.current = 1
            GROUP BY wr.id_record, wr.id_map, wr.id_vehicle, wr.id_player,
                wr.distance, wr.current, wr.id_tuning_setup, wr.questionable,
                wr.questionable_reason, m.name_map, v.name_vehicle, p.name_player, p.country
            ORDER BY wr.id_map DESC
            """
        )

    def search_records(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        where = ["wr.current = 1"]
        params: dict[str, Any] = {}

        like_filters = {
            "map": ("m.name_map", "map"),
            "vehicle": ("v.name_vehicle", "vehicle"),
            "player": ("p.name_player", "player"),
            "country": ("p.country", "country"),
        }
        for raw_key, (column, param_key) in like_filters.items():
            value = self._like_value(filters.get(raw_key))
            if value is not None:
                where.append(f"LOWER({column}) LIKE LOWER(%({param_key})s)")
                params[param_key] = value

        questionable = filters.get("questionable")
        if questionable in {"0", "1", 0, 1}:
            where.append("wr.questionable = %(questionable)s")
            params["questionable"] = int(questionable)

        min_distance = self._int_filter(filters.get("min_distance"))
        if min_distance is not None:
            where.append("wr.distance >= %(min_distance)s")
            params["min_distance"] = min_distance

        max_distance = self._int_filter(filters.get("max_distance"))
        if max_distance is not None:
            where.append("wr.distance <= %(max_distance)s")
            params["max_distance"] = max_distance

        query = self._like_value(filters.get("q"))
        if query is not None:
            where.append(
                """
                (
                    LOWER(m.name_map) LIKE LOWER(%(q)s)
                    OR LOWER(v.name_vehicle) LIKE LOWER(%(q)s)
                    OR LOWER(p.name_player) LIKE LOWER(%(q)s)
                    OR LOWER(COALESCE(wr.questionable_reason, '')) LIKE LOWER(%(q)s)
                )
                """
            )
            params["q"] = query

        limit = self._bounded_int(filters.get("limit"), default=100, minimum=1, maximum=500)
        offset = self._bounded_int(filters.get("offset"), default=0, minimum=0, maximum=10_000_000)
        params["limit"] = limit
        params["offset"] = offset

        return self._fetch_all(
            f"""
            SELECT
                wr.id_record AS "idRecord",
                wr.id_map AS "idMap",
                wr.id_vehicle AS "idVehicle",
                wr.id_player AS "idPlayer",
                wr.distance,
                wr.current,
                wr.id_tuning_setup AS "idTuningSetup",
                wr.questionable,
                COALESCE(wr.questionable_reason, '') AS notes,
                m.name_map AS map_name,
                v.name_vehicle AS vehicle_name,
                p.name_player AS player_name,
                COALESCE(p.country, '') AS player_country,
                string_agg(tp.name_tuning_part, ', ' ORDER BY tp.name_tuning_part) AS tuning_parts
            FROM world_record AS wr
            JOIN map AS m ON wr.id_map = m.id_map
            JOIN vehicle AS v ON wr.id_vehicle = v.id_vehicle
            LEFT JOIN player AS p ON wr.id_player = p.id_player
            LEFT JOIN tuning_setup_part tsp ON wr.id_tuning_setup = tsp.id_tuning_setup
            LEFT JOIN tuning_part tp ON tsp.id_tuning_part = tp.id_tuning_part
            WHERE {' AND '.join(where)}
            GROUP BY wr.id_record, wr.id_map, wr.id_vehicle, wr.id_player,
                wr.distance, wr.current, wr.id_tuning_setup, wr.questionable,
                wr.questionable_reason, m.name_map, v.name_vehicle, p.name_player, p.country
            ORDER BY wr.id_map DESC
            LIMIT %(limit)s OFFSET %(offset)s
            """,
            params,
        )

    @staticmethod
    def _like_value(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return "%" + text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

    @staticmethod
    def _int_filter(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _bounded_int(cls, value: Any, *, default: int, minimum: int, maximum: int) -> int:
        parsed = cls._int_filter(value)
        if parsed is None:
            return default
        return min(max(parsed, minimum), maximum)
