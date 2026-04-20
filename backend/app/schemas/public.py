from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiRow(BaseModel):
    model_config = ConfigDict(extra="allow")


class MapItem(ApiRow):
    idMap: int
    nameMap: str


class VehicleItem(ApiRow):
    idVehicle: int
    nameVehicle: str


class PlayerItem(ApiRow):
    idPlayer: int
    namePlayer: str
    country: str | None = None


class TuningPartItem(ApiRow):
    idTuningPart: int
    nameTuningPart: str


class TuningSetupPart(BaseModel):
    nameTuningPart: str


class TuningSetupItem(ApiRow):
    idTuningSetup: int
    parts: list[TuningSetupPart]


class RecordItem(ApiRow):
    idRecord: int
    distance: int
    current: int | bool
    idTuningSetup: int | None = None
    questionable: int | bool
    questionable_reason: str
    map_name: str
    vehicle_name: str
    player_name: str
    player_country: str | None = None
    tuning_parts: str | None = None


class ApiError(BaseModel):
    error: str


PublicDataPayload = list[dict[str, Any]]
