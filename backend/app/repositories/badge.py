from typing import Any, Protocol

import psycopg

from app.db.session import DatabaseConfig, open_connection

BADGE_COLUMNS = """
    b.id, b.identifier, b.category_id, c.identifier AS category_identifier,
    c.name AS category_name, b.name, b.description, b.icon_path, b.badge_type,
    b.award_method, b.rarity, b.requirement_type, b.requirement_config,
    b.enabled, b.hidden_until_unlocked, b.revocable, b.featureable, b.permanent,
    b.archived_at, b.expires_at, b.discord_role_id, b.discord_sync_enabled,
    b.sort_order, b.created_at, b.updated_at
"""

USER_BADGE_COLUMNS = """
    ub.id, ub.community_user_id, ub.badge_id, b.identifier AS badge_identifier,
    b.name AS badge_name, b.description AS badge_description, b.icon_path,
    b.badge_type, b.category_identifier, b.category_name, b.rarity,
    b.featureable, b.hidden_until_unlocked, ub.active, ub.source, ub.awarded_at,
    ub.awarded_by, ub.reason, ub.public_reason, ub.expires_at, ub.revoked_at,
    ub.revoked_by, ub.revocation_reason
"""

CATEGORY_COLUMNS = """
    id, identifier, name, description, sort_order, enabled, created_at
"""


class BadgeError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _row(cursor: Any) -> dict[str, Any] | None:
    value = cursor.fetchone()
    return dict(value) if value is not None else None


def _definition_columns() -> list[str]:
    return [
        "identifier",
        "category_id",
        "name",
        "description",
        "icon_path",
        "badge_type",
        "award_method",
        "rarity",
        "requirement_type",
        "requirement_config",
        "enabled",
        "hidden_until_unlocked",
        "revocable",
        "featureable",
        "permanent",
        "expires_at",
        "discord_role_id",
        "discord_sync_enabled",
        "sort_order",
    ]


def award_badge_cursor(
    cursor: Any,
    *,
    community_user_id: int,
    badge_id: int,
    source: str,
    actor: str | None,
    reason: str | None,
    public_reason: str | None,
    event_key: str | None = None,
) -> tuple[dict[str, Any] | None, bool]:
    cursor.execute(
        f"""
        SELECT {USER_BADGE_COLUMNS}
        FROM community_user_badge ub
        JOIN badge b ON b.id = ub.badge_id
        JOIN badge_category c ON c.id = b.category_id
        WHERE ub.community_user_id = %(user_id)s AND ub.badge_id = %(badge_id)s
        FOR UPDATE OF ub
        """,
        {"user_id": community_user_id, "badge_id": badge_id},
    )
    existing = _row(cursor)
    if existing is not None and existing["active"] and not existing["expires_at"]:
        return existing, False
    if existing is not None and existing["active"] and existing["expires_at"]:
        from datetime import datetime

        if existing["expires_at"] > datetime.now(existing["expires_at"].tzinfo):
            return existing, False

    cursor.execute(
        "SELECT expires_at, enabled, archived_at FROM badge WHERE id = %(badge_id)s",
        {"badge_id": badge_id},
    )
    definition = _row(cursor)
    if definition is None or not definition["enabled"] or definition["archived_at"] is not None:
        raise BadgeError("Badge is not available.", 409)

    params = {
        "user_id": community_user_id,
        "badge_id": badge_id,
        "source": source,
        "actor": actor,
        "reason": reason,
        "public_reason": public_reason,
        "expires_at": definition["expires_at"],
        "event_key": event_key,
    }
    if existing is None:
        cursor.execute(
            """
            INSERT INTO community_user_badge
                (community_user_id, badge_id, source, awarded_at, awarded_by,
                 reason, public_reason, expires_at)
            VALUES
                (%(user_id)s, %(badge_id)s, %(source)s, CURRENT_TIMESTAMP, %(actor)s,
                 %(reason)s, %(public_reason)s, %(expires_at)s)
            RETURNING id
            """,
            params,
        )
    else:
        cursor.execute(
            """
            UPDATE community_user_badge SET
                active = TRUE,
                source = %(source)s,
                awarded_at = CURRENT_TIMESTAMP,
                awarded_by = %(actor)s,
                reason = %(reason)s,
                public_reason = %(public_reason)s,
                expires_at = %(expires_at)s,
                revoked_at = NULL,
                revoked_by = NULL,
                revocation_reason = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %(user_badge_id)s
            RETURNING id
            """,
            {**params, "user_badge_id": existing["id"]},
        )
    user_badge_id = int(cursor.fetchone()["id"])
    cursor.execute(
        """
        INSERT INTO badge_award_history
            (user_badge_id, community_user_id, badge_id, action, actor, reason, event_key)
        VALUES
            (%(user_badge_id)s, %(user_id)s, %(badge_id)s, 'awarded', %(actor)s,
             %(reason)s, %(event_key)s)
        """,
        {**params, "user_badge_id": user_badge_id},
    )
    cursor.execute(
        f"""
        SELECT {USER_BADGE_COLUMNS}
        FROM community_user_badge ub
        JOIN badge b ON b.id = ub.badge_id
        JOIN badge_category c ON c.id = b.category_id
        WHERE ub.id = %(user_badge_id)s
        """,
        {"user_badge_id": user_badge_id},
    )
    return _row(cursor), True


