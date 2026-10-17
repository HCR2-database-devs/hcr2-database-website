"""SQL-level tests for the Phase 4 repository.

There is no database in the test environment, so these assert on the SQL and
parameters handed to psycopg using a fake cursor, in the same style as
``tests/test_record_submission_controls.py``. What matters here is the shape of
the statements themselves: which tables they touch, that the eligible-name
query is anchored on ``world_record``, that approval locks and runs in a
transaction, and that user input only ever arrives as bound parameters.
"""

from typing import Any

import pytest

from app.repositories.hcr2_link import (
    _REQUEST_COLUMNS,
    ADMIN_REQUEST_COLUMNS,
    ActiveLinkConflictError,
    PostgresHcr2LinkRepository,
)
from app.services.rate_limit import RATE_LIMIT_TABLE, consume_rate_limit, rate_limit_key


class _Cursor:
    def __init__(self, responses: dict[str, Any] | None = None) -> None:
        self.responses = responses or {}
        self.queries: list[str] = []
        self.parameters: list[Any] = []
        self.rowcount = 0
        self._rows: list[dict[str, Any]] = []
        self._one: dict[str, Any] | None = None

    def __enter__(self) -> "_Cursor":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def _default_row(self, normalized: str) -> dict[str, Any] | None:
        """Plausible RETURNING rows so statements proceed like they would in prod."""
        if "::int AS count" in normalized:
            return {"count": 0}
        if "FOR UPDATE" in normalized and "hcr2_verification_request" in normalized:
            return {
                "id": 1,
                "status": "submitted",
                "player_name": "Demo Driver",
                "player_name_norm": "demo driver",
                "community_user_id": 1,
            }
        if "RETURNING" not in normalized:
            return None
        if "INSERT INTO hcr2_account_link" in normalized:
            return {
                "id": 1,
                "community_user_id": 1,
                "player_id": 1,
                "player_name": "Demo Driver",
                "player_name_norm": "demo driver",
                "verification_method": "team",
                "status": "active",
                "requested_at": None,
                "approved_at": None,
                "approved_by_admin": "mod",
                "revoked_at": None,
                "revoked_by_admin": "",
                "revocation_reason": None,
            }
        if "INSERT INTO hcr2_verification_request " in normalized:
            return {"id": 1}
        if "UPDATE hcr2_verification_request" in normalized:
            return {"id": 1, "status": "approved", "code_roll_count": 1}
        return {"id": 1}

    def execute(self, query: str, parameters: Any = None) -> None:
        normalized = " ".join(query.split())
        self.queries.append(normalized)
        self.parameters.append(parameters)
        for marker, value in self.responses.items():
            if marker in normalized:
                if isinstance(value, list):
                    self._rows = value
                    self._one = value[0] if value else None
                elif isinstance(value, dict):
                    self._rows = [value]
                    self._one = value
                else:
                    self._rows = []
                    self._one = None
                self.rowcount = len(self._rows)
                return
        default = self._default_row(normalized)
        self._rows = [default] if default is not None else []
        self._one = default
        self.rowcount = len(self._rows)

    def fetchone(self) -> dict[str, Any] | None:
        return self._one

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows

    def __iter__(self) -> Any:
        return iter(self._rows)


class _Transaction:
    def __init__(self) -> None:
        self.entered = 0

    def __enter__(self) -> "_Transaction":
        self.entered += 1
        return self

    def __exit__(self, *_args: Any) -> None:
        return None


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor
        self.transaction_obj = _Transaction()
        self.commits = 0

    def __enter__(self) -> "_Connection":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def cursor(self) -> _Cursor:
        return self._cursor

    def transaction(self) -> _Transaction:
        return self.transaction_obj

    def commit(self) -> None:
        self.commits += 1


@pytest.fixture
def cursor() -> _Cursor:
    return _Cursor()


@pytest.fixture
def repository(monkeypatch: pytest.MonkeyPatch, cursor: _Cursor) -> PostgresHcr2LinkRepository:
    connection = _Connection(cursor)
    monkeypatch.setattr(
        "app.repositories.hcr2_link.open_connection",
        lambda *_args, **_kwargs: connection,
    )
    repository = PostgresHcr2LinkRepository()
    repository._connection = connection  # type: ignore[attr-defined]
    return repository


# -- eligible player names -------------------------------------------------


