import re
import stat
from pathlib import Path
from typing import Any

from psycopg import sql

from app.core.config import REPO_ROOT
from app.db.session import DatabaseConfig, open_connection
from app.schemas.admin import (
    AddMapRequest,
    AddTuningPartRequest,
    AddTuningSetupRequest,
    AddVehicleRequest,
    AssignSetupRequest,
    DeleteNewsRequest,
    DeleteRecordRequest,
    PostNewsRequest,
    SetQuestionableRequest,
    SubmitRecordRequest,
    UpdateNewsRequest,
)


class AdminServiceError(Exception):
    status_code = 400


class AdminNotFoundError(AdminServiceError):
    status_code = 404


class AdminConflictError(AdminServiceError):
    status_code = 409


class AdminUnsupportedMediaError(AdminServiceError):
    status_code = 415


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]*>", "", value).strip()


class AdminService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config
        self._maintenance_flag = REPO_ROOT / "MAINTENANCE"
        self._backups_dir = REPO_ROOT / "backups"
        self._backup_tables = (
            "map",
            "vehicle",
            "player",
            "tuning_part",
            "tuning_setup",
            "tuning_setup_part",
            "world_record",
            "pending_submission",
            "news",
        )
        self._backup_sequences = {
            "map": ("map_id_seq", "id_map"),
            "vehicle": ("vehicle_id_seq", "id_vehicle"),
            "player": ("player_id_seq", "id_player"),
            "tuning_part": ("tuning_part_id_seq", "id_tuning_part"),
            "tuning_setup": ("tuning_setup_id_seq", "id_tuning_setup"),
            "world_record": ("world_record_id_seq", "id_record"),
            "pending_submission": ("pending_submission_id_seq", "id"),
            "news": ("news_id_seq", "id"),
        }

    def list_records(self) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        wr.id_record AS "idRecord",
                        wr.id_map AS "idMap",
                        wr.id_vehicle AS "idVehicle",
                        wr.id_player AS "idPlayer",
                        wr.id_tuning_setup AS "idTuningSetup",
                        wr.distance,
                        wr.current,
                        wr.questionable,
                        COALESCE(wr.questionable_reason, '') AS questionable_reason,
                        m.name_map AS map_name,
                        v.name_vehicle AS vehicle_name,
                        p.name_player AS player_name,
                        p.country AS player_country,
                        string_agg(
                            tp.name_tuning_part,
                            ', '
                            ORDER BY tp.name_tuning_part
                        ) AS tuning_parts
                    FROM world_record AS wr
                    LEFT JOIN map AS m ON wr.id_map = m.id_map
                    LEFT JOIN vehicle AS v ON wr.id_vehicle = v.id_vehicle
                    LEFT JOIN player AS p ON wr.id_player = p.id_player
                    LEFT JOIN tuning_setup_part tsp
                        ON wr.id_tuning_setup = tsp.id_tuning_setup
                    LEFT JOIN tuning_part tp ON tsp.id_tuning_part = tp.id_tuning_part
                    WHERE wr.current = 1
                    GROUP BY wr.id_record, wr.id_map, wr.id_vehicle, wr.id_player,
                        wr.id_tuning_setup, wr.distance, wr.current, wr.questionable,
                        wr.questionable_reason, m.name_map, v.name_vehicle,
                        p.name_player, p.country
                    ORDER BY m.name_map, v.name_vehicle
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
                        p.id_map AS "idMap",
                        p.id_vehicle AS "idVehicle",
                        p.distance,
                        p.player_name AS "playerName",
                        p.player_country AS "playerCountry",
                        p.tuning_parts AS "tuningParts",
                        p.submitter_ip AS "submitterIp",
                        p.status,
                        p.submitted_at,
                        m.name_map AS "mapName",
                        v.name_vehicle AS "vehicleName"
                    FROM pending_submission p
                    LEFT JOIN map m ON p.id_map = m.id_map
                    LEFT JOIN vehicle v ON p.id_vehicle = v.id_vehicle
                    WHERE p.status = 'pending'
                    ORDER BY p.submitted_at DESC, p.id DESC
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
                self._ensure_exists(cursor, "map", "id_map", payload.map_id, "Map not found.")
                self._ensure_exists(
                    cursor,
                    "vehicle",
                    "id_vehicle",
                    payload.vehicle_id,
                    "Vehicle not found.",
                )
                if payload.tuning_setup_id is not None:
                    self._ensure_exists(
                        cursor,
                        "tuning_setup",
                        "id_tuning_setup",
                        payload.tuning_setup_id,
                        "Tuning setup not found.",
                    )

                player_id = self._resolve_player(cursor, payload)

                cursor.execute(
                    "DELETE FROM world_record WHERE id_map = %s AND id_vehicle = %s",
                    (payload.map_id, payload.vehicle_id),
                )
                cursor.execute(
                    """
                    INSERT INTO world_record (
                        id_map, id_vehicle, id_player, distance, current,
                        id_tuning_setup, questionable, questionable_reason
                    )
                    VALUES (%s, %s, %s, %s, 1, %s, %s, %s)
                    RETURNING id_record
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
                record_id = cursor.fetchone()["id_record"]

                map_name = self._name_for(cursor, "map", "name_map", "id_map", payload.map_id)
                vehicle_name = self._name_for(
                    cursor,
                    "vehicle",
                    "name_vehicle",
                    "id_vehicle",
                    payload.vehicle_id,
                )
                player_name = self._name_for(
                    cursor,
                    "player",
                    "name_player",
                    "id_player",
                    player_id,
                )

        return {
            "success": True,
            "idRecord": record_id,
            "playerId": player_id,
            "mapName": map_name,
            "vehicleName": vehicle_name,
            "playerName": player_name,
            "distance": payload.distance,
        }

    def delete_record(self, payload: DeleteRecordRequest) -> dict[str, Any]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM world_record WHERE id_record = %s AND current = 1",
                    (payload.record_id,),
                )
                deleted = cursor.rowcount
        return {"success": True, "deleted": deleted}

    def set_questionable(self, payload: SetQuestionableRequest) -> dict[str, Any]:
        if payload.questionable not in (0, 1):
            raise AdminServiceError("Invalid questionable value (must be 0 or 1)")

        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM world_record WHERE id_record = %s AND current = 1 LIMIT 1",
                    (payload.record_id,),
                )
                if cursor.fetchone() is None:
                    raise AdminNotFoundError("Record not found")
                cursor.execute(
                    """
                    UPDATE world_record
                    SET questionable = %s, questionable_reason = %s
                    WHERE id_record = %s AND current = 1
                    """,
                    (payload.questionable, _clean_text(payload.note) or None, payload.record_id),
                )
        return {"success": True, "message": "Record status updated successfully"}

    def assign_setup(self, payload: AssignSetupRequest) -> dict[str, bool]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id_tuning_setup FROM world_record WHERE id_record = %s AND current = 1",
                    (payload.record_id,),
                )
                record = cursor.fetchone()
                if record is None:
                    raise AdminNotFoundError("Record not found")
                if record["id_tuning_setup"]:
                    raise AdminServiceError("Record already has a tuning setup assigned")

                self._ensure_exists(
                    cursor,
                    "tuning_setup",
                    "id_tuning_setup",
                    payload.tuning_setup_id,
                    "Tuning setup not found",
                )
                cursor.execute(
                    """
                    UPDATE world_record
                    SET id_tuning_setup = %s
                    WHERE id_record = %s AND current = 1
                    """,
                    (payload.tuning_setup_id, payload.record_id),
                )
        return {"success": True}

    def add_map(self, payload: AddMapRequest) -> dict[str, Any]:
        name = _clean_text(payload.map_name)
        if not name:
            raise AdminServiceError("Map name is required.")
        self._ensure_max_length(name, 19, "Map name must be 19 characters or fewer.")
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._ensure_unique_name(
                    cursor,
                    "map",
                    "name_map",
                    name,
                    "Map already exists in database.",
                )
                cursor.execute(
                    "INSERT INTO map (name_map) VALUES (%s) RETURNING id_map",
                    (name,),
                )
                new_id = cursor.fetchone()["id_map"]
        return {"success": True, "idMap": new_id, "nameMap": name, "iconMessage": ""}

    def add_vehicle(self, payload: AddVehicleRequest) -> dict[str, Any]:
        name = _clean_text(payload.vehicle_name)
        if not name:
            raise AdminServiceError("Vehicle name is required.")
        self._ensure_max_length(name, 16, "Vehicle name must be 16 characters or fewer.")
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._ensure_unique_name(
                    cursor,
                    "vehicle",
                    "name_vehicle",
                    name,
                    "Vehicle already exists in database.",
                )
                cursor.execute(
                    "INSERT INTO vehicle (name_vehicle) VALUES (%s) RETURNING id_vehicle",
                    (name,),
                )
                new_id = cursor.fetchone()["id_vehicle"]
        return {"success": True, "idVehicle": new_id, "nameVehicle": name, "iconMessage": ""}

    def add_tuning_part(self, payload: AddTuningPartRequest) -> dict[str, Any]:
        name = _clean_text(payload.part_name)
        if not name:
            raise AdminServiceError("Tuning part name is required.")
        self._ensure_max_length(name, 17, "Tuning part name must be 17 characters or fewer.")
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._ensure_unique_name(
                    cursor,
                    "tuning_part",
                    "name_tuning_part",
                    name,
                    "A tuning part with this name already exists.",
                )
                cursor.execute(
                    """
                    INSERT INTO tuning_part (name_tuning_part)
                    VALUES (%s)
                    RETURNING id_tuning_part
                    """,
                    (name,),
                )
                new_id = cursor.fetchone()["id_tuning_part"]
        return {"success": True, "idTuningPart": new_id, "nameTuningPart": name, "iconMessage": ""}

    def save_icon(
        self,
        folder: str,
        item_name: str,
        filename: str | None,
        content_type: str | None,
        content: bytes | None,
    ) -> str:
        if not content:
            return ""
        self._validate_svg_icon(filename, content_type, content)
        target_dir = REPO_ROOT / "frontend" / "public" / "img" / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{self._asset_slug(item_name)}.svg"
        target.write_bytes(content)
        return f"Icon uploaded: {target.name}"

    def validate_icon_upload(
        self,
        filename: str | None,
        content_type: str | None,
        content: bytes | None,
    ) -> None:
        if content:
            self._validate_svg_icon(filename, content_type, content)

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
                    "DELETE FROM world_record WHERE id_map = %s AND id_vehicle = %s",
                    (submission["id_map"], submission["id_vehicle"]),
                )

                player_id = self._find_or_create_player(
                    cursor,
                    _clean_text(submission.get("player_name")),
                    _clean_text(submission.get("player_country")),
                )
                cursor.execute(
                    """
                    INSERT INTO world_record (id_map, id_vehicle, id_player, distance, current)
                    VALUES (%s, %s, %s, %s, 1)
                    RETURNING id_record
                    """,
                    (
                        submission["id_map"],
                        submission["id_vehicle"],
                        player_id,
                        submission["distance"],
                    ),
                )
                record_id = cursor.fetchone()["id_record"]

                tuning_parts = _clean_text(submission.get("tuning_parts"))
                if tuning_parts:
                    part_ids = self._part_ids_from_names(cursor, tuning_parts)
                    if 3 <= len(part_ids) <= 4:
                        setup_id = self._create_setup(cursor, part_ids)
                        cursor.execute(
                            "UPDATE world_record SET id_tuning_setup = %s WHERE id_record = %s",
                            (setup_id, record_id),
                        )

                cursor.execute(
                    "UPDATE pending_submission SET status = 'approved' WHERE id = %s",
                    (submission_id,),
                )
        return {"success": True}

    def reject_submission(self, submission_id: int) -> dict[str, bool]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                self._get_pending_submission(cursor, submission_id)
                cursor.execute(
                    "UPDATE pending_submission SET status = 'rejected' WHERE id = %s",
                    (submission_id,),
                )
        return {"success": True}

    def post_news(self, payload: PostNewsRequest, author: str | None) -> dict[str, Any]:
        title = _strip_tags(payload.title)
        content = _strip_tags(payload.content)
        if not title or not content:
            raise AdminServiceError("Title and content are required.")
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO news (title, content, author)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (title, content, author or ""),
                )
                news_id = int(cursor.fetchone()["id"])
        return {"success": True, "id": news_id}

    def update_news(self, news_id: int, payload: UpdateNewsRequest) -> dict[str, Any]:
        title = _strip_tags(payload.title)
        content = _strip_tags(payload.content)
        if news_id <= 0 or not title or not content:
            raise AdminServiceError("News ID, title, and content are required.")
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE news SET title = %s, content = %s WHERE id = %s",
                    (title, content, news_id),
                )
        return {"success": True, "dryRun": False}

    def delete_news(self, payload: DeleteNewsRequest) -> dict[str, Any]:
        if payload.id <= 0:
            raise AdminServiceError("Invalid news ID.")
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM news WHERE id = %s", (payload.id,))
        return {"success": True, "dryRun": False}

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
                    "map",
                    "vehicle",
                    "player",
                    "tuning_part",
                    "tuning_setup",
                    "world_record",
                    "pending_submission",
                    "news",
                ):
                    cursor.execute(f"SELECT count(*) AS count FROM {table}")
                    counts[table] = int(cursor.fetchone()["count"])
        return {"ok": True, "result": ok, "counts": counts}

    def create_backup(self) -> dict[str, Any]:
        self._ensure_backups_dir()
        filename = self._next_backup_filename()
        target = self._backups_dir / filename

        with open_connection(self._config) as connection:
            dump = self._build_application_sql_dump(connection)

        target.write_text(dump, encoding="utf-8")
        try:
            target.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            # Windows may ignore POSIX-like permission bits; the file is still stored locally.
            pass

        info = self._backup_info(target)
        return {"success": True, "filename": info["name"], "backup": info}

    def list_backups(self) -> dict[str, list[dict[str, Any]]]:
        self._ensure_backups_dir()
        backups = [
            self._backup_info(path)
            for path in self._backups_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".sql"
        ]
        backups.sort(key=lambda item: str(item["mtime"]), reverse=True)
        return {"backups": backups}

    def delete_backup(self, filename: str) -> dict[str, bool]:
        path = self._safe_backup_path(filename)
        if not path.exists() or not path.is_file():
            raise AdminNotFoundError("Backup file not found.")
        path.unlink()
        return {"success": True}

    def backup_path(self, filename: str) -> Path:
        path = self._safe_backup_path(filename)
        if not path.exists() or not path.is_file():
            raise AdminNotFoundError("Backup file not found.")
        return path

    def _resolve_player(self, cursor: Any, payload: SubmitRecordRequest) -> int:
        if payload.player_id is not None:
            self._ensure_exists(
                cursor,
                "player",
                "id_player",
                payload.player_id,
                "Selected player does not exist.",
            )
            return payload.player_id

        new_name = _clean_text(payload.new_player_name or payload.player_name)
        if not new_name:
            raise AdminServiceError("No valid player selected or provided.")
        if not _clean_text(payload.country):
            raise AdminServiceError("Please provide a country for the new player.")
        self._ensure_max_length(new_name, 15, "Player name is too long for the database schema.")
        self._ensure_max_length(
            _clean_text(payload.country),
            32,
            "Country is too long for the database schema.",
        )
        return self._find_or_create_player(cursor, new_name, _clean_text(payload.country))

    def _find_or_create_player(self, cursor: Any, name: str, country: str) -> int:
        if not name:
            raise AdminServiceError("No valid player selected or provided.")
        self._ensure_max_length(name, 15, "Player name is too long for the database schema.")
        self._ensure_max_length(country, 32, "Country is too long for the database schema.")
        cursor.execute("SELECT id_player FROM player WHERE name_player = %s LIMIT 1", (name,))
        existing = cursor.fetchone()
        if existing:
            return int(existing["id_player"])
        cursor.execute(
            "INSERT INTO player (name_player, country) VALUES (%s, %s) RETURNING id_player",
            (name, country or ""),
        )
        return int(cursor.fetchone()["id_player"])

    def _get_pending_submission(self, cursor: Any, submission_id: int) -> dict[str, Any]:
        cursor.execute(
            "SELECT * FROM pending_submission WHERE id = %s LIMIT 1",
            (submission_id,),
        )
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
                "SELECT id_tuning_part FROM tuning_part WHERE name_tuning_part = %s LIMIT 1",
                (name,),
            )
            row = cursor.fetchone()
            if row is None:
                return []
            part_ids.append(int(row["id_tuning_part"]))
        return sorted(part_ids)

    def _ensure_parts_exist(self, cursor: Any, part_ids: list[int]) -> None:
        cursor.execute(
            """
            SELECT id_tuning_part
            FROM tuning_part
            WHERE id_tuning_part = ANY(%s::int[])
            """,
            (part_ids,),
        )
        found = {int(row["id_tuning_part"]) for row in cursor.fetchall()}
        missing = [part_id for part_id in part_ids if part_id not in found]
        if missing:
            raise AdminNotFoundError(f"Tuning part not found: {missing[0]}")

    def _find_setup_by_parts(self, cursor: Any, part_ids: list[int]) -> int | None:
        cursor.execute(
            """
            SELECT id_tuning_setup
            FROM (
                SELECT
                    id_tuning_setup,
                    array_agg(id_tuning_part ORDER BY id_tuning_part) AS part_ids
                FROM tuning_setup_part
                GROUP BY id_tuning_setup
            ) grouped
            WHERE part_ids = %s::int[]
            LIMIT 1
            """,
            (part_ids,),
        )
        row = cursor.fetchone()
        return int(row["id_tuning_setup"]) if row else None

    def _create_setup(self, cursor: Any, part_ids: list[int]) -> int:
        cursor.execute("INSERT INTO tuning_setup DEFAULT VALUES RETURNING id_tuning_setup")
        setup_id = int(cursor.fetchone()["id_tuning_setup"])
        for part_id in part_ids:
            cursor.execute(
                """
                INSERT INTO tuning_setup_part (id_tuning_setup, id_tuning_part)
                VALUES (%s, %s)
                """,
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

    def _ensure_max_length(self, value: str, max_length: int, message: str) -> None:
        if len(value) > max_length:
            raise AdminServiceError(message)

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

    def _validate_svg_icon(
        self,
        filename: str | None,
        content_type: str | None,
        content: bytes,
    ) -> None:
        if len(content) > 500_000:
            raise AdminServiceError("Icon file is too large.")
        if filename and not filename.lower().endswith(".svg"):
            raise AdminUnsupportedMediaError("Only SVG icon uploads are supported.")
        if content_type and content_type not in {"image/svg+xml", "application/octet-stream"}:
            raise AdminUnsupportedMediaError("Only SVG icon uploads are supported.")
        preview = content[:1024].lstrip().lower()
        if b"<svg" not in preview and not preview.startswith(b"<?xml"):
            raise AdminUnsupportedMediaError("The uploaded icon does not look like an SVG file.")

    def _asset_slug(self, name: str) -> str:
        slug = re.sub(r"\s+", "_", name.strip().lower())
        slug = re.sub(r"[^a-z0-9_-]", "", slug)
        if not slug:
            raise AdminServiceError("Icon filename could not be generated.")
        return slug

    def _ensure_backups_dir(self) -> None:
        self._backups_dir.mkdir(mode=0o750, parents=True, exist_ok=True)

    def _next_backup_filename(self) -> str:
        from datetime import UTC, datetime

        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        candidate = f"hcr2-backup-{stamp}.sql"
        counter = 1
        while (self._backups_dir / candidate).exists():
            counter += 1
            candidate = f"hcr2-backup-{stamp}-{counter}.sql"
        return candidate

    def _safe_backup_path(self, filename: str) -> Path:
        self._ensure_backups_dir()
        name = Path(filename).name
        if not name or name != filename or not name.endswith(".sql"):
            raise AdminServiceError("Invalid backup filename.")
        path = (self._backups_dir / name).resolve()
        backups_root = self._backups_dir.resolve()
        if backups_root not in path.parents and path != backups_root:
            raise AdminServiceError("Invalid backup filename.")
        return path

    def _backup_info(self, path: Path) -> dict[str, Any]:
        from datetime import datetime

        stat_result = path.stat()
        return {
            "name": path.name,
            "size": stat_result.st_size,
            "mtime": datetime.fromtimestamp(stat_result.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _build_application_sql_dump(self, connection: Any) -> str:
        lines = [
            "-- HCR2 application data backup generated by the FastAPI admin.",
            "-- This backup contains application tables only.",
            "-- It does not include roles, extensions, or server settings.",
            "BEGIN;",
            "SET CONSTRAINTS ALL DEFERRED;",
            (
                "TRUNCATE TABLE "
                f"{', '.join(self._quote_ident(table) for table in self._backup_tables)} "
                "RESTART IDENTITY CASCADE;"
            ),
        ]

        with connection.cursor() as cursor:
            for table in self._backup_tables:
                cursor.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = current_schema() AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (table,),
                )
                columns = [str(row["column_name"]) for row in cursor.fetchall()]
                if not columns:
                    continue

                column_sql = ", ".join(self._quote_ident(column) for column in columns)
                cursor.execute(f"SELECT {column_sql} FROM {self._quote_ident(table)}")
                rows = cursor.fetchall()
                if not rows:
                    continue

                lines.append("")
                lines.append(f"-- Data for {table}")
                for row in rows:
                    values = ", ".join(
                        sql.Literal(row[column]).as_string(connection)
                        for column in columns
                    )
                    lines.append(
                        f"INSERT INTO {self._quote_ident(table)} "
                        f"({column_sql}) VALUES ({values});"
                    )

        lines.append("")
        lines.append("-- Sequence positions")
        for table, (sequence, column) in self._backup_sequences.items():
            quoted_table = self._quote_ident(table)
            quoted_column = self._quote_ident(column)
            lines.append(
                "SELECT setval("
                f"'{sequence}', "
                f"COALESCE((SELECT MAX({quoted_column}) FROM {quoted_table}), 1), "
                f"EXISTS (SELECT 1 FROM {quoted_table})"
                ");"
            )

        lines.extend(["COMMIT;", ""])
        return "\n".join(lines)

    def _quote_ident(self, name: str) -> str:
        return '"' + name.replace('"', '""') + '"'


def maintenance_flag_path() -> Path:
    return REPO_ROOT / "MAINTENANCE"
