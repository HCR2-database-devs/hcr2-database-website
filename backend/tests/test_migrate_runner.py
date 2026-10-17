"""Tests for the SQL migration runner in ``scripts/migrate.py``.

The runner wraps every migration in its own transaction, so it strips
``BEGIN``/``COMMIT``/``END`` statements from the file first. That rewrite is
text-based and therefore has to understand dollar-quoted bodies: a
``DO $$ BEGIN ... END $$;`` block is PL/pgSQL whose bare ``BEGIN`` line belongs
to the block. Scrubbing it away turned every ``DO $$`` migration into a syntax
error at ``IF`` and left a development database with no community tables at all.

The script lives outside the ``app`` package, so it is loaded by path.
"""

import importlib.util
from pathlib import Path

import pytest

MIGRATE_PY = Path(__file__).resolve().parents[2] / "scripts" / "migrate.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("hcr2_migrate", MIGRATE_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migrate = _load_runner()


def test_real_transaction_control_statements_are_stripped() -> None:
    sql = "BEGIN;\nCREATE TABLE demo (id integer);\nCOMMIT;\n"

    scrubbed = migrate._scrub_transaction_control(sql)

    assert scrubbed == "CREATE TABLE demo (id integer);"


def test_begin_and_end_inside_a_dollar_quoted_body_survive() -> None:
    sql = (
        "DO $$\n"
        "BEGIN\n"
        "    IF to_regclass('public.map') IS NOT NULL THEN\n"
        "        UPDATE map SET special = 1;\n"
        "    END IF;\n"
        "END $$;\n"
    )

    scrubbed = migrate._scrub_transaction_control(sql)

    assert "BEGIN" in scrubbed
    assert "END $$;" in scrubbed
    assert scrubbed.count("IF to_regclass") == 1


def test_a_tagged_dollar_quoted_body_survives() -> None:
    sql = "DO $body$\nBEGIN\n    PERFORM 1;\nEND\n$body$;\n"

    assert migrate._scrub_transaction_control(sql).strip() == sql.strip()


def test_a_string_literal_containing_begin_is_not_rewritten() -> None:
    sql = "INSERT INTO demo (note) VALUES ('BEGIN');\nCOMMIT;\n"

    scrubbed = migrate._scrub_transaction_control(sql)

    assert "'BEGIN'" in scrubbed
    assert "COMMIT" not in scrubbed


@pytest.mark.parametrize(
    "path",
    sorted((Path(__file__).resolve().parents[2] / "migrations").glob("*.up.sql")),
    ids=lambda path: path.name,
)
def test_every_shipped_migration_keeps_its_dollar_quoted_bodies(path: Path) -> None:
    """No migration may lose a ``BEGIN``/``END`` that belongs to a DO body.

    Files are free to wrap themselves in their own ``BEGIN``/``COMMIT`` -- those
    are stripped on purpose. A bare ``BEGIN`` inside a dollar-quoted body is
    PL/pgSQL, and mangling it used to turn the whole migration into a syntax
    error at ``IF`` during ``migrate.py up``.
    """
    sql = path.read_text(encoding="utf-8")
    scrubbed = migrate._scrub_transaction_control(sql)

    quoted_before = [chunk for quoted, chunk in migrate._split_dollar_quoted(sql) if quoted]
    quoted_after = [chunk for quoted, chunk in migrate._split_dollar_quoted(scrubbed) if quoted]

    assert quoted_after == quoted_before, path.name

    # Nothing that looks like transaction control may survive outside a body.
    for quoted, chunk in migrate._split_dollar_quoted(scrubbed):
        if quoted:
            continue
        assert not migrate._TRANSACTION_CONTROL.search(chunk), path.name