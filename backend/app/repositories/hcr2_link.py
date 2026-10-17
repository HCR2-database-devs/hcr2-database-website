"""Data access for Phase 4 HCR2 player account linking.

Two tables back the feature:

``hcr2_account_link``
    The durable link between a community account and an HCR2 player name.
    Only one link per normalized player name and one per community account
    may be ``active`` at a time; both are enforced by partial unique indexes
    rather than by application logic alone.

``hcr2_verification_request``
    The wizard state for one attempt. Verification is always manual, so this
    table records what the user *claims* to have done (``team_joined_at``,
    ``code_sent_confirmed_at``, ...) and never records an approval on its own.

Player names are always resolved through :meth:`find_eligible_player`, which
requires at least one row in ``world_record``. Because superseded records are
retained with ``current = 0``, that single ``EXISTS`` covers both players who
still hold a world record and players whose records were only historical. A
name with no row at all in ``world_record`` is never eligible.

The verification code is stored twice: ``code_token_hash`` is the keyed hash
used for any comparison, and ``code_value`` is the plaintext an administrator
has to read in order to compare it against what they see in team chat. The
plaintext column is read only by the admin review endpoint and is never
returned by a user-facing or public endpoint. It grants no access on its own:
approval always requires a human decision.
"""

from typing import Any, Protocol

import psycopg

from app.db.session import DatabaseConfig, open_connection


def _alias_columns(columns: str, prefix: str) -> str:
    """Prefix a comma-separated column list for use in an aliased ``SELECT``.

    ``INSERT``/``UPDATE ... RETURNING`` have no table alias in scope, so those
    statements use the bare list instead.
    """
    parts = [part.strip() for part in columns.replace("\n", " ").split(",")]
    return ", ".join(f"{prefix}{part}" for part in parts if part)


#: Columns selected for the admin review queue.
ADMIN_REQUEST_COLUMNS = """
    r.id, r.community_user_id, r.link_id, r.player_id,
    r.player_name, r.player_name_norm,
    r.verification_method, r.status, r.step,
    r.attempt_count, r.is_resubmission, r.supersedes_request_id,
    r.created_at, r.updated_at, r.expires_at, r.submitted_at,
    r.player_confirmed_at, r.team_joined_at,
    r.code_value, r.code_generated_at, r.code_expires_at,
    r.code_last_generated_at, r.code_roll_count,
    r.code_sent_confirmed_at, r.code_visibility_confirmed,
    r.discord_joined_at, r.contacted_owner_at,
    r.challenge_distance_m, r.challenge_url, r.challenge_id, r.challenge_confirmed_at,
    r.appointment_status, r.appointment_at, r.appointment_note,
    r.decided_at, r.decided_by_admin,
    r.rejection_category, r.rejection_reason, r.admin_note,
    cu.username AS community_username,
    cu.discord_id, cu.discord_username, cu.discord_avatar
"""

#: Request columns fetched for the owning user. Includes ``code_token_hash`` so
#: the service can verify a code's integrity before accepting the "I've sent the
#: code" claim, but the service's ``_user_view`` whitelist means the hash never
#: reaches an API response. Also deliberately excludes ``admin_note``,
#: ``decided_by_admin`` and any Discord identifier.
#:
#: Bare column names are declared separately as :data:`_REQUEST_COLUMNS` for
#: ``INSERT``/``UPDATE ... RETURNING``; aliased columns are not valid there
#: because no table alias exists in a ``RETURNING`` list.
_REQUEST_COLUMNS = """
    id, player_name, player_name_norm,
    verification_method, status, step,
    attempt_count, is_resubmission, supersedes_request_id,
    created_at, updated_at, expires_at, submitted_at,
    team_joined_at, code_token_hash,
    code_value, code_generated_at, code_expires_at,
    code_last_generated_at, code_roll_count,
    code_sent_confirmed_at, code_visibility_confirmed,
    discord_joined_at, contacted_owner_at,
    challenge_distance_m, challenge_url, challenge_id, challenge_confirmed_at,
    appointment_status, appointment_at,
    decided_at, rejection_category
"""

