from typing import Any

from app.services.stats_service import StatsService


class Capture:
    def __init__(self) -> None:
        self.last_sql = ""
        self.last_params: dict[str, Any] = {}
        self.result_rows: list[dict[str, Any]] = []

    def fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        self.last_sql = sql
        self.last_params = params or {}
        return self.result_rows


class FakeStatsService:
    def __init__(self) -> None:
        self.capture = Capture()

    def record_history(
        self,
        map_name: str,
        vehicle_name: str,
        mythic: bool | None = None,
    ) -> dict[str, Any]:
        rows = self.capture.fetch_all(
            "SELECT wr.id_record AS \"idRecord\", LOWER(m.name_map) AS map, "
            "LOWER(v.name_vehicle) AS vehicle FROM world_record AS wr "
            "JOIN map AS m ON wr.id_map = m.id_map "
            "JOIN vehicle AS v ON wr.id_vehicle = v.id_vehicle "
            "WHERE LOWER(m.name_map) = LOWER(%(map)s) "
            "AND LOWER(v.name_vehicle) = LOWER(%(vehicle)s) "
            "AND wr.is_mythic = %(mythic)s",
            {"map": map_name, "vehicle": vehicle_name, "mythic": mythic},
        )
        return {"map": map_name, "vehicle": vehicle_name, "entries": rows}

    def submission_volume(self, weeks: int) -> dict[str, Any]:
        bounded = max(1, min(weeks, 52))
        rows = self.capture.fetch_all(
            "SELECT w.week_start AS \"weekStart\", %(weeks)s AS weeks FROM pending_submission w",
            {"weeks": bounded},
        )
        return {"weeks": rows}

    def longest_record(self) -> dict[str, Any]:
        rows = self.capture.fetch_all("SELECT * FROM longest_standing_record")
        return {"set": bool(rows), "distance": (rows[0]["distance"] if rows else None)}


def test_record_history_filters_by_map_and_vehicle() -> None:
    service = FakeStatsService()
    result = service.record_history("Countryside", "Jeep")

    assert "LOWER(m.name_map)" in service.capture.last_sql
    assert "LOWER(v.name_vehicle)" in service.capture.last_sql
    assert service.capture.last_params["map"] == "Countryside"
    assert service.capture.last_params["vehicle"] == "Jeep"
    assert result["map"] == "Countryside"
    assert result["vehicle"] == "Jeep"


def test_record_history_passes_mythic_flag() -> None:
    service = FakeStatsService()
    service.record_history("Countryside", "Jeep", mythic=True)

    assert service.capture.last_params["mythic"] is True


def test_submission_volume_bounds_weeks() -> None:
    service = FakeStatsService()
    service.submission_volume(0)
    assert service.capture.last_params["weeks"] == 1
    service.submission_volume(99)
    assert service.capture.last_params["weeks"] == 52
    service.submission_volume(12)
    assert service.capture.last_params["weeks"] == 12


def test_stats_service_default_config_is_available() -> None:
    assert StatsService().config is None


def test_longest_record_unset_returns_set_false() -> None:
    service = FakeStatsService()
    service.capture.result_rows = []

    result = service.longest_record()

    assert result["set"] is False


def test_longest_record_returns_record_row() -> None:
    service = FakeStatsService()
    service.capture.result_rows = [{"distance": 12345, "mapName": "Countryside"}]

    result = service.longest_record()

    assert result["set"] is True
    assert result["distance"] == 12345