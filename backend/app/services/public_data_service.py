from dataclasses import dataclass
from typing import Any

from app.repositories.public_data import PublicDataRepository


class InvalidLoadDataType(ValueError):
    pass


class MissingLoadDataType(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PublicDataService:
    repository: PublicDataRepository

    def load_data(self, data_type: str | None) -> list[dict[str, Any]]:
        if data_type is None or data_type == "":
            raise MissingLoadDataType("No data type specified")

        match data_type:
            case "maps":
                return self.repository.list_maps()
            case "vehicles":
                return self.repository.list_vehicles()
            case "players":
                return self.repository.list_players()
            case "tuning_parts":
                return self.repository.list_tuning_parts()
            case "tuning_setups":
                return self.repository.list_tuning_setups()
            case "records":
                return self.repository.list_records()
            case _:
                raise InvalidLoadDataType("Invalid data type")

    def search_records(self, filters: dict[str, Any]) -> dict[str, Any]:
        rows = self.repository.search_records(filters)
        return {"records": rows, "count": len(rows)}