def test_eligible_name_search_is_anchored_on_world_record(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    repository.search_eligible_players(search="demo", limit=20, offset=0)

    listing = next(
        query for query in cursor.queries if "FROM player p" in query and "GROUP BY" in query
    )
    # The EXISTS is what excludes names that have never had a world record.
    eligibility = listing.split("EXISTS", 1)[1]
    assert "FROM world_record wr" in eligibility
    assert "wr.id_player = p.id_player" in eligibility
    # It is deliberately not restricted to current = 1: superseded rows are
    # retained history, so a player whose only records are historical stays
    # eligible. Only a total absence of rows removes a name.
    assert "current" not in eligibility.split(")", 1)[0]


def test_eligible_name_search_exposes_no_submission_metadata(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    repository.search_eligible_players(search=None, limit=20, offset=0)

    listing = next(query for query in cursor.queries if "GROUP BY" in query)
    select_clause = listing.split("FROM player p")[0]
    assert "name_player" in select_clause
    for leaked in (
        "submitter",
        "submitter_ip",
        "questionable",
        "id_tuning_setup",
        "discord",
        "community_user",
    ):
        assert leaked not in select_clause


def test_eligible_name_search_binds_the_pattern_as_a_parameter(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    # A name containing SQL metacharacters must not reach the statement text.
    hostile = "100%'; DROP TABLE player;--"
    repository.search_eligible_players(search=hostile, limit=20, offset=0)

    assert all("DROP TABLE" not in query for query in cursor.queries)
    patterns = [
        str(params["pattern"])
        for params in cursor.parameters
        if isinstance(params, dict) and "pattern" in params
    ]
    assert patterns, "the search term must arrive as a bound parameter"
    # The LIKE wildcard is escaped rather than interpolated.
    assert any("100\\%" in pattern for pattern in patterns)


def test_find_eligible_player_uses_an_exact_match(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    repository.find_eligible_player("Demo Driver")

    lookup = next(query for query in cursor.queries if "p.name_player =" in query)
    assert "ILIKE" not in lookup
    assert "FROM world_record wr" in lookup


# -- code generation -------------------------------------------------------


def test_issue_code_invalidates_the_previous_code_in_one_statement(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    repository.issue_code(
        {
            "request_id": 1,
            "code_token_hash": "hash",
            "code_value": "Demo Driver:K7M4-X9Q2",
            "code_expires_at": "2026-10-16 12:15:00",
            "cooldown_cutoff": "2026-10-16 12:00:00",
        }
    )

    update = cursor.queries[0]
    assert "code_token_hash = %(code_token_hash)s" in update
    assert "code_value = %(code_value)s" in update
    assert "code_last_generated_at = CURRENT_TIMESTAMP" in update
    # The cooldown is a WHERE condition, so the statement simply matches zero
    # rows while the cooldown runs instead of the caller trusting a clock.
    assert "code_last_generated_at IS NULL" in update
    assert "code_last_generated_at <= %(cooldown_cutoff)s" in update
    assert " OR " in update.split("WHERE id")[1]


def test_issue_code_writes_a_step_audit_row(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    repository.issue_code(
        {
            "request_id": 1,
            "code_token_hash": "hash",
            "code_value": "Demo Driver:K7M4-X9Q2",
            "code_expires_at": "2026-10-16 12:15:00",
            "cooldown_cutoff": "2026-10-16 12:00:00",
        }
    )

    assert any("hcr2_verification_request_step" in query for query in cursor.queries)


def test_approval_clears_the_stored_hash(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    repository.approve_request(
        {
            "request_id": 1,
            "community_user_id": 1,
            "player_id": 1,
            "player_name": "Demo Driver",
            "player_name_norm": "demo driver",
            "verification_method": "team",
            "requested_at": None,
            "admin_username": "mod",
            "note": None,
        }
    )

    update = next(query for query in cursor.queries if "status = 'approved'" in query)
    assert "code_token_hash = NULL" in update


# -- atomicity and concurrency ---------------------------------------------


def test_approval_locks_the_request_and_runs_in_a_transaction(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    connection = repository._connection  # type: ignore[attr-defined]

    repository.approve_request(
        {
            "request_id": 1,
            "community_user_id": 1,
            "player_id": 1,
            "player_name": "Demo Driver",
            "player_name_norm": "demo driver",
            "verification_method": "team",
            "requested_at": None,
            "admin_username": "mod",
            "note": None,
        }
    )

    assert connection.transaction_obj.entered == 1
    lock = next(query for query in cursor.queries if "FOR UPDATE" in query)
    assert "hcr2_verification_request" in lock


def test_approval_refuses_a_request_that_is_no_longer_submitted(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Guards the double-approval race: the second admin blocks on FOR UPDATE,
    # then finds the request already decided and must not create a second link.
    connection = repository._connection  # type: ignore[attr-defined]
    original = connection.cursor

    def decided_cursor() -> _Cursor:
        fake = original()
        real_execute = fake.execute

        def execute(query: str, parameters: Any = None) -> None:
            if "FOR UPDATE" in " ".join(query.split()):
                fake.queries.append(" ".join(query.split()))
                fake.parameters.append(parameters)
                fake._one = {
                    "id": 1,
                    "status": "approved",
                    "player_name": "Demo Driver",
                    "player_name_norm": "demo driver",
                    "community_user_id": 1,
                }
                return
            real_execute(query, parameters)

        fake.execute = execute  # type: ignore[method-assign]
        return fake

    connection.cursor = decided_cursor  # type: ignore[method-assign]

    result = repository.approve_request(
        {
            "request_id": 1,
            "community_user_id": 1,
            "player_id": 1,
            "player_name": "Demo Driver",
            "player_name_norm": "demo driver",
            "verification_method": "team",
            "requested_at": None,
            "admin_username": "mod",
            "note": None,
        }
    )

    assert result is None
    assert not any("INSERT INTO hcr2_account_link" in query for query in cursor.queries)


def test_derived_column_lists_are_alias_safe() -> None:
    # A RETURNING list has no table alias in scope, so the bare lists must not
    # carry one. This is the bug class that only shows up against a real
    # database, since the fake cursor accepts any SQL.
    from app.repositories.hcr2_link import (
        _LINK_COLUMNS,
        _REQUEST_COLUMNS,
        LINK_SELECT_COLUMNS,
        USER_REQUEST_COLUMNS,
    )

    assert "l." not in _LINK_COLUMNS
    assert "r." not in _REQUEST_COLUMNS
    assert LINK_SELECT_COLUMNS.startswith("l.id,")
    assert USER_REQUEST_COLUMNS.startswith("r.id,")


def test_mark_request_step_joins_set_assignments_with_commas(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    repository.mark_request_step(
        1,
        step="team_join",
        fields={"team_joined_at": "2026-10-16 12:00:00", "code_visibility_confirmed": True},
        detail="joined",
    )

    update = cursor.queries[0]
    set_clause = update.split("SET", 1)[1].split("WHERE id", 1)[0]
    assert " AND " not in set_clause
    assert "team_joined_at = %(team_joined_at)s" in set_clause
    assert "code_visibility_confirmed = %(code_visibility_confirmed)s" in set_clause


def test_duplicate_active_link_violation_becomes_a_generic_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import psycopg

    class _RaisingCursor(_Cursor):
        def execute(self, query: str, parameters: Any = None) -> None:
            super().execute(query, parameters)
            raise psycopg.errors.UniqueViolation("duplicate key value")

    connection = _Connection(_RaisingCursor())
    monkeypatch.setattr(
        "app.repositories.hcr2_link.open_connection",
        lambda *_args, **_kwargs: connection,
    )
    repository = PostgresHcr2LinkRepository()

    with pytest.raises(ActiveLinkConflictError) as excinfo:
        repository.approve_request(
            {
                "request_id": 1,
                "community_user_id": 1,
                "player_id": 1,
                "player_name": "Demo Driver",
                "player_name_norm": "demo driver",
                "verification_method": "team",
                "requested_at": None,
                "admin_username": "mod",
                "note": None,
            }
        )

    # The exception must not name the conflicting account or player.
    assert "1" not in str(excinfo.value)
    assert "mod" not in str(excinfo.value)


def test_mark_request_step_only_writes_allowlisted_columns(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    repository.mark_request_step(
        1,
        step="team_code",
        status="in_progress",
        fields={"team_joined_at": "2026-10-16 12:00:00"},
        detail="joined",
    )

    update = cursor.queries[0]
    assert "team_joined_at = %(team_joined_at)s" in update
    # No caller-controlled column names reach the statement.
    assert "discord_id" not in update


def test_challenge_proof_columns_are_selected_and_writable(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    # Method C stores the assigned distance and the link, so every column it
    # writes has to be in the update allowlist and every column the service
    # reads has to be in the select lists.
    repository.mark_request_step(
        1,
        step="challenge_link",
        fields={
            "challenge_distance_m": 1234,
            "challenge_url": "https://playhcr.com/challenge?id=abc123",
            "challenge_id": "abc123",
            "challenge_confirmed_at": "2026-10-17 12:00:00",
        },
        detail="link sent",
    )

    update = cursor.queries[0]
    for column in (
        "challenge_distance_m",
        "challenge_url",
        "challenge_id",
        "challenge_confirmed_at",
    ):
        assert f"{column} = %({column})s" in update

    for column in (
        "challenge_distance_m",
        "challenge_url",
        "challenge_id",
        "challenge_confirmed_at",
    ):
        assert column in ADMIN_REQUEST_COLUMNS
        assert column in _REQUEST_COLUMNS

    # The admin queue must be able to render the link, and the owner's own
    # status payload must carry the same four values back.
    assert "r.challenge_url" in ADMIN_REQUEST_COLUMNS
    assert "challenge_url" in _REQUEST_COLUMNS


def test_set_link_status_requires_a_reason_free_path_for_restore(
    repository: PostgresHcr2LinkRepository,
    cursor: _Cursor,
) -> None:
    repository.set_link_status(
        {
            "link_id": 1,
            "status": "active",
            "revoked_at": None,
            "revoked_by_admin": "",
            "revocation_reason": None,
        }
    )

    update = cursor.queries[0]
    assert "revoked_at = CASE WHEN %(status)s = 'active' THEN NULL" in update


# -- rate limiting ---------------------------------------------------------


def test_rate_limit_key_is_hmacd_not_the_raw_value() -> None:
    key = rate_limit_key("hcr2-link-code", "123456789", "pepper")

    assert key.startswith("hcr2-link-code:")
    assert "123456789" not in key
    assert key == rate_limit_key("hcr2-link-code", "123456789", "pepper")
    assert key != rate_limit_key("hcr2-link-code", "123456789", "other")


def test_consume_rate_limit_allows_up_to_the_limit() -> None:
    cursor = _Cursor(
        {"community_action_rate_limit": {"request_count": 3, "retry_after_seconds": 60}}
    )

    result = consume_rate_limit(
        cursor,
        table=RATE_LIMIT_TABLE,
        scope="hcr2-link-code",
        value="1",
        limit=5,
        window_seconds=300,
        secret="pepper",
    )

    assert result.allowed is True
    assert result.remaining == 2


def test_consume_rate_limit_blocks_past_the_limit_and_reports_retry_after() -> None:
    cursor = _Cursor(
        {"community_action_rate_limit": {"request_count": 6, "retry_after_seconds": 42}}
    )

    result = consume_rate_limit(
        cursor,
        table=RATE_LIMIT_TABLE,
        scope="hcr2-link-code",
        value="1",
        limit=5,
        window_seconds=300,
        secret="pepper",
    )

    assert result.allowed is False
    assert result.retry_after == 42


def test_consume_rate_limit_increments_in_a_single_upsert() -> None:
    cursor = _Cursor(
        {"community_action_rate_limit": {"request_count": 1, "retry_after_seconds": 5}}
    )

    consume_rate_limit(
        cursor,
        table=RATE_LIMIT_TABLE,
        scope="hcr2-link-code",
        value="1",
        limit=5,
        window_seconds=300,
        secret="pepper",
    )

    upsert = cursor.queries[0]
    assert "ON CONFLICT (rate_key) DO UPDATE" in upsert
    # One statement, so two concurrent requests cannot both pass on the last
    # remaining allowance.
    assert upsert.count("INSERT INTO") == 1


def test_consume_rate_limit_is_disabled_by_a_zero_limit() -> None:
    cursor = _Cursor()

    result = consume_rate_limit(
        cursor,
        table=RATE_LIMIT_TABLE,
        scope="hcr2-link-code",
        value="1",
        limit=0,
        window_seconds=300,
        secret="pepper",
    )

    assert result.allowed is True
    assert cursor.queries == []


def test_consume_rate_limit_binds_the_key_and_window_as_parameters() -> None:
    cursor = _Cursor(
        {"community_action_rate_limit": {"request_count": 1, "retry_after_seconds": 5}}
    )

    consume_rate_limit(
        cursor,
        table=RATE_LIMIT_TABLE,
        scope="hcr2-link-code",
        value="1234",
        limit=5,
        window_seconds=300,
        secret="pepper",
    )

    parameters = cursor.parameters[0]
    assert parameters["window_seconds"] == 300
    assert "1234" not in parameters["rate_key"]

# -- profile integration ---------------------------------------------------


def test_link_verified_at_is_promoted_to_an_explicit_utc_offset() -> None:
    """The linked name and its approval date ride along on community profiles.

    ``hcr2_link_verified_at`` is promoted to ``timestamptz`` in SQL so it
    serializes with an offset. Left as a naive column it reached the browser as
    ``2026-10-16T14:45:08.681936``, which JavaScript reads as local time and
    renders hours early for anyone east of UTC.
    """
    from app.repositories.community_user import PROFILE_COLUMNS

    assert "l.approved_at AT TIME ZONE 'UTC'" in PROFILE_COLUMNS
    assert "hcr2_player_name" in PROFILE_COLUMNS
    assert "hcr2_link_verified_at" in PROFILE_COLUMNS