USER_REQUEST_COLUMNS = _alias_columns(_REQUEST_COLUMNS, "r.")

#: Link columns. Bare column names, for use in ``INSERT``/``UPDATE ... RETURNING``,
#: where no table alias is in scope. Use :data:`LINK_SELECT_COLUMNS` in a
#: ``SELECT`` that aliases the table as ``l``.
_LINK_COLUMNS = """
    id, community_user_id, player_id, player_name, player_name_norm,
    verification_method, status, requested_at, approved_at,
    approved_by_admin, revoked_at, revoked_by_admin, revocation_reason
"""

#: Same columns, aliased for ``SELECT ... FROM hcr2_account_link l``.
LINK_SELECT_COLUMNS = _alias_columns(_LINK_COLUMNS, "l.")


class ActiveLinkConflictError(Exception):
    """Raised when the player name or the account already has an active link.

    Deliberately carries no information about *who* holds the conflicting
    link: the caller shows a generic message and tells the user to contact
    staff.
    """


class Hcr2LinkRepository(Protocol):
    def search_eligible_players(
        self,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]: ...

    def find_eligible_player(self, name: str) -> dict[str, Any] | None: ...

    def get_active_link_for_user(self, community_user_id: int) -> dict[str, Any] | None: ...

    def get_active_link_for_player(
        self,
        player_name_norm: str,
    ) -> dict[str, Any] | None: ...

    def get_link(self, link_id: int) -> dict[str, Any] | None: ...

    def get_request(self, request_id: int) -> dict[str, Any] | None: ...

    def get_active_request(self, community_user_id: int) -> dict[str, Any] | None: ...

    def get_latest_request(self, community_user_id: int) -> dict[str, Any] | None: ...

    def list_open_request_ids(self, community_user_id: int) -> list[int]: ...

    def list_requests_for_user(self, community_user_id: int) -> list[dict[str, Any]]: ...

    def create_request(self, values: dict[str, Any]) -> dict[str, Any]: ...

    def mark_request_step(
        self,
        request_id: int,
        *,
        step: str,
        status: str | None = None,
        fields: dict[str, Any] | None = None,
        detail: str = "",
    ) -> dict[str, Any] | None: ...

    def issue_code(self, values: dict[str, Any]) -> dict[str, Any] | None: ...

    def expire_stale_requests(self) -> int: ...

    def cancel_open_requests_for_user(self, community_user_id: int) -> int: ...

    def clear_codes_for_user(self, community_user_id: int) -> int: ...

    def list_admin_requests(
        self,
        *,
        status: str | None,
        method: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]: ...

    def list_request_history(
        self,
        *,
        community_user_id: int,
        player_name_norm: str,
    ) -> list[dict[str, Any]]: ...

    def list_request_steps(self, request_id: int) -> list[dict[str, Any]]: ...

    def approve_request(self, values: dict[str, Any]) -> dict[str, Any] | None: ...

    def reject_request(self, values: dict[str, Any]) -> dict[str, Any] | None: ...

    def set_request_status(self, request_id: int, status: str) -> dict[str, Any] | None: ...

    def set_appointment(self, values: dict[str, Any]) -> dict[str, Any] | None: ...

    def list_links(
        self,
        *,
        status: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]: ...

    def set_link_status(self, values: dict[str, Any]) -> dict[str, Any] | None: ...

    def find_conflicts(self, player_name_norm: str) -> dict[str, Any]: ...


def _escape_like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


_ELIGIBLE_PLAYER_PREDICATE = """
    EXISTS (
        SELECT 1 FROM world_record wr
        WHERE wr.id_player = p.id_player
    )
"""


