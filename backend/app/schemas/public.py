from typing import Any

from pydantic import BaseModel, ConfigDict


class LegacyRow(BaseModel):
    model_config = ConfigDict(extra="allow")


class MapItem(LegacyRow):
    idMap: int
    nameMap: str


class VehicleItem(LegacyRow):
    idVehicle: int
    nameVehicle: str


class PlayerItem(LegacyRow):
    idPlayer: int
    namePlayer: str
    country: str | None = None


class TuningPartItem(LegacyRow):
    idTuningPart: int
    nameTuningPart: str


class TuningSetupPart(BaseModel):
    nameTuningPart: str


class TuningSetupItem(LegacyRow):
    idTuningSetup: int
    parts: list[TuningSetupPart]


class RecordItem(LegacyRow):
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


class LegacyError(BaseModel):
    error: str


PublicDataPayload = list[dict[str, Any]]
