from typing import Any

import pytest

from app.repositories.public_data import PostgresPublicDataRepository
from app.services.public_data_service import (
    InvalidLoadDataType,
    MissingLoadDataType,
    PublicDataService,
)


class FakePublicDataRepository:
    def list_maps(self) -> list[dict[str, Any]]:
        return [{"idMap": 1, "nameMap": "Countryside", "special": 0}]

    def list_vehicles(self) -> list[dict[str, Any]]:
        return [{"idVehicle": 1, "nameVehicle": "Jeep"}]

    def list_players(self) -> list[dict[str, Any]]:
        return [{"idPlayer": 1, "namePlayer": "Player", "country": "FR"}]

    def list_tuning_parts(self) -> list[dict[str, Any]]:
        return [{"idTuningPart": 1, "nameTuningPart": "Wings"}]

    def list_tuning_setups(self) -> list[dict[str, Any]]:
        return [{"idTuningSetup": 1, "parts": [{"nameTuningPart": "Wings"}]}]

    def list_records(self) -> list[dict[str, Any]]:
        return [{"idRecord": 1, "distance": 1234, "map_name": "Countryside"}]

    def search_records(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        return [{"idRecord": 1, "filters": filters}]


class CapturingPostgresPublicDataRepository(PostgresPublicDataRepository):
    def __init__(self) -> None:
        super().__init__()
        self.last_sql = ""
        self.last_params: dict[str, Any] = {}

    def _fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        self.last_sql = sql
        self.last_params = params or {}
        return []


def test_public_data_service_dispatches_public_types() -> None:
    service = PublicDataService(FakePublicDataRepository())

    assert service.load_data("maps")[0]["nameMap"] == "Countryside"
    assert service.load_data("vehicles")[0]["nameVehicle"] == "Jeep"
    assert service.load_data("players")[0]["namePlayer"] == "Player"
    assert service.load_data("tuning_parts")[0]["nameTuningPart"] == "Wings"
    assert service.load_data("tuning_setups")[0]["parts"][0]["nameTuningPart"] == "Wings"
    assert service.load_data("records")[0]["distance"] == 1234


def test_public_data_service_search_records_keeps_api_records_shape() -> None:
    service = PublicDataService(FakePublicDataRepository())

    result = service.search_records({"limit": "1"})

    assert result["count"] == 1
    assert result["records"][0]["filters"] == {"limit": "1"}


def test_postgres_search_records_uses_exact_main_filters_and_car_alias() -> None:
    repository = CapturingPostgresPublicDataRepository()

    repository.search_records(
        {
            "map": "Countryside",
            "car": "Hill Climber",
            "player": "Demo Driver",
            "country": "FR",
            "q": "proof",
        }
    )

    assert "LOWER(m.name_map) = LOWER(%(map)s)" in repository.last_sql
    assert "LOWER(v.name_vehicle) = LOWER(%(vehicle)s)" in repository.last_sql
    assert "LOWER(p.name_player) = LOWER(%(player)s)" in repository.last_sql
    assert "LOWER(p.country) = LOWER(%(country)s)" in repository.last_sql
    assert repository.last_params["map"] == "Countryside"
    assert repository.last_params["vehicle"] == "Hill Climber"
    assert repository.last_params["player"] == "Demo Driver"
    assert repository.last_params["country"] == "FR"
    assert repository.last_params["q"] == "%proof%"


def test_public_data_service_preserves_missing_type_error() -> None:
    service = PublicDataService(FakePublicDataRepository())

    with pytest.raises(MissingLoadDataType, match="No data type specified"):
        service.load_data(None)


def test_public_data_service_preserves_invalid_type_error() -> None:
    service = PublicDataService(FakePublicDataRepository())

    with pytest.raises(InvalidLoadDataType, match="Invalid data type"):
        service.load_data("unknown")