class PostgresHcr2LinkRepository:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self._config = config

    # -- player name lookup -------------------------------------------------

    def search_eligible_players(
        self,
        *,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return player names that have, or ever had, an Adventure world record.

        Only the canonical name and the count of *current* world records are
        exposed. Submission data, submitter identities, IP addresses and
        questionable flags are deliberately not part of this query: the
        dropdown is not a record browser.
        """
        clauses = [_ELIGIBLE_PLAYER_PREDICATE]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if search:
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params["pattern"] = f"%{escaped}%"
            clauses.append("p.name_player ILIKE %(pattern)s ESCAPE '\\'")

        where_sql = " AND ".join(clauses)
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT p.id_player, p.name_player,
                           COUNT(*) FILTER (WHERE wr.current = 1)::int AS record_count
                    FROM player p
                    JOIN world_record wr ON wr.id_player = p.id_player
                    WHERE {where_sql}
                    GROUP BY p.id_player, p.name_player
                    ORDER BY
                        (lower(p.name_player) = lower(%(search)s)) DESC,
                        p.name_player
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    {**params, "search": search or ""},
                )
                players = [dict(row) for row in cursor.fetchall()]

                cursor.execute(
                    f"""
                    SELECT count(DISTINCT p.id_player)::int AS count
                    FROM player p
                    WHERE {where_sql}
                    """,
                    params,
                )
                total = int(cursor.fetchone()["count"])
                return players, total

    def find_eligible_player(self, name: str) -> dict[str, Any] | None:
        """Resolve one exact canonical player name, or ``None`` if ineligible.

        The lookup is exact rather than fuzzy: the user picked a specific row
        from the dropdown, so matching a different spelling would be a bug,
        not a convenience.
        """
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT p.id_player, p.name_player,
                           COUNT(*) FILTER (WHERE wr.current = 1)::int AS record_count
                    FROM player p
                    JOIN world_record wr ON wr.id_player = p.id_player
                    WHERE p.name_player = %(name)s
                      AND {_ELIGIBLE_PLAYER_PREDICATE}
                    GROUP BY p.id_player, p.name_player
                    """,
                    {"name": name},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    # -- links --------------------------------------------------------------

    def get_active_link_for_user(self, community_user_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {LINK_SELECT_COLUMNS}
                    FROM hcr2_account_link l
                    WHERE l.community_user_id = %(user_id)s
                      AND l.status = 'active'
                    ORDER BY l.approved_at DESC NULLS LAST, l.id DESC
                    LIMIT 1
                    """,
                    {"user_id": community_user_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def get_active_link_for_player(self, player_name_norm: str) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {LINK_SELECT_COLUMNS}
                    FROM hcr2_account_link l
                    WHERE l.player_name_norm = %(player_name_norm)s
                      AND l.status = 'active'
                    LIMIT 1
                    """,
                    {"player_name_norm": player_name_norm},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def get_link(self, link_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT {LINK_SELECT_COLUMNS} FROM hcr2_account_link l"
                    " WHERE l.id = %(link_id)s",
                    {"link_id": link_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def list_links(
        self,
        *,
        status: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            clauses.append("l.status = %(status)s")
            params["status"] = status
        if search:
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params["pattern"] = f"%{escaped}%"
            clauses.append(
                "(l.player_name ILIKE %(pattern)s ESCAPE '\\'"
                " OR cu.username ILIKE %(pattern)s ESCAPE '\\'"
                " OR cu.discord_username ILIKE %(pattern)s ESCAPE '\\')"
            )
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {LINK_SELECT_COLUMNS},
                           cu.username AS community_username,
                           cu.discord_id, cu.discord_username
                    FROM hcr2_account_link l
                    JOIN community_user cu ON cu.id = l.community_user_id
                    {where_sql}
                    ORDER BY l.requested_at DESC, l.id DESC
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    params,
                )
                links = [dict(row) for row in cursor.fetchall()]
                cursor.execute(
                    f"""
                    SELECT count(*)::int AS count
                    FROM hcr2_account_link l
                    JOIN community_user cu ON cu.id = l.community_user_id
                    {where_sql}
                    """,
                    params,
                )
                total = int(cursor.fetchone()["count"])
                return links, total

    def set_link_status(self, values: dict[str, Any]) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE hcr2_account_link SET
                        status = %(status)s,
                        revoked_at = CASE WHEN %(status)s = 'active'
                            THEN NULL ELSE COALESCE(%(revoked_at)s, CURRENT_TIMESTAMP) END,
                        revoked_by_admin = CASE WHEN %(status)s = 'active'
                            THEN '' ELSE %(revoked_by_admin)s END,
                        revocation_reason = CASE WHEN %(status)s = 'active'
                            THEN NULL ELSE %(revocation_reason)s END
                    WHERE id = %(link_id)s
                    RETURNING {_LINK_COLUMNS}
                    """,
                    values,
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    # -- requests -----------------------------------------------------------

    def get_request(self, request_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {ADMIN_REQUEST_COLUMNS}
                    FROM hcr2_verification_request r
                    JOIN community_user cu ON cu.id = r.community_user_id
                    WHERE r.id = %(request_id)s
                    """,
                    {"request_id": request_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def get_active_request(self, community_user_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {USER_REQUEST_COLUMNS}
                    FROM hcr2_verification_request r
                    WHERE r.community_user_id = %(user_id)s
                      AND r.status IN ('draft', 'in_progress', 'submitted')
                    ORDER BY
                        CASE r.status WHEN 'submitted' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END,
                        r.updated_at DESC,
                        r.id DESC
                    LIMIT 1
                    """,
                    {"user_id": community_user_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def get_latest_request(self, community_user_id: int) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {USER_REQUEST_COLUMNS}
                    FROM hcr2_verification_request r
                    WHERE r.community_user_id = %(user_id)s
                    ORDER BY r.created_at DESC, r.id DESC
                    LIMIT 1
                    """,
                    {"user_id": community_user_id},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else None

    def list_open_request_ids(self, community_user_id: int) -> list[int]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM hcr2_verification_request
                    WHERE community_user_id = %(user_id)s
                      AND status IN ('draft', 'in_progress')
                    ORDER BY id
                    """,
                    {"user_id": community_user_id},
                )
                return [int(row["id"]) for row in cursor.fetchall()]

    def list_requests_for_user(self, community_user_id: int) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {USER_REQUEST_COLUMNS}
                    FROM hcr2_verification_request r
                    WHERE r.community_user_id = %(user_id)s
                    ORDER BY r.created_at DESC, r.id DESC
                    LIMIT 20
                    """,
                    {"user_id": community_user_id},
                )
                return [dict(row) for row in cursor.fetchall()]

    def create_request(self, values: dict[str, Any]) -> dict[str, Any]:
        """Insert a new attempt.

        ``values["step"]`` is whatever the caller determined; the service owns
        that decision so it stays in one place.
        """
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO hcr2_verification_request (
                        community_user_id, player_id, player_name, player_name_norm,
                        verification_method, status, step, attempt_count,
                        is_resubmission, supersedes_request_id, expires_at
                    )
                    VALUES (
                        %(community_user_id)s, %(player_id)s, %(player_name)s,
                        %(player_name_norm)s, %(verification_method)s, %(status)s,
                        %(step)s, %(attempt_count)s, %(is_resubmission)s,
                        %(supersedes_request_id)s, %(expires_at)s
                    )
                    RETURNING {_REQUEST_COLUMNS}
                    """,
                    values,
                )
                request = dict(cursor.fetchone())
                cursor.execute(
                    """
                    INSERT INTO hcr2_verification_request_step (request_id, step, detail)
                    VALUES (%(request_id)s, %(step)s, %(detail)s)
                    """,
                    {
                        "request_id": request["id"],
                        "step": request["step"],
                        "detail": "Request started",
                    },
                )
                return request

    def mark_request_step(
        self,
        request_id: int,
        *,
        step: str,
        status: str | None = None,
        fields: dict[str, Any] | None = None,
        detail: str = "",
    ) -> dict[str, Any] | None:
        """Advance a request and append its step-history row.

        Column names come from :class:`Hcr2LinkRequestUpdate` and are joined
        from a hardcoded allowlist, never from user input.
        """
        assignments = ["step = %(step)s", "updated_at = CURRENT_TIMESTAMP"]
        params: dict[str, Any] = {"request_id": request_id, "step": step}
        if status is not None:
            assignments.append("status = %(status)s")
            params["status"] = status
        for column in _REQUEST_UPDATE_COLUMNS:
            if fields and column in fields:
                assignments.append(f"{column} = %({column})s")
                params[column] = fields[column]
        set_sql = ", ".join(assignments)

        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE hcr2_verification_request SET {set_sql}
                    WHERE id = %(request_id)s
                    RETURNING {_REQUEST_COLUMNS}
                    """,
                    params,
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                cursor.execute(
                    """
                    INSERT INTO hcr2_verification_request_step (request_id, step, detail)
                    VALUES (%(request_id)s, %(step)s, %(detail)s)
                    """,
                    {"request_id": request_id, "step": step, "detail": detail},
                )
                return dict(row)

    def issue_code(self, values: dict[str, Any]) -> dict[str, Any] | None:
        """Write a freshly generated code, replacing any previous one.

        A single ``UPDATE`` means the previous code is invalidated in the same
        statement that installs its replacement, so two codes for the same
        attempt can never both be active. The returned row omits
        ``code_token_hash``; only ``code_value`` and the timestamps travel back
        to the owning user.
        """
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE hcr2_verification_request SET
                        code_token_hash = %(code_token_hash)s,
                        code_value = %(code_value)s,
                        code_generated_at = CURRENT_TIMESTAMP,
                        code_expires_at = %(code_expires_at)s,
                        code_last_generated_at = CURRENT_TIMESTAMP,
                        code_roll_count = code_roll_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %(request_id)s
                      AND (
                          code_last_generated_at IS NULL
                          OR code_last_generated_at <= %(cooldown_cutoff)s
                      )
                    RETURNING {_REQUEST_COLUMNS}
                    """,
                    values,
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                cursor.execute(
                    """
                    INSERT INTO hcr2_verification_request_step (request_id, step, detail)
                    VALUES (%(request_id)s, 'team_code', %(detail)s)
                    """,
                    {
                        "request_id": values["request_id"],
                        "detail": "Verification code generated (roll "
                        f"{int(row.get('code_roll_count', 1))})",
                    },
                )
                return dict(row)

    def expire_stale_requests(self) -> int:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE hcr2_verification_request SET
                        status = 'expired',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE status IN ('draft', 'in_progress')
                      AND expires_at <= CURRENT_TIMESTAMP
                    RETURNING id
                    """
                )
                expired = [int(row["id"]) for row in cursor.fetchall()]
                for request_id in expired:
                    cursor.execute(
                        """
                        INSERT INTO hcr2_verification_request_step
                            (request_id, step, detail)
                        VALUES (%(request_id)s, 'expired', 'Request expired')
                        """,
                        {"request_id": request_id},
                    )
                return len(expired)

    def cancel_open_requests_for_user(self, community_user_id: int) -> int:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE hcr2_verification_request SET
                        status = 'cancelled',
                        code_token_hash = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE community_user_id = %(user_id)s
                      AND status IN ('draft', 'in_progress')
                    RETURNING id
                    """,
                    {"user_id": community_user_id},
                )
                cancelled = [int(row["id"]) for row in cursor.fetchall()]
                for request_id in cancelled:
                    cursor.execute(
                        """
                        INSERT INTO hcr2_verification_request_step
                            (request_id, step, detail)
                        VALUES (%(request_id)s, 'cancelled', 'Request cancelled by the user')
                        """,
                        {"request_id": request_id},
                    )
                return len(cancelled)

    def clear_codes_for_user(self, community_user_id: int) -> int:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE hcr2_verification_request SET
                        code_token_hash = NULL,
                        code_value = NULL,
                        code_expires_at = NULL
                    WHERE community_user_id = %(user_id)s
                      AND code_token_hash IS NOT NULL
                    """,
                    {"user_id": community_user_id},
                )
                return int(cursor.rowcount)

    # -- admin --------------------------------------------------------------

    def list_admin_requests(
        self,
        *,
        status: str | None,
        method: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, Any]], int]:
        clauses: list[str] = []
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            clauses.append("r.status = %(status)s")
            params["status"] = status
        if method:
            clauses.append("r.verification_method = %(method)s")
            params["method"] = method
        if search:
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params["pattern"] = f"%{escaped}%"
            clauses.append(
                "(r.player_name ILIKE %(pattern)s ESCAPE '\\'"
                " OR cu.username ILIKE %(pattern)s ESCAPE '\\'"
                " OR cu.discord_username ILIKE %(pattern)s ESCAPE '\\')"
            )
        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT {ADMIN_REQUEST_COLUMNS},
                           (
                               SELECT count(*)::int FROM hcr2_verification_request p
                               WHERE p.community_user_id = r.community_user_id
                                 AND p.id <> r.id
                           ) AS other_attempts
                    FROM hcr2_verification_request r
                    JOIN community_user cu ON cu.id = r.community_user_id
                    {where_sql}
                    ORDER BY
                        CASE r.status WHEN 'submitted' THEN 0 ELSE 1 END,
                        r.created_at DESC,
                        r.id DESC
                    LIMIT %(limit)s OFFSET %(offset)s
                    """,
                    params,
                )
                requests = [dict(row) for row in cursor.fetchall()]
                cursor.execute(
                    f"""
                    SELECT count(*)::int AS count
                    FROM hcr2_verification_request r
                    JOIN community_user cu ON cu.id = r.community_user_id
                    {where_sql}
                    """,
                    params,
                )
                total = int(cursor.fetchone()["count"])
                return requests, total

    def list_request_history(
        self,
        *,
        community_user_id: int,
        player_name_norm: str,
    ) -> list[dict[str, Any]]:
        """Previous attempts by this account or by anyone else for the same name.

        Used by the admin panel to spot duplicate or competing linking claims.
        """
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT r.id, r.community_user_id, r.player_name, r.player_name_norm,
                           r.verification_method, r.status, r.step,
                           r.created_at, r.submitted_at, r.decided_at,
                           r.rejection_category, r.rejection_reason,
                           r.is_resubmission, r.attempt_count, r.supersedes_request_id,
                           cu.username AS community_username
                    FROM hcr2_verification_request r
                    JOIN community_user cu ON cu.id = r.community_user_id
                    WHERE r.community_user_id = %(user_id)s
                       OR r.player_name_norm = %(player_name_norm)s
                    ORDER BY r.created_at DESC, r.id DESC
                    LIMIT 40
                    """,
                    {
                        "user_id": community_user_id,
                        "player_name_norm": player_name_norm,
                    },
                )
                return [dict(row) for row in cursor.fetchall()]

    def list_request_steps(self, request_id: int) -> list[dict[str, Any]]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, step, reached_at, detail
                    FROM hcr2_verification_request_step
                    WHERE request_id = %(request_id)s
                    ORDER BY reached_at, id
                    """,
                    {"request_id": request_id},
                )
                return [dict(row) for row in cursor.fetchall()]

    def approve_request(self, values: dict[str, Any]) -> dict[str, Any] | None:
        """Approve a request and create its active link in one transaction.

        The request row is locked with ``FOR UPDATE`` first, and its status is
        re-read under that lock, so two admins clicking Approve at the same
        time cannot both create a link: the second one blocks until the first
        commits and then finds the request no longer ``submitted`` and gets
        ``None`` back. The partial unique indexes on ``hcr2_account_link`` are
        the final backstop for the player name and the account; a violation is
        translated into :class:`ActiveLinkConflictError`, which carries no
        information about the conflicting holder.
        """
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                try:
                    with connection.transaction():
                        cursor.execute(
                            """
                            SELECT id, status, player_name, player_name_norm,
                                   community_user_id
                            FROM hcr2_verification_request
                            WHERE id = %(request_id)s
                            FOR UPDATE
                            """,
                            {"request_id": values["request_id"]},
                        )
                        locked = cursor.fetchone()
                        if locked is None or locked["status"] != "submitted":
                            return None

                        cursor.execute(
                            f"""
                            INSERT INTO hcr2_account_link (
                                community_user_id, player_id, player_name, player_name_norm,
                                verification_method, status, requested_at, approved_at,
                                approved_by_admin
                            )
                            VALUES (
                                %(community_user_id)s, %(player_id)s, %(player_name)s,
                                %(player_name_norm)s, %(verification_method)s, 'active',
                                COALESCE(%(requested_at)s, CURRENT_TIMESTAMP),
                                CURRENT_TIMESTAMP, %(admin_username)s
                            )
                            RETURNING {_LINK_COLUMNS}
                            """,
                            values,
                        )
                        link = dict(cursor.fetchone())

                        cursor.execute(
                            """
                            UPDATE hcr2_verification_request SET
                                status = 'approved',
                                step = 'summary',
                                link_id = %(link_id)s,
                                decided_at = CURRENT_TIMESTAMP,
                                decided_by_admin = %(admin_username)s,
                                admin_note = %(note)s,
                                code_token_hash = NULL,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %(request_id)s
                            RETURNING id
                            """,
                            {
                                "link_id": link["id"],
                                "request_id": values["request_id"],
                                "admin_username": values["admin_username"],
                                "note": values.get("note"),
                            },
                        )
                        cursor.execute(
                            """
                            INSERT INTO hcr2_verification_request_step
                                (request_id, step, detail)
                            VALUES (%(request_id)s, 'approved', %(detail)s)
                            """,
                            {
                                "request_id": values["request_id"],
                                "detail": f"Approved by {values['admin_username']}",
                            },
                        )
                except psycopg.errors.UniqueViolation:
                    raise ActiveLinkConflictError(
                        "An active link already exists for this player name or account."
                    ) from None
                return link

    def reject_request(self, values: dict[str, Any]) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                with connection.transaction():
                    cursor.execute(
                        """
                        SELECT id FROM hcr2_verification_request
                        WHERE id = %(request_id)s
                        FOR UPDATE
                        """,
                        {"request_id": values["request_id"]},
                    )
                    if cursor.fetchone() is None:
                        return None
                    cursor.execute(
                        """
                        UPDATE hcr2_verification_request SET
                            status = 'rejected',
                            step = 'summary',
                            decided_at = CURRENT_TIMESTAMP,
                            decided_by_admin = %(admin_username)s,
                            rejection_category = %(category)s,
                            rejection_reason = %(reason)s,
                            admin_note = %(note)s,
                            code_token_hash = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %(request_id)s
                        RETURNING id
                        """,
                        {
                            "request_id": values["request_id"],
                            "admin_username": values["admin_username"],
                            "category": values.get("category"),
                            "reason": values.get("reason"),
                            "note": values.get("note"),
                        },
                    )
                    cursor.execute(
                        """
                        INSERT INTO hcr2_verification_request_step
                            (request_id, step, detail)
                        VALUES (%(request_id)s, 'rejected', %(detail)s)
                        """,
                        {
                            "request_id": values["request_id"],
                            "detail": f"Rejected by {values['admin_username']}",
                        },
                    )
                return {"id": values["request_id"], "status": "rejected"}

    def set_request_status(self, request_id: int, status: str) -> dict[str, Any] | None:
        """Move a request to a terminal status without creating or revoking a link."""
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                with connection.transaction():
                    cursor.execute(
                        f"""
                        UPDATE hcr2_verification_request SET
                            status = %(status)s,
                            code_token_hash = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %(request_id)s
                        RETURNING {_REQUEST_COLUMNS}
                        """,
                        {"request_id": request_id, "status": status},
                    )
                    row = cursor.fetchone()
                    if row is None:
                        return None
                    cursor.execute(
                        """
                        INSERT INTO hcr2_verification_request_step
                            (request_id, step, detail)
                        VALUES (%(request_id)s, %(step)s, %(detail)s)
                        """,
                        {
                            "request_id": request_id,
                            "step": status if status != "in_progress" else "retry_requested",
                            "detail": f"Status set to {status} by an administrator",
                        },
                    )
                    return dict(row)

    def set_appointment(self, values: dict[str, Any]) -> dict[str, Any] | None:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                with connection.transaction():
                    cursor.execute(
                        """
                        UPDATE hcr2_verification_request SET
                            appointment_status = %(appointment_status)s,
                            appointment_at = %(appointment_at)s,
                            appointment_note = %(appointment_note)s,
                            step = 'discord_schedule',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %(request_id)s
                          AND verification_method = 'discord_screen_share'
                        RETURNING id
                        """,
                        values,
                    )
                    if cursor.fetchone() is None:
                        return None
                    cursor.execute(
                        """
                        INSERT INTO hcr2_verification_request_step
                            (request_id, step, detail)
                        VALUES (%(request_id)s, 'discord_schedule', %(detail)s)
                        """,
                        {
                            "request_id": values["request_id"],
                            "detail": (
                                f"Appointment status set to {values['appointment_status']}"
                                + (
                                    f" for {values['appointment_at']}"
                                    if values.get("appointment_at")
                                    else ""
                                )
                            ),
                        },
                    )
                return {"id": values["request_id"], "status": values["appointment_status"]}

    def find_conflicts(self, player_name_norm: str) -> dict[str, Any]:
        with open_connection(self._config) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        (SELECT count(*)::int FROM hcr2_account_link l
                         WHERE l.player_name_norm = %(player_name_norm)s
                           AND l.status = 'active') AS active_links,
                        (SELECT count(*)::int FROM hcr2_verification_request r
                         WHERE r.player_name_norm = %(player_name_norm)s
                           AND r.status = 'submitted') AS open_requests,
                        (SELECT count(DISTINCT r.community_user_id)::int
                         FROM hcr2_verification_request r
                         WHERE r.player_name_norm = %(player_name_norm)s
                           AND r.status IN ('draft', 'in_progress', 'submitted')
                        ) AS competing_claimants
                    """,
                    {"player_name_norm": player_name_norm},
                )
                row = cursor.fetchone()
                return dict(row) if row is not None else {
                    "active_links": 0,
                    "open_requests": 0,
                    "competing_claimants": 0,
                }


#: Allowlist of request columns that ``mark_request_step`` may write. Keeps the
#: dynamic ``SET`` clause away from user input.
_REQUEST_UPDATE_COLUMNS = (
    "verification_method",
    "expires_at",
    "submitted_at",
    "player_confirmed_at",
    "team_joined_at",
    "code_token_hash",
    "code_value",
    "code_generated_at",
    "code_expires_at",
    "code_last_generated_at",
    "code_sent_confirmed_at",
    "code_visibility_confirmed",
    "discord_joined_at",
    "contacted_owner_at",
    "challenge_distance_m",
    "challenge_url",
    "challenge_id",
    "challenge_confirmed_at",
    "appointment_status",
    "appointment_at",
    "appointment_note",
    "rejection_category",
    "player_name",
    "player_name_norm",
    "player_id",
)