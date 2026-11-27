import json
from datetime import datetime
from typing import Any, Protocol

from app.core.progression_rules import level_summary
from app.db.session import DatabaseConfig, open_connection
from app.repositories.badge import (
    award_badge_cursor,
    revoke_badge_cursor,
    upsert_badge_progress_cursor,
)


class ProgressionError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _row(cursor: Any) -> dict[str, Any] | None:
    value = cursor.fetchone()
    return dict(value) if value is not None else None


def _int_config(config: dict[str, Any], key: str, default: int) -> int:
    try:
        value = int(config.get(key, default))
    except (TypeError, ValueError):
        return default
    return max(1, value)


def _metric(
    cursor: Any,
    community_user_id: int,
    requirement_type: str | None,
    config: dict[str, Any],
) -> tuple[int, int]:
    """Return (current value, target) for an automatic requirement."""
    if requirement_type in {
        "world_records_current_count",
        "world_records_ever_count",
    }:
        current_only = requirement_type == "world_records_current_count"
        cursor.execute(
            """
            SELECT COUNT(DISTINCT wr.id_record) AS value
            FROM world_record wr
            JOIN hcr2_account_link l
              ON l.player_id = wr.id_player AND l.status = 'active'
            WHERE l.community_user_id = %(user_id)s
              AND COALESCE(wr.questionable, 0) = 0
              AND (%(current_only)s = FALSE OR wr.current = 1)
            """,
            {"user_id": community_user_id, "current_only": current_only},
        )
        return int(_row(cursor)["value"]), _int_config(config, "count", 1)
    if requirement_type == "approved_submissions_count":
        cursor.execute(
            """
            SELECT COUNT(*) AS value FROM pending_submission
            WHERE submitter_community_user_id = %(user_id)s AND status = 'approved'
            """,
            {"user_id": community_user_id},
        )
        return int(_row(cursor)["value"]), _int_config(config, "count", 1)
    if requirement_type == "hcr2_identity_verified":
        cursor.execute(
            """
            SELECT COUNT(*) AS value FROM hcr2_account_link
            WHERE community_user_id = %(user_id)s AND status = 'active'
            """,
            {"user_id": community_user_id},
        )
        return int(_row(cursor)["value"]), 1
    if requirement_type == "membership_duration_days":
        cursor.execute(
            "SELECT created_at FROM community_user WHERE id = %(user_id)s",
            {"user_id": community_user_id},
        )
        account = _row(cursor)
        if account is None:
            return 0, _int_config(config, "days", 365)
        days = int((datetime.now() - account["created_at"]).total_seconds() // 86400)
        return max(0, days), _int_config(config, "days", 365)
    if requirement_type == "xp_total":
        cursor.execute(
            "SELECT total_xp FROM community_progression WHERE community_user_id = %(user_id)s",
            {"user_id": community_user_id},
        )
        row = _row(cursor)
        return int(row["total_xp"]) if row else 0, _int_config(config, "amount", 500)
    return 0, 1


def _evaluate_automatic_badges_cursor(
    cursor: Any,
    *,
    community_user_id: int,
    event_key: str | None,
) -> dict[str, list[dict[str, Any]]]:
    cursor.execute(
        """
        SELECT b.id, b.identifier, b.name, b.requirement_type, b.requirement_config, b.permanent
        FROM badge b
        WHERE b.award_method = 'automatic' AND b.enabled = TRUE AND b.archived_at IS NULL
          AND b.requirement_type IS NOT NULL
        ORDER BY b.sort_order, b.id
        """
    )
    definitions = [dict(row) for row in cursor.fetchall()]
    awarded: list[dict[str, Any]] = []
    revoked: list[dict[str, Any]] = []
    for definition in definitions:
        value, target = _metric(
            cursor,
            community_user_id,
            definition["requirement_type"],
            definition["requirement_config"] or {},
        )
        upsert_badge_progress_cursor(
            cursor,
            community_user_id=community_user_id,
            badge_id=definition["id"],
            progress_value=value,
            target_value=target,
        )
        if value >= target:
            badge_event_key = f"badge:{event_key}:{definition['id']}" if event_key else None
            awarded_badge, created = award_badge_cursor(
                cursor,
                community_user_id=community_user_id,
                badge_id=definition["id"],
                source="automatic",
                actor=None,
                reason=f"Requirement met: {value}/{target}",
                public_reason=None,
                event_key=badge_event_key,
            )
            if created and awarded_badge is not None:
                awarded.append(awarded_badge)
            continue
        if not definition["permanent"]:
            cursor.execute(
                """
                SELECT ub.id FROM community_user_badge ub
                WHERE ub.community_user_id = %(user_id)s AND ub.badge_id = %(badge_id)s
                  AND ub.active = TRUE
                """,
                {"user_id": community_user_id, "badge_id": definition["id"]},
            )
            row = _row(cursor)
            if row is not None:
                revoke_event_key = f"revoke:{event_key}:{definition['id']}" if event_key else None
                removed = revoke_badge_cursor(
                    cursor,
                    user_badge_id=row["id"],
                    actor="system",
                    reason=f"Requirement no longer met: {value}/{target}",
                    event_key=revoke_event_key,
                )
                if removed is not None:
                    revoked.append(removed)
    return {"awarded": awarded, "revoked": revoked}


class ProgressionRepository(Protocol):
    def process_event(
        self,
        *,
        event_key: str,
        community_user_id: int,
        event_type: str,
        payload: dict[str, Any],
        xp_amount: int,
        xp_reason: str,
        level_divisor: int,
    ) -> dict[str, Any]: ...

    def get_summary(self, community_user_id: int, level_divisor: int) -> dict[str, Any]: ...

    def list_transactions(
        self,
        community_user_id: int,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]: ...

    def refresh_badges(self, community_user_id: int) -> dict[str, list[dict[str, Any]]]: ...

    def claim_evaluation(self, community_user_id: int, requirement_type: str) -> bool: ...

    def list_evaluations(
        self,
        *,
        community_user_id: int | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]: ...

    def user_exists(self, community_user_id: int) -> bool: ...


class PostgresProgressionRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def user_exists(self, community_user_id: int) -> bool:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM community_user WHERE id = %(user_id)s",
                    {"user_id": community_user_id},
                )
                return cursor.fetchone() is not None

    def process_event(
        self,
        *,
        event_key: str,
        community_user_id: int,
        event_type: str,
        payload: dict[str, Any],
        xp_amount: int,
        xp_reason: str,
        level_divisor: int,
    ) -> dict[str, Any]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM progression_event WHERE event_key = %(key)s",
                    {"key": event_key},
                )
                if cursor.fetchone() is not None:
                    return {"duplicate": True, "event_key": event_key}
                cursor.execute(
                    "SELECT 1 FROM community_user WHERE id = %(user_id)s",
                    {"user_id": community_user_id},
                )
                if cursor.fetchone() is None:
                    return {"ignored": True, "reason": "unknown_user"}

                before = self._summary_cursor(cursor, community_user_id, level_divisor)
                cursor.execute(
                    """
                    INSERT INTO progression_event
                        (event_key, community_user_id, event_type, payload, status, processed_at)
                    VALUES
                        (%(key)s, %(user_id)s, %(event_type)s, %(payload)s::jsonb,
                         'processed', CURRENT_TIMESTAMP)
                    """,
                    {
                        "key": event_key,
                        "user_id": community_user_id,
                        "event_type": event_type,
                        "payload": json.dumps(payload),
                    },
                )
                amount = int(xp_amount)
                if amount != 0:
                    cursor.execute(
                        """
                        SELECT total_xp FROM community_progression
                        WHERE community_user_id = %(user_id)s FOR UPDATE
                        """,
                        {"user_id": community_user_id},
                    )
                    row = _row(cursor)
                    current = int(row["total_xp"]) if row else 0
                    if current + amount < 0:
                        raise ProgressionError("XP adjustment would make total XP negative.")
                    cursor.execute(
                        """
                        INSERT INTO community_progression (community_user_id, total_xp)
                        VALUES (%(user_id)s, %(amount)s)
                        ON CONFLICT (community_user_id) DO UPDATE SET
                            total_xp = community_progression.total_xp + %(amount)s,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        {"user_id": community_user_id, "amount": amount},
                    )
                    cursor.execute(
                        """
                        INSERT INTO xp_transaction
                            (community_user_id, amount, event_type, event_key, reason, actor)
                        VALUES
                            (%(user_id)s, %(amount)s, %(event_type)s, %(key)s,
                             %(reason)s, %(actor)s)
                        """,
                        {
                            "user_id": community_user_id,
                            "amount": amount,
                            "event_type": event_type,
                            "key": event_key,
                            "reason": xp_reason,
                            "actor": payload.get("actor"),
                        },
                    )
                after = self._summary_cursor(cursor, community_user_id, level_divisor)
                changes = _evaluate_automatic_badges_cursor(
                    cursor,
                    community_user_id=community_user_id,
                    event_key=event_key,
                )
                connection.commit()
        return {
            "duplicate": False,
            "event_key": event_key,
            "xp_awarded": amount,
            "level_before": before["level"],
            "level_after": after["level"],
            **changes,
        }

    def _summary_cursor(
        self,
        cursor: Any,
        community_user_id: int,
        level_divisor: int,
    ) -> dict[str, Any]:
        cursor.execute(
            "SELECT total_xp FROM community_progression WHERE community_user_id = %(user_id)s",
            {"user_id": community_user_id},
        )
        row = _row(cursor)
        total = int(row["total_xp"]) if row else 0
        return level_summary(total, level_divisor)

    def get_summary(self, community_user_id: int, level_divisor: int) -> dict[str, Any]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                return self._summary_cursor(cursor, community_user_id, level_divisor)

    def list_transactions(
        self,
        community_user_id: int,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        params = {"user_id": community_user_id, "limit": limit, "offset": offset}
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS count FROM xp_transaction
                    WHERE community_user_id = %(user_id)s
                    """,
                    params,
                )
                total = int(cursor.fetchone()["count"])
                cursor.execute(
                    """
                    SELECT id, amount, event_type, event_key, reason, actor, created_at
                    FROM xp_transaction
                    WHERE community_user_id = %(user_id)s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    params,
                )
                return [dict(row) for row in cursor.fetchall()], total

    def refresh_badges(self, community_user_id: int) -> dict[str, list[dict[str, Any]]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                changes = _evaluate_automatic_badges_cursor(
                    cursor,
                    community_user_id=community_user_id,
                    event_key=None,
                )
                connection.commit()
                return changes

    def claim_evaluation(self, community_user_id: int, requirement_type: str) -> bool:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO progression_evaluation
                        (community_user_id, requirement_type)
                    VALUES (%(user_id)s, %(requirement)s)
                    ON CONFLICT DO NOTHING
                    RETURNING community_user_id
                    """,
                    {"user_id": community_user_id, "requirement": requirement_type},
                )
                return cursor.fetchone() is not None

    def list_evaluations(
        self,
        *,
        community_user_id: int | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        where = "WHERE community_user_id = %(user_id)s" if community_user_id is not None else ""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if community_user_id is not None:
            params["user_id"] = community_user_id
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT COUNT(*) AS count FROM progression_evaluation {where}",
                    params,
                )
                total = int(cursor.fetchone()["count"])
                cursor.execute(
                    f"""
                    SELECT community_user_id, requirement_type, evaluated_on, created_at
                    FROM progression_evaluation
                    {where}
                    ORDER BY evaluated_on DESC, created_at DESC
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    params,
                )
                return {
                    "evaluations": [dict(row) for row in cursor.fetchall()],
                    "count": total,
                    "limit": limit,
                    "offset": offset,
                }
