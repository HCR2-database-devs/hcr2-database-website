from typing import Any, Protocol

from app.db.session import DatabaseConfig, open_connection


class PublicDataRepository(Protocol):
    def list_maps(self) -> list[dict[str, Any]]: ...

    def list_vehicles(self) -> list[dict[str, Any]]: ...

    def list_players(self) -> list[dict[str, Any]]: ...

    def list_tuning_parts(self) -> list[dict[str, Any]]: ...

    def list_tuning_setups(self) -> list[dict[str, Any]]: ...

    def list_records(self) -> list[dict[str, Any]]: ...


class PostgresPublicDataRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def _fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or {})
                return [dict(row) for row in cursor.fetchall()]

    def list_maps(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM _map")

    def list_vehicles(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM _vehicle")

    def list_players(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM _player")

    def list_tuning_parts(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM _tuningpart ORDER BY nameTuningPart")

    def list_tuning_setups(self) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT ts.idTuningSetup,
                   string_agg(tp.nameTuningPart, ', ') AS parts
            FROM _tuningsetup ts
            JOIN _tuningsetupparts tsp ON ts.idTuningSetup = tsp.idTuningSetup
            JOIN _tuningpart tp ON tsp.idTuningPart = tp.idTuningPart
            GROUP BY ts.idTuningSetup
            ORDER BY ts.idTuningSetup
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
                wr.idRecord AS idRecord,
                wr.distance,
                wr.current,
                wr.idTuningSetup,
                wr.questionable,
                COALESCE(wr.questionable_reason, '') AS questionable_reason,
                m.nameMap AS map_name,
                v.nameVehicle AS vehicle_name,
                p.namePlayer AS player_name,
                p.country AS player_country,
                string_agg(tp.nameTuningPart, ', ') AS tuning_parts
            FROM _worldrecord AS wr
            JOIN _map AS m ON wr.idMap = m.idMap
            JOIN _vehicle AS v ON wr.idVehicle = v.idVehicle
            JOIN _player AS p ON wr.idPlayer = p.idPlayer
            LEFT JOIN _tuningsetupparts tsp ON wr.idTuningSetup = tsp.idTuningSetup
            LEFT JOIN _tuningpart tp ON tsp.idTuningPart = tp.idTuningPart
            WHERE wr.current = 1
            GROUP BY wr.idRecord, wr.distance, wr.current, wr.idTuningSetup,
                wr.questionable, wr.questionable_reason, m.nameMap, v.nameVehicle,
                p.namePlayer, p.country
            """
        )
