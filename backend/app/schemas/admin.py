from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AdminPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class SubmitRecordRequest(AdminPayload):
    map_id: int = Field(validation_alias=AliasChoices("mapId", "map_id"))
    vehicle_id: int = Field(validation_alias=AliasChoices("vehicleId", "vehicle_id"))
    distance: int
    tuning_setup_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("tuningSetupId", "tuning_setup_id"),
    )
    player_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("playerId", "player_id"),
    )
    player_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("playerName", "player_name"),
    )
    new_player_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("newPlayerName", "new_player_name"),
    )
    country: str | None = None
    questionable: int = 0
    questionable_reason: str | None = Field(
        default=None,
        validation_alias=AliasChoices("questionableReason", "questionable_reason", "note"),
    )


class DeleteRecordRequest(AdminPayload):
    record_id: int = Field(validation_alias=AliasChoices("recordId", "record_id"))


class SetQuestionableRequest(AdminPayload):
    record_id: int = Field(validation_alias=AliasChoices("recordId", "record_id"))
    questionable: int
    note: str | None = Field(default=None, validation_alias=AliasChoices("note", "reason"))


class AssignSetupRequest(AdminPayload):
    record_id: int = Field(validation_alias=AliasChoices("recordId", "record_id"))
    tuning_setup_id: int = Field(validation_alias=AliasChoices("tuningSetupId", "tuning_setup_id"))


class AddMapRequest(AdminPayload):
    map_name: str = Field(validation_alias=AliasChoices("mapName", "map_name", "name"))


class AddVehicleRequest(AdminPayload):
    vehicle_name: str = Field(validation_alias=AliasChoices("vehicleName", "vehicle_name", "name"))


class AddTuningPartRequest(AdminPayload):
    part_name: str = Field(validation_alias=AliasChoices("partName", "part_name", "name"))


class AddTuningSetupRequest(AdminPayload):
    part_ids: list[int] = Field(validation_alias=AliasChoices("partIds", "part_ids"))


class PendingActionRequest(AdminPayload):
    id: int


class PostNewsRequest(AdminPayload):
    title: str
    content: str


class SetMaintenanceRequest(AdminPayload):
    action: str | None = None
    maintenance: bool | None = None


AdminResponse = dict[str, Any]
