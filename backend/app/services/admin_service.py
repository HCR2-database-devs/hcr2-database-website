import re
from pathlib import Path
from typing import Any

from app.core.config import REPO_ROOT
from app.db.session import DatabaseConfig, open_connection
from app.schemas.admin import (
    AddMapRequest,
    AddTuningPartRequest,
    AddTuningSetupRequest,
    AddVehicleRequest,
    AssignSetupRequest,
    DeleteRecordRequest,
    PostNewsRequest,
    SetQuestionableRequest,
    SubmitRecordRequest,
)


class AdminServiceError(Exception):
    status_code = 400


class AdminNotFoundError(AdminServiceError):
    status_code = 404


class AdminConflictError(AdminServiceError):
    status_code = 409


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]*>", "", value).strip()


class AdminService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config
        self._maintenance_flag = REPO_ROOT / "MAINTENANCE"

    def list_records(self) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        wr.idrecord AS "idRecord",
                        wr.idmap AS "idMap",
                        wr.idvehicle AS "idVehicle",
                        wr.idplayer AS "idPlayer",
                        wr.idtuningsetup AS "idTuningSetup",
                        wr.distance,
                        wr.current,
                        wr.questionable,
                        COALESCE(wr.questionable_reason, '') AS questionable_reason,
                        m.namemap AS map_name,
                        v.namevehicle AS vehicle_name,
                        p.nameplayer AS player_name,
                        p.country AS player_country,
                        string_agg(tp.nametuningpart, ', ') AS tuning_parts
                    FROM _worldrecord AS wr
                    LEFT JOIN _map AS m ON wr.idmap = m.idmap
                    LEFT JOIN _vehicle AS v ON wr.idvehicle = v.idvehicle
                    LEFT JOIN _player AS p ON wr.idplayer = p.idplayer
                    LEFT JOIN _tuningsetupparts tsp ON wr.idtuningsetup = tsp.idtuningsetup
                    LEFT JOIN _tuningpart tp ON tsp.idtuningpart = tp.idtuningpart
                    WHERE wr.current = 1
                    GROUP BY wr.idrecord, wr.idmap, wr.idvehicle, wr.idplayer,
                        wr.idtuningsetup, wr.distance, wr.current, wr.questionable,
                        wr.questionable_reason, m.namemap, v.namevehicle, p.nameplayer, p.country
                    ORDER BY m.namemap, v.namevehicle
                    """
                )
                return [dict(row) for row in cursor.fetchall()]

    def list_pending(self) -> dict[str, list[dict[str, Any]]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        p.id,
                        p.idmap AS "idMap",
                        p.idvehicle AS "idVehicle",
                        p.distance,
                        p.playername AS "playerName",
                        p.playercountry AS "playerCountry",
                        p.tuningparts AS "tuningParts",
                        p.status,
                        p.submitted_at,
                        m.namemap AS "mapName",
                        v.namevehicle AS "vehicleName"
                    FROM pendingsubmission p
                    LEFT JOIN _map m ON p.idmap = m.idmap
                    LEFT JOIN _vehicle v ON p.idvehicle = v.idvehicle
                    WHERE p.status = 'pending'
                    ORDER BY p.submitted_at DESC
                    """
                )
                return {"pending": [dict(row) for row in cursor.fetchall()]}

    def submit_record(self, payload: SubmitRecordRequest) -> dict[str, Any]:
        if payload.distance <= 0:
            raise AdminServiceError("Distance must be a positive number.")
        if payload.questionable not in (0, 1):
            raise AdminServiceError("Invalid questionable value (must be 0 or 1).")

        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._ensure_exists(cursor, "_map", "idmap", payload.map_id, "Map not found.")
                self._ensure_exists(
                    cursor,
                    "_vehicle",
                    "idvehicle",
                    payload.vehicle_id,
                    "Vehicle not found.",
                )
                if payload.tuning_setup_id is not None:
                    self._ensure_exists(
                        cursor,
                        "_tuningsetup",
                        "idtuningsetup",
                        payload.tuning_setup_id,
                        "Tuning setup not found.",
                    )

                player_id = self._resolve_player(cursor, payload)

                cursor.execute(
                    "DELETE FROM _worldrecord WHERE idmap = %s AND idvehicle = %s",
                    (payload.map_id, payload.vehicle_id),
                )
                cursor.execute(
                    """
                    INSERT INTO _worldrecord (
                        idmap, idvehicle, idplayer, distance, current,
                        idtuningsetup, questionable, questionable_reason
                    )
                    VALUES (%s, %s, %s, %s, 1, %s, %s, %s)
                    RETURNING idrecord
                    """,
                    (
                        payload.map_id,
                        payload.vehicle_id,
                        player_id,
                        payload.distance,
                        payload.tuning_setup_id,
                        payload.questionable,
                        _clean_text(payload.questionable_reason) or None,
                    ),
                )
                record_id = cursor.fetchone()["idrecord"]

                map_name = self._name_for(cursor, "_map", "namemap", "idmap", payload.map_id)
                vehicle_name = self._name_for(
                    cursor,
                    "_vehicle",
                    "namevehicle",
                    "idvehicle",
                    payload.vehicle_id,
                )
                player_name = self._name_for(cursor, "_player", "nameplayer", "idplayer", player_id)

        return {
            "success": True,
            "idRecord": record_id,
            "playerId": player_id,
            "mapName": map_name,
            "vehicleName": vehicle_name,
            "playerName": player_name,
            "distance": payload.distance,
        }

    def delete_record(self, payload: DeleteRecordRequest) -> dict[str, bool]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM _worldrecord WHERE idrecord = %s", (payload.record_id,))
        return {"success": True}

    def set_questionable(self, payload: SetQuestionableRequest) -> dict[str, Any]:
        if payload.questionable not in (0, 1):
            raise AdminServiceError("Invalid questionable value (must be 0 or 1)")

        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._ensure_exists(
                    cursor,
                    "_worldrecord",
                    "idrecord",
                    payload.record_id,
                    "Record not found",
                )
                cursor.execute(
                    """
                    UPDATE _worldrecord
                    SET questionable = %s, questionable_reason = %s
                    WHERE idrecord = %s
                    """,
                    (payload.questionable, _clean_text(payload.note) or None, payload.record_id),
                )
        return {"success": True, "message": "Record status updated successfully"}

    def assign_setup(self, payload: AssignSetupRequest) -> dict[str, bool]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT idtuningsetup FROM _worldrecord WHERE idrecord = %s",
                    (payload.record_id,),
                )
                record = cursor.fetchone()
                if record is None:
                    raise AdminNotFoundError("Record not found")
                if record["idtuningsetup"]:
                    raise AdminServiceError("Record already has a tuning setup assigned")

                self._ensure_exists(
                    cursor,
                    "_tuningsetup",
                    "idtuningsetup",
                    payload.tuning_setup_id,
                    "Tuning setup not found",
                )
                cursor.execute(
                    "UPDATE _worldrecord SET idtuningsetup = %s WHERE idrecord = %s",
                    (payload.tuning_setup_id, payload.record_id),
                )
        return {"success": True}

    def add_map(self, payload: AddMapRequest) -> dict[str, Any]:
        name = _clean_text(payload.map_name)
        if not name:
            raise AdminServiceError("Map name is required.")
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._ensure_unique_name(
                    cursor,
                    "_map",
                    "namemap",
                    name,
                    "Map already exists in database.",
                )
                new_id = self._next_manual_id(cursor, "_map", "idmap")
                cursor.execute("INSERT INTO _map (idmap, namemap) VALUES (%s, %s)", (new_id, name))
        return {"success": True, "idMap": new_id, "nameMap": name, "iconMessage": ""}

    def add_vehicle(self, payload: AddVehicleRequest) -> dict[str, Any]:
        name = _clean_text(payload.vehicle_name)
        if not name:
            raise AdminServiceError("Vehicle name is required.")
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._ensure_unique_name(
                    cursor,
                    "_vehicle",
                    "namevehicle",
                    name,
                    "Vehicle already exists in database.",
                )
                new_id = self._next_manual_id(cursor, "_vehicle", "idvehicle")
                cursor.execute(
                    "INSERT INTO _vehicle (idvehicle, namevehicle) VALUES (%s, %s)",
                    (new_id, name),
                )
        return {"success": True, "idVehicle": new_id, "nameVehicle": name, "iconMessage": ""}

    def add_tuning_part(self, payload: AddTuningPartRequest) -> dict[str, Any]:
        name = _clean_text(payload.part_name)
        if not name:
            raise AdminServiceError("Tuning part name is required.")
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._ensure_unique_name(
                    cursor,
                    "_tuningpart",
                    "nametuningpart",
                    name,
                    "A tuning part with this name already exists.",
                )
                cursor.execute(
                    "INSERT INTO _tuningpart (nametuningpart) VALUES (%s) RETURNING idtuningpart",
                    (name,),
                )
                new_id = cursor.fetchone()["idtuningpart"]
        return {"success": True, "idTuningPart": new_id, "nameTuningPart": name, "iconMessage": ""}

    def add_tuning_setup(self, payload: AddTuningSetupRequest) -> dict[str, Any]:
        part_ids = sorted(set(int(part_id) for part_id in payload.part_ids))
        if len(part_ids) < 3 or len(part_ids) > 4:
            raise AdminServiceError("Must select 3 or 4 tuning parts.")

        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._ensure_parts_exist(cursor, part_ids)
                existing = self._find_setup_by_parts(cursor, part_ids)
                if existing is not None:
                    raise AdminConflictError("A setup with these parts already exists.")
                setup_id = self._create_setup(cursor, part_ids)
        return {"success": True, "idTuningSetup": setup_id}

    def approve_submission(self, submission_id: int) -> dict[str, bool]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                submission = self._get_pending_submission(cursor, submission_id)

                cursor.execute(
                    "DELETE FROM _worldrecord WHERE idmap = %s AND idvehicle = %s",
                    (submission["idmap"], submission["idvehicle"]),
                )

                player_id = self._find_or_create_player(
                    cursor,
                    _clean_text(submission.get("playername")),
                    _clean_text(submission.get("playercountry")),
                )
                cursor.execute(
                    """
                    INSERT INTO _worldrecord (idmap, idvehicle, idplayer, distance, current)
                    VALUES (%s, %s, %s, %s, 1)
                    RETURNING idrecord
                    """,
                    (
                        submission["idmap"],
                        submission["idvehicle"],
                        player_id,
                        submission["distance"],
                    ),
                )
                record_id = cursor.fetchone()["idrecord"]

                tuning_parts = _clean_text(submission.get("tuningparts"))
                if tuning_parts:
                    part_ids = self._part_ids_from_names(cursor, tuning_parts)
                    if 3 <= len(part_ids) <= 4:
                        setup_id = self._create_setup(cursor, part_ids)
                        cursor.execute(
                            "UPDATE _worldrecord SET idtuningsetup = %s WHERE idrecord = %s",
                            (setup_id, record_id),
                        )

                cursor.execute(
                    "UPDATE pendingsubmission SET status = 'approved' WHERE id = %s",
                    (submission_id,),
                )
        return {"success": True}

    def reject_submission(self, submission_id: int) -> dict[str, bool]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._get_pending_submission(cursor, submission_id)
                cursor.execute(
                    "UPDATE pendingsubmission SET status = 'rejected' WHERE id = %s",
                    (submission_id,),
                )
        return {"success": True}

    def post_news(self, payload: PostNewsRequest, author: str | None) -> dict[str, bool]:
        title = _strip_tags(payload.title)
        content = _strip_tags(payload.content)
        if not title or not content:
            raise AdminServiceError("Title and content are required.")
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO news (title, content, author) VALUES (%s, %s, %s)",
                    (title, content, author or ""),
                )
        return {"success": True}

    def maintenance_status(self, allowed: bool) -> dict[str, bool]:
        return {"maintenance": self._maintenance_flag.exists(), "allowed": allowed}

    def set_maintenance(
        self,
        action: str | None,
        maintenance: bool | None = None,
    ) -> dict[str, bool]:
        target = maintenance
        normalized = _clean_text(action).lower()
        if target is None:
            if normalized in {"enable", "on", "1", "true"}:
                target = True
            elif normalized in {"disable", "off", "0", "false"}:
                target = False
            else:
                target = not self._maintenance_flag.exists()

        if target:
            self._maintenance_flag.write_text("1", encoding="utf-8")
        elif self._maintenance_flag.exists():
            self._maintenance_flag.unlink()
        return {"success": True, "maintenance": bool(target)}

    def integrity_check(self) -> dict[str, Any]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok")
                ok = cursor.fetchone()["ok"]
                counts: dict[str, int] = {}
                for table in (
                    "_map",
                    "_vehicle",
                    "_player",
                    "_tuningpart",
                    "_tuningsetup",
                    "_worldrecord",
                    "pendingsubmission",
                    "news",
                ):
                    cursor.execute(f"SELECT count(*) AS count FROM {table}")
                    counts[table] = int(cursor.fetchone()["count"])
        return {"ok": True, "result": ok, "counts": counts}

    def _resolve_player(self, cursor: Any, payload: SubmitRecordRequest) -> int:
        if payload.player_id is not None:
            self._ensure_exists(
                cursor,
                "_player",
                "idplayer",
                payload.player_id,
                "Selected player does not exist.",
            )
            return payload.player_id

        new_name = _clean_text(payload.new_player_name or payload.player_name)
        if not new_name:
            raise AdminServiceError("No valid player selected or provided.")
        if not _clean_text(payload.country):
            raise AdminServiceError("Please provide a country for the new player.")
        return self._find_or_create_player(cursor, new_name, _clean_text(payload.country))

    def _find_or_create_player(self, cursor: Any, name: str, country: str) -> int:
        if not name:
            raise AdminServiceError("No valid player selected or provided.")
        cursor.execute("SELECT idplayer FROM _player WHERE nameplayer = %s LIMIT 1", (name,))
        existing = cursor.fetchone()
        if existing:
            return int(existing["idplayer"])
        new_id = self._next_manual_id(cursor, "_player", "idplayer")
        cursor.execute(
            "INSERT INTO _player (idplayer, nameplayer, country) VALUES (%s, %s, %s)",
            (new_id, name, country or None),
        )
        return new_id

    def _get_pending_submission(self, cursor: Any, submission_id: int) -> dict[str, Any]:
        cursor.execute("SELECT * FROM pendingsubmission WHERE id = %s LIMIT 1", (submission_id,))
        submission = cursor.fetchone()
        if submission is None:
            raise AdminNotFoundError("Submission not found")
        return dict(submission)

    def _part_ids_from_names(self, cursor: Any, tuning_parts: str) -> list[int]:
        names = [_clean_text(part) for part in tuning_parts.split(",") if _clean_text(part)]
        if not (3 <= len(names) <= 4):
            return []
        part_ids: list[int] = []
        for name in names:
            cursor.execute(
                "SELECT idtuningpart FROM _tuningpart WHERE nametuningpart = %s LIMIT 1",
                (name,),
            )
            row = cursor.fetchone()
            if row is None:
                return []
            part_ids.append(int(row["idtuningpart"]))
        return sorted(part_ids)

    def _ensure_parts_exist(self, cursor: Any, part_ids: list[int]) -> None:
        cursor.execute(
            "SELECT idtuningpart FROM _tuningpart WHERE idtuningpart = ANY(%s::int[])",
            (part_ids,),
        )
        found = {int(row["idtuningpart"]) for row in cursor.fetchall()}
        missing = [part_id for part_id in part_ids if part_id not in found]
        if missing:
            raise AdminNotFoundError(f"Tuning part not found: {missing[0]}")

    def _find_setup_by_parts(self, cursor: Any, part_ids: list[int]) -> int | None:
        cursor.execute(
            """
            SELECT idtuningsetup
            FROM (
                SELECT idtuningsetup, array_agg(idtuningpart ORDER BY idtuningpart) AS part_ids
                FROM _tuningsetupparts
                GROUP BY idtuningsetup
            ) grouped
            WHERE part_ids = %s::int[]
            LIMIT 1
            """,
            (part_ids,),
        )
        row = cursor.fetchone()
        return int(row["idtuningsetup"]) if row else None

    def _create_setup(self, cursor: Any, part_ids: list[int]) -> int:
        cursor.execute("INSERT INTO _tuningsetup DEFAULT VALUES RETURNING idtuningsetup")
        setup_id = int(cursor.fetchone()["idtuningsetup"])
        for part_id in part_ids:
            cursor.execute(
                "INSERT INTO _tuningsetupparts (idtuningsetup, idtuningpart) VALUES (%s, %s)",
                (setup_id, part_id),
            )
        return setup_id

    def _ensure_exists(
        self,
        cursor: Any,
        table: str,
        id_column: str,
        value: int | None,
        message: str,
    ) -> None:
        if value is None:
            raise AdminNotFoundError(message)
        cursor.execute(f"SELECT 1 FROM {table} WHERE {id_column} = %s LIMIT 1", (value,))
        if cursor.fetchone() is None:
            raise AdminNotFoundError(message)

    def _ensure_unique_name(
        self,
        cursor: Any,
        table: str,
        column: str,
        name: str,
        message: str,
    ) -> None:
        cursor.execute(f"SELECT 1 FROM {table} WHERE {column} = %s LIMIT 1", (name,))
        if cursor.fetchone() is not None:
            raise AdminConflictError(message)

    def _next_manual_id(self, cursor: Any, table: str, column: str) -> int:
        cursor.execute(f"SELECT COALESCE(MAX({column}), 0) + 1 AS next_id FROM {table}")
        return int(cursor.fetchone()["next_id"])

    def _name_for(
        self,
        cursor: Any,
        table: str,
        name_column: str,
        id_column: str,
        value: int | None,
    ) -> str:
        if value is None:
            return "Unknown"
        cursor.execute(
            f"SELECT {name_column} AS name FROM {table} WHERE {id_column} = %s LIMIT 1",
            (value,),
        )
        row = cursor.fetchone()
        return str(row["name"]) if row else "Unknown"


def maintenance_flag_path() -> Path:
    return REPO_ROOT / "MAINTENANCE"
