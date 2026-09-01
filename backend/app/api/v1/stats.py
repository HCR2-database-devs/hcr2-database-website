from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_stats_service
from app.api.responses import DATABASE_ERROR_TYPES, database_error_response
from app.services.admin_service import maintenance_flag_path
from app.services.stats_service import StatsService


def _check_maintenance() -> None:
    if maintenance_flag_path().exists():
        raise HTTPException(status_code=503, detail="Service is under maintenance")


router = APIRouter(tags=["stats"], dependencies=[Depends(_check_maintenance)])

StatsServiceDep = Annotated[StatsService, Depends(get_stats_service)]


@router.get("/stats/record-history", response_model=None)
def get_record_history(
    service: StatsServiceDep,
    map: Annotated[str, Query()],
    vehicle: Annotated[str, Query()],
    mythic: Annotated[str | None, Query()] = None,
) -> Any:
    mythic_bool: bool | None = None
    if mythic in {"true", "false"}:
        mythic_bool = mythic == "true"
    try:
        return service.record_history(map, vehicle, mythic_bool)
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)  # type: ignore[return-value]


@router.get("/stats/submission-volume", response_model=None)
def get_submission_volume(
    service: StatsServiceDep,
    weeks: Annotated[str | None, Query()] = None,
) -> Any:
    week_count = 12
    if weeks is not None:
        try:
            week_count = max(4, min(int(weeks), 52))
        except (TypeError, ValueError):
            week_count = 12
    try:
        return service.submission_volume(week_count)
    except DATABASE_ERROR_TYPES as exc:
        return database_error_response(exc)  # type: ignore[return-value]