def revoke_badge_cursor(
    cursor: Any,
    *,
    user_badge_id: int,
    actor: str,
    reason: str,
    event_key: str | None = None,
) -> dict[str, Any] | None:
    cursor.execute(
        f"""
        SELECT {USER_BADGE_COLUMNS}, b.revocable
        FROM community_user_badge ub
        JOIN badge b ON b.id = ub.badge_id
        JOIN badge_category c ON c.id = b.category_id
        WHERE ub.id = %(user_badge_id)s
        FOR UPDATE OF ub
        """,
        {"user_badge_id": user_badge_id},
    )
    row = _row(cursor)
    if row is None or not row["active"]:
        return None
    if not row["revocable"]:
        raise BadgeError("This badge cannot be revoked.", 409)
    cursor.execute(
        """
        UPDATE community_user_badge SET
            active = FALSE, revoked_at = CURRENT_TIMESTAMP, revoked_by = %(actor)s,
            revocation_reason = %(reason)s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %(user_badge_id)s
        """,
        {"user_badge_id": user_badge_id, "actor": actor, "reason": reason},
    )
    cursor.execute("DELETE FROM featured_badge WHERE user_badge_id = %(id)s", {"id": user_badge_id})
    cursor.execute(
        """
        INSERT INTO badge_award_history
            (user_badge_id, community_user_id, badge_id, action, actor, reason, event_key)
        VALUES
            (%(user_badge_id)s, %(user_id)s, %(badge_id)s, 'revoked', %(actor)s,
             %(reason)s, %(event_key)s)
        """,
        {
            "user_badge_id": user_badge_id,
            "user_id": row["community_user_id"],
            "badge_id": row["badge_id"],
            "actor": actor,
            "reason": reason,
            "event_key": event_key,
        },
    )
    return row


def upsert_badge_progress_cursor(
    cursor: Any,
    *,
    community_user_id: int,
    badge_id: int,
    progress_value: int,
    target_value: int,
) -> None:
    cursor.execute(
        """
        INSERT INTO badge_progress (community_user_id, badge_id, progress_value, target_value)
        VALUES (%(user_id)s, %(badge_id)s, %(value)s, %(target)s)
        ON CONFLICT (community_user_id, badge_id) DO UPDATE SET
            progress_value = EXCLUDED.progress_value,
            target_value = EXCLUDED.target_value,
            updated_at = CURRENT_TIMESTAMP
        """,
        {
            "user_id": community_user_id,
            "badge_id": badge_id,
            "value": max(0, int(progress_value)),
            "target": max(1, int(target_value)),
        },
    )


