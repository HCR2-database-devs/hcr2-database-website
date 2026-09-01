from dataclasses import dataclass
from typing import Any

from app.db.session import DatabaseConfig, open_connection


@dataclass(frozen=True, slots=True)
class StatsService:
    config: DatabaseConfig | None = None

    def record_history(
        self,
        map_name: str,
        vehicle_name: str,
        mythic: bool | None = None,
    ) -> dict[str, Any]:
        where = [
            "LOWER(m.name_map) = LOWER(%(map)s)",
            "LOWER(v.name_vehicle) = LOWER(%(vehicle)s)",
        ]
        params: dict[str, Any] = {"map": map_name, "vehicle": vehicle_name}
        if mythic is not None:
            where.append("wr.is_mythic = %(mythic)s")
            params["mythic"] = mythic

        where_clause = " AND ".join(where)
        rows = self._fetch_all(
            f"""
            SELECT
                wr.id_record AS "idRecord",
                wr.distance,
                wr.current,
                wr.is_mythic AS "isMythic",
                wr.questionable,
                COALESCE(wr.questionable_reason, '') AS questionable_reason,
                wr.created_at,
                p.name_player AS "playerName",
                COALESCE(p.country, '') AS "playerCountry",
                string_agg(
                    tp.name_tuning_part, ', ' ORDER BY tp.name_tuning_part
                ) AS "tuningParts"
            FROM world_record AS wr
            JOIN map AS m ON wr.id_map = m.id_map
            JOIN vehicle AS v ON wr.id_vehicle = v.id_vehicle
            LEFT JOIN player AS p ON wr.id_player = p.id_player
            LEFT JOIN tuning_setup_part tsp ON wr.id_tuning_setup = tsp.id_tuning_setup
            LEFT JOIN tuning_part tp ON tsp.id_tuning_part = tp.id_tuning_part
            WHERE {where_clause}
            GROUP BY
                wr.id_record, wr.distance, wr.current, wr.is_mythic, wr.questionable,
                wr.questionable_reason, wr.created_at, p.name_player, p.country
            ORDER BY wr.created_at ASC, wr.id_record ASC
            """,
            params,
        )

        return {
            "map": map_name,
            "vehicle": vehicle_name,
            "entries": rows,
        }

    def submission_volume(self, weeks: int) -> dict[str, Any]:
        bounded = max(1, min(weeks, 52))
        rows = self._fetch_all(
            """
            SELECT
                to_char(w.week_start, 'YYYY-MM-DD') AS "weekStart",
                COALESCE(s.pending, 0) AS pending,
                COALESCE(s.approved, 0) AS approved,
                COALESCE(s.rejected, 0) AS rejected,
                COALESCE(s.total, 0) AS total
            FROM (
                SELECT
                    date_trunc('week', CURRENT_TIMESTAMP)
                    - (n::int) * INTERVAL '1 week' AS week_start
                FROM generate_series(0, %(weeks)s - 1) AS n
            ) AS w
            LEFT JOIN (
                SELECT
                    date_trunc('week', submitted_at) AS week_start,
                    COUNT(*) FILTER (WHERE status = 'pending') AS pending,
                    COUNT(*) FILTER (WHERE status = 'approved') AS approved,
                    COUNT(*) FILTER (WHERE status = 'rejected') AS rejected,
                    COUNT(*) AS total
                FROM pending_submission
                GROUP BY date_trunc('week', submitted_at)
            ) AS s ON s.week_start = w.week_start
            ORDER BY w.week_start ASC
            """,
            {"weeks": bounded},
        )
        return {"weeks": rows}

    def _fetch_all(
        self, sql: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        with open_connection(self.config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or {})
                return [dict(row) for row in cursor.fetchall()]