class BadgeRepository(Protocol):
    def list_categories(self, include_disabled: bool = False) -> list[dict[str, Any]]: ...

    def create_category(self, payload: Any) -> dict[str, Any]: ...

    def update_category(self, category_id: int, payload: Any) -> dict[str, Any] | None: ...

    def list_definitions(
        self,
        *,
        category: str | None = None,
        badge_type: str | None = None,
        include_admin: bool = False,
    ) -> list[dict[str, Any]]: ...

    def get_definition(self, badge_id: int) -> dict[str, Any] | None: ...

    def get_definition_by_identifier(self, identifier: str) -> dict[str, Any] | None: ...

    def create_definition(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def update_definition(
        self,
        badge_id: int,
        changes: dict[str, Any],
    ) -> dict[str, Any] | None: ...

    def archive_definition(self, badge_id: int) -> dict[str, Any] | None: ...

    def list_user_badges(
        self,
        community_user_id: int,
        *,
        active_only: bool = True,
    ) -> list[dict[str, Any]]: ...

    def get_user_badge(self, user_badge_id: int) -> dict[str, Any] | None: ...

    def get_user_badge_by_badge(
        self,
        community_user_id: int,
        badge_id: int,
    ) -> dict[str, Any] | None: ...

    def award_badge(
        self,
        *,
        community_user_id: int,
        badge_id: int,
        source: str,
        actor: str | None,
        reason: str | None,
        public_reason: str | None,
        event_key: str | None = None,
    ) -> tuple[dict[str, Any] | None, bool]: ...

    def revoke_badge(
        self,
        *,
        user_badge_id: int,
        actor: str,
        reason: str,
    ) -> dict[str, Any] | None: ...

    def list_featured(self, community_user_id: int) -> list[dict[str, Any]]: ...

    def replace_featured(
        self,
        community_user_id: int,
        user_badge_ids: list[int],
    ) -> list[dict[str, Any]]: ...

    def list_progress(self, community_user_id: int) -> list[dict[str, Any]]: ...

    def list_history(
        self,
        *,
        community_user_id: int | None,
        badge_id: int | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]: ...


class PostgresBadgeRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    def list_categories(self, include_disabled: bool = False) -> list[dict[str, Any]]:
        where = "" if include_disabled else "WHERE enabled = TRUE"
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {CATEGORY_COLUMNS} FROM badge_category
                    {where} ORDER BY sort_order, id
                    """
                )
                return [dict(row) for row in cursor.fetchall()]

    def create_category(self, payload: Any) -> dict[str, Any]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        f"""
                        INSERT INTO badge_category (identifier, name, description, sort_order)
                        VALUES (%(identifier)s, %(name)s, %(description)s, %(sort_order)s)
                        RETURNING {CATEGORY_COLUMNS}
                        """,
                        payload.model_dump(),
                    )
                except psycopg.errors.UniqueViolation:
                    raise BadgeError("Category identifier is already in use.", 409) from None
                return _row(cursor)

    def update_category(self, category_id: int, payload: Any) -> dict[str, Any] | None:
        changes = {
            key: value
            for key, value in payload.model_dump(exclude_unset=True).items()
            if value is not None
        }
        if not changes:
            return self.get_category(category_id)
        assignments = ", ".join(f"{key} = %({key})s" for key in changes)
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE badge_category SET {assignments}
                    WHERE id = %(id)s RETURNING {CATEGORY_COLUMNS}
                    """,
                    {**changes, "id": category_id},
                )
                return _row(cursor)

    def get_category(self, category_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT {CATEGORY_COLUMNS} FROM badge_category WHERE id = %(id)s",
                    {"id": category_id},
                )
                return _row(cursor)

    def list_definitions(
        self,
        *,
        category: str | None = None,
        badge_type: str | None = None,
        include_admin: bool = False,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: dict[str, Any] = {}
        if not include_admin:
            clauses.extend(["b.enabled = TRUE", "b.archived_at IS NULL"])
        if category:
            clauses.append("c.identifier = %(category)s")
            params["category"] = category
        if badge_type:
            clauses.append("b.badge_type = %(badge_type)s")
            params["badge_type"] = badge_type
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {BADGE_COLUMNS}
                    FROM badge b JOIN badge_category c ON c.id = b.category_id
                    {where}
                    ORDER BY c.sort_order, b.sort_order, b.id
                    """,
                    params,
                )
                return [dict(row) for row in cursor.fetchall()]

    def get_definition(self, badge_id: int) -> dict[str, Any] | None:
        return self._definition_by("b.id", badge_id)

    def get_definition_by_identifier(self, identifier: str) -> dict[str, Any] | None:
        return self._definition_by("b.identifier", identifier)

    def _definition_by(self, column: str, value: Any) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {BADGE_COLUMNS}
                    FROM badge b JOIN badge_category c ON c.id = b.category_id
                    WHERE {column} = %(value)s
                    """,
                    {"value": value},
                )
                return _row(cursor)

    def create_definition(self, payload: dict[str, Any]) -> dict[str, Any]:
        columns = _definition_columns()
        assignments = ", ".join(columns)
        placeholders = ", ".join(f"%({key})s" for key in columns)
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        f"""
                        INSERT INTO badge ({assignments})
                        VALUES ({placeholders})
                        RETURNING {BADGE_COLUMNS}
                        """,
                        payload,
                    )
                except psycopg.errors.UniqueViolation:
                    raise BadgeError("Badge identifier is already in use.", 409) from None
                return _row(cursor)

    def update_definition(self, badge_id: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        if not changes:
            return self.get_definition(badge_id)
        assignments = ", ".join(f"{key} = %({key})s" for key in changes)
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        f"""
                        UPDATE badge SET {assignments}, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %(id)s
                        RETURNING {BADGE_COLUMNS}
                        """,
                        {**changes, "id": badge_id},
                    )
                except psycopg.errors.UniqueViolation:
                    raise BadgeError("Badge identifier is already in use.", 409) from None
                return _row(cursor)

    def archive_definition(self, badge_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE badge SET archived_at = CURRENT_TIMESTAMP, enabled = FALSE,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %(id)s RETURNING {BADGE_COLUMNS}
                    """,
                    {"id": badge_id},
                )
                return _row(cursor)

    def list_user_badges(
        self,
        community_user_id: int,
        *,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        clause = "AND ub.active = TRUE" if active_only else ""
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {USER_BADGE_COLUMNS}
                    FROM community_user_badge ub
                    JOIN badge b ON b.id = ub.badge_id
                    JOIN badge_category c ON c.id = b.category_id
                    WHERE ub.community_user_id = %(user_id)s {clause}
                    ORDER BY c.sort_order, b.sort_order, ub.awarded_at DESC, ub.id DESC
                    """,
                    {"user_id": community_user_id},
                )
                return [dict(row) for row in cursor.fetchall()]

    def get_user_badge(self, user_badge_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {USER_BADGE_COLUMNS}
                    FROM community_user_badge ub
                    JOIN badge b ON b.id = ub.badge_id
                    JOIN badge_category c ON c.id = b.category_id
                    WHERE ub.id = %(id)s
                    """,
                    {"id": user_badge_id},
                )
                return _row(cursor)

    def get_user_badge_by_badge(
        self,
        community_user_id: int,
        badge_id: int,
    ) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {USER_BADGE_COLUMNS}
                    FROM community_user_badge ub
                    JOIN badge b ON b.id = ub.badge_id
                    JOIN badge_category c ON c.id = b.category_id
                    WHERE ub.community_user_id = %(user_id)s AND ub.badge_id = %(badge_id)s
                    """,
                    {"user_id": community_user_id, "badge_id": badge_id},
                )
                return _row(cursor)

    def award_badge(
        self,
        *,
        community_user_id: int,
        badge_id: int,
        source: str,
        actor: str | None,
        reason: str | None,
        public_reason: str | None,
        event_key: str | None = None,
    ) -> tuple[dict[str, Any] | None, bool]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                result = award_badge_cursor(
                    cursor,
                    community_user_id=community_user_id,
                    badge_id=badge_id,
                    source=source,
                    actor=actor,
                    reason=reason,
                    public_reason=public_reason,
                    event_key=event_key,
                )
                connection.commit()
                return result

    def revoke_badge(
        self,
        *,
        user_badge_id: int,
        actor: str,
        reason: str,
    ) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                result = revoke_badge_cursor(
                    cursor,
                    user_badge_id=user_badge_id,
                    actor=actor,
                    reason=reason,
                )
                connection.commit()
                return result

    def list_featured(self, community_user_id: int) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT f.position, {USER_BADGE_COLUMNS}
                    FROM featured_badge f
                    JOIN community_user_badge ub ON ub.id = f.user_badge_id
                    JOIN badge b ON b.id = ub.badge_id
                    JOIN badge_category c ON c.id = b.category_id
                    WHERE f.community_user_id = %(user_id)s AND ub.active = TRUE
                    ORDER BY f.position
                    """,
                    {"user_id": community_user_id},
                )
                return [dict(row) for row in cursor.fetchall()]

    def replace_featured(
        self,
        community_user_id: int,
        user_badge_ids: list[int],
    ) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM featured_badge WHERE community_user_id = %(user_id)s",
                    {"user_id": community_user_id},
                )
                for position, user_badge_id in enumerate(user_badge_ids, start=1):
                    cursor.execute(
                        "SELECT badge_id FROM community_user_badge WHERE id = %(id)s",
                        {"id": user_badge_id},
                    )
                    row = _row(cursor)
                    cursor.execute(
                        """
                        INSERT INTO featured_badge
                            (community_user_id, user_badge_id, badge_id, position)
                        VALUES (%(user_id)s, %(user_badge_id)s, %(badge_id)s, %(position)s)
                        """,
                        {
                            "user_id": community_user_id,
                            "user_badge_id": user_badge_id,
                            "badge_id": row["badge_id"] if row else None,
                            "position": position,
                        },
                    )
                connection.commit()
        return self.list_featured(community_user_id)

    def list_progress(self, community_user_id: int) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT p.badge_id, b.identifier, p.progress_value, p.target_value,
                           p.updated_at
                    FROM badge_progress p JOIN badge b ON b.id = p.badge_id
                    WHERE p.community_user_id = %(user_id)s
                    ORDER BY b.sort_order, b.id
                    """,
                    {"user_id": community_user_id},
                )
                return [dict(row) for row in cursor.fetchall()]

    def list_history(
        self,
        *,
        community_user_id: int | None,
        badge_id: int | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if community_user_id is not None:
            clauses.append("h.community_user_id = %(user_id)s")
            params["user_id"] = community_user_id
        if badge_id is not None:
            clauses.append("h.badge_id = %(badge_id)s")
            params["badge_id"] = badge_id
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT COUNT(*) AS count FROM badge_award_history h{where}
                    """,
                    params,
                )
                total = int(cursor.fetchone()["count"])
                cursor.execute(
                    f"""
                    SELECT h.id, h.community_user_id, h.badge_id, b.identifier AS badge_identifier,
                           b.name AS badge_name, h.action, h.actor, h.reason, h.event_key,
                           h.created_at, cu.username AS community_username
                    FROM badge_award_history h
                    JOIN badge b ON b.id = h.badge_id
                    LEFT JOIN community_user cu ON cu.id = h.community_user_id
                    {where}
                    ORDER BY h.created_at DESC, h.id DESC
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    params,
                )
                return [dict(row) for row in cursor.fetchall()], total
