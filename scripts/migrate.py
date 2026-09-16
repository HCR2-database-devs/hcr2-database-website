#!/usr/bin/env python3
"""
Database migration runner for HCR2 Records.

Applies timestamped SQL migration files in migrations/ to a PostgreSQL database,
tracking applied versions in a `schema_migrations` table.

Usage
-----
    migrate.py status           Show applied / pending migrations
    migrate.py up [OPTIONS]    Apply pending migrations (default if no command)
    migrate.py down [OPTIONS]  Roll back last applied migration(s)
    migrate.py baseline        Mark all pending migrations as applied (no SQL run)
    migrate.py create <name>   Create new migration files for today's date

Options
-------
    --db-url DSN       PostgreSQL DSN (default: from backend/.env or $DATABASE_URL)
    --target VERSION   Apply/rollback only up to this migration version (inclusive)
    --steps N          Number of steps for `down` (default: 1)
    --dry-run          Print what would be executed without running SQL

Connection precedence
---------------------
1. --db-url argument
2. $DATABASE_URL environment variable
3. A local .env file (backend/.env or repo-root .env) using DB_HOST,
   DB_PORT, DB_NAME, DB_USER, DB_PASS

Migration naming convention
---------------------------
Migrations live in the repo-root migrations/ directory and must be named:
    YYYYMMDD_<description>.up.sql    (forward migration)
    YYYYMMDD_<description>.down.sql  (rollback migration)

A plain YYYYMMDD_<description>.sql file is treated as an up-only migration.
If both NAME.up.sql and NAME.sql exist for the same base name, only
NAME.up.sql is used (a warning is printed).

Deployment (production) workflow
--------------------------------
1. Deploy the repo (including scripts/migrate.py and migrations/).
2. Use the backend virtualenv (already installed on the server):
       cd /var/www/hcr2.xyz/backend
       . .venv/bin/activate
   The tool only needs psycopg, already a dependency of the backend.
3. First adoption (schema was migrated by hand before this tool existed):
   make a backup first, then mark the existing migrations as applied
   WITHOUT re-running them:
       ../scripts/migrate.py status                 # sanity check
       ../scripts/migrate.py baseline               # adopt current schema
4. Whenever a new migration is added, apply pending ones:
       ../scripts/migrate.py up                     # or `--dry-run` first
   Roll back the most recent migration:
       ../scripts/migrate.py down                   # --steps N, --target VERSION
   Create a new empty migration pair:
       ../scripts/migrate.py create add_fancy_feature

The tracking table is "schema_migrations". If the production .env is not at
repo-root/backend/.env, pass --db-url explicitly or use .env in repo root.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    sys.exit(
        "psycopg is not installed.\n"
        "Activate the backend venv first:\n"
        "  cd backend && . .venv/bin/activate\n"
        "or install psycopg directly:\n"
        "  pip install 'psycopg[binary]'"
    )

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = REPO_ROOT / "migrations"
BACKEND_ENV = REPO_ROOT / "backend" / ".env"
ROOT_ENV = REPO_ROOT / ".env"

TRACKING_TABLE = "schema_migrations"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_env(path: Path) -> dict[str, str]:
    """Parse a simple KEY=VALUE .env file."""
    env: dict[str, str] = {}
    if not path.is_file():
        return env
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        value = value.strip().strip("'\"")
        env[key.strip()] = value
    return env


def _build_dsn(env: dict[str, str]) -> str:
    """Build a PostgreSQL DSN from individual env vars."""
    from urllib.parse import quote_plus

    host = env.get("DB_HOST") or env.get("PG_HOST") or "127.0.0.1"
    port = env.get("DB_PORT") or env.get("PG_PORT") or "5432"
    dbname = env.get("DB_NAME") or env.get("PG_DATABASE") or "hcr2_dev"
    user = env.get("DB_USER") or env.get("PG_USER") or "hcr2_dev"
    password = env.get("DB_PASS") or env.get("PG_PASSWORD") or ""
    encoded_user = quote_plus(user)
    encoded_pass = quote_plus(password)
    return f"postgresql://{encoded_user}:{encoded_pass}@{host}:{port}/{dbname}"


def find_env_file() -> Path:
    for candidate in (BACKEND_ENV, ROOT_ENV):
        if candidate.is_file():
            return candidate
    return BACKEND_ENV


def resolve_dsn(cli_db_url: str | None = None) -> str:
    if cli_db_url:
        return cli_db_url
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    env = _parse_env(find_env_file())
    if env.get("DATABASE_URL"):
        return env["DATABASE_URL"]
    if env.get("DB_HOST") or env.get("DB_NAME"):
        return _build_dsn(env)
    return "postgresql://hcr2_dev:hcr2_dev_password@127.0.0.1:54329/hcr2_dev"


# ---------------------------------------------------------------------------
# Migration discovery
# ---------------------------------------------------------------------------

class Migration:
    """Represents one migration step identified by its base filename."""

    def __init__(self, version: str, forward: Path, rollback: Path | None):
        self.version = version
        self.forward = forward
        self.rollback = rollback

    def __repr__(self) -> str:
        return f"Migration({self.version!r})"


def _load_migrations() -> list[Migration]:
    """
    Scan migrations/ and return a sorted list of Migration objects.

    If both NAME.sql and NAME.up.sql exist, prefer NAME.up.sql.
    """
    if not MIGRATIONS_DIR.is_dir():
        sys.exit(f"Migrations directory not found: {MIGRATIONS_DIR}")

    files = sorted(MIGRATIONS_DIR.iterdir())
    by_base: dict[str, dict[str, Path | None]] = {}
    duplicates: list[str] = []

    for f in files:
        if not f.suffix == ".sql" or not f.is_file():
            continue
        stem = f.stem  # e.g. 20260601_add_echo_affected_part.up

        if stem.endswith(".down"):
            base = stem[: -len(".down")]
            by_base.setdefault(base, {})["down"] = f
        elif stem.endswith(".up"):
            base = stem[: -len(".up")]
            by_base.setdefault(base, {})["up"] = f
        else:
            # plain .sql — treat as forward migration
            base = stem
            if "up" in by_base.get(base, {}):
                duplicates.append(f"{base}: ignoring {f.name} (prefer .up.sql)")
            else:
                by_base.setdefault(base, {})["up"] = f

    for msg in duplicates:
        print(f"  warning: {msg}", file=sys.stderr)

    migrations: list[Migration] = []
    for version in sorted(by_base):
        entry = by_base[version]
        forward: Path | None = entry.get("up")
        if forward is None:
            print(f"  warning: {version}: no up migration found, skipping", file=sys.stderr)
            continue
        rollback: Path | None = entry.get("down")
        migrations.append(Migration(version, forward, rollback))
    return migrations


def _ensure_tracking_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TRACKING_TABLE} (
                version   TEXT PRIMARY KEY,
                name      TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    conn.commit()


def _applied_versions(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(f"SELECT version FROM {TRACKING_TABLE} ORDER BY version")
        return {row["version"] for row in cur.fetchall()}


def _read_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


_TRANSACTION_CONTROL = re.compile(
    r"^\s*(BEGIN|START\s+TRANSACTION|COMMIT|END|ROLLBACK)\s*;?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _scrub_transaction_control(sql: str) -> str:
    """
    Strip BEGIN/COMMIT/END statements from migration SQL.

    The runner wraps each migration in its own transaction, so any
    transaction-control statements in the file would conflict.
    """
    scrubbed = _TRANSACTION_CONTROL.sub("", sql)
    return scrubbed.strip()


def _apply_sql(conn: psycopg.Connection, sql: str, *, dry_run: bool) -> None:
    if dry_run:
        print(f"    [dry-run] would execute {len(sql)} chars of SQL")
        return
    sql = _scrub_transaction_control(sql)
    with conn.transaction():
        conn.execute(sql)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_status(conn: psycopg.Connection, **_kwargs: Any) -> None:
    all_migrations = _load_migrations()
    applied = _applied_versions(conn)

    if not all_migrations:
        print("No migrations found.")
        return

    print(f"\n  Migrations ({len(all_migrations)} total, {len(applied & {m.version for m in all_migrations})} applied):\n")
    for m in all_migrations:
        tag = "APPLIED" if m.version in applied else "PENDING "
        print(f"    [{tag}]  {m.version}")

    pending = [m for m in all_migrations if m.version not in applied]
    if pending:
        print(f"\n  Run `migrate.py up` to apply {len(pending)} pending migration(s).\n")
    else:
        print("\n  All migrations applied.\n")


def cmd_up(conn: psycopg.Connection, *, target: str | None, dry_run: bool, **_kwargs: Any) -> None:
    all_migrations = _load_migrations()
    applied = _applied_versions(conn)
    pending = [m for m in all_migrations if m.version not in applied]

    if target:
        pending = [m for m in pending if m.version <= target]

    if not pending:
        print("  Nothing to apply.\n")
        return

    print(f"\n  Applying {len(pending)} migration(s) ...\n")
    for m in pending:
        sql = _read_sql(m.forward)
        print(f"    [{m.version}]  {m.forward.name} ({len(sql)} chars)")
        if not dry_run:
            _apply_sql(conn, sql, dry_run=False)
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {TRACKING_TABLE} (version, name) VALUES (%s, %s)",
                    (m.version, m.forward.name),
                )
            conn.commit()
            print("          ✓ applied")
        else:
            print("          (dry-run)")

    print("\n  Done.\n")


def cmd_down(conn: psycopg.Connection, *, steps: int, target: str | None, dry_run: bool, **_kwargs: Any) -> None:
    all_migrations = _load_migrations()
    applied = _applied_versions(conn)
    applied_list = [m for m in all_migrations if m.version in applied]

    if target:
        applied_list = [m for m in applied_list if m.version >= target]

    applied_list = applied_list[::-1]  # reverse = most recent first
    to_rollback = applied_list[:steps]

    if not to_rollback:
        print("  Nothing to roll back.\n")
        return

    print(f"\n  Rolling back {len(to_rollback)} migration(s) ...\n")
    for m in to_rollback:
        if m.rollback is None:
            sys.exit(
                f"  Error: no down migration found for {m.version} "
                f"(expected {m.rollback.name if m.rollback else '???'}).\n"
                f"  Rollback blocked — nothing was changed."
            )
        sql = _read_sql(m.rollback)
        print(f"    [{m.version}]  {m.rollback.name} ({len(sql)} chars)")
        if not dry_run:
            _apply_sql(conn, sql, dry_run=False)
            with conn.cursor() as cur:
                cur.execute(
                    f"DELETE FROM {TRACKING_TABLE} WHERE version = %s",
                    (m.version,),
                )
            conn.commit()
            print("          ✓ rolled back")
        else:
            print("          (dry-run)")

    print("\n  Done.\n")


def cmd_baseline(conn: psycopg.Connection, *, dry_run: bool, **_kwargs: Any) -> None:
    all_migrations = _load_migrations()
    applied = _applied_versions(conn)
    pending = [m for m in all_migrations if m.version not in applied]

    if not pending:
        print("  Nothing to baseline.\n")
        return

    print(f"\n  Baselining {len(pending)} migration(s) (marking as applied, no SQL executed) ...\n")
    for m in pending:
        print(f"    [{m.version}]  {m.forward.name}")
        if not dry_run:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {TRACKING_TABLE} (version, name) VALUES (%s, %s)",
                    (m.version, m.forward.name),
                )
            conn.commit()

    print("\n  Done. Future `migrate.py up` calls will skip these.\n")


def cmd_create(args: argparse.Namespace) -> None:
    name: str = args.name
    today = date.today().strftime("%Y%m%d")
    version = f"{today}_{name}"
    up_path = MIGRATIONS_DIR / f"{version}.up.sql"
    down_path = MIGRATIONS_DIR / f"{version}.down.sql"

    if up_path.exists() or down_path.exists():
        sys.exit(f"  Error: migration files already exist for {version}")

    up_path.write_text(
        f"-- Migration: {version}\n"
        f"-- Description: {name.replace('_', ' ')}\n"
        f"-- Applied: \n"
        f"\n"
        f"-- TODO: write your forward migration here\n"
        f"\n"
        f"SELECT 1;\n",
        encoding="utf-8",
    )
    down_path.write_text(
        f"-- Rollback: {version}\n"
        f"-- Description: {name.replace('_', ' ')}\n"
        f"-- Applied: \n"
        f"\n"
        f"-- TODO: write your rollback migration here\n"
        f"\n"
        f"SELECT 1;\n",
        encoding="utf-8",
    )
    print(f"\n  Created:\n    {up_path}\n    {down_path}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="HCR2 database migration runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="up",
        choices=["up", "down", "status", "baseline", "create"],
        help="Command (default: up)",
    )
    parser.add_argument("name", nargs="?", help="Migration name (for `create` command)")
    parser.add_argument("--db-url", default=None, help="PostgreSQL DSN")
    parser.add_argument("--target", default=None, help="Target migration version (inclusive)")
    parser.add_argument("--steps", type=int, default=1, help="Number of rollback steps (for `down`)")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without executing")
    parser.add_argument("--no-color", action="store_true", help="(accepted for compat, ignored)")
    args = parser.parse_args()

    if args.command == "create":
        if not args.name:
            parser.error("`create` requires a migration name argument: migrate.py create <name>")
        cmd_create(args)
        return

    dsn = resolve_dsn(args.db_url)
    print(f"  Connecting to database ...")

    try:
        with psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5) as conn:
            _ensure_tracking_table(conn)
            if args.command == "status":
                cmd_status(conn)
            elif args.command == "up":
                cmd_up(conn, target=args.target, dry_run=args.dry_run)
            elif args.command == "down":
                cmd_down(conn, steps=args.steps, target=args.target, dry_run=args.dry_run)
            elif args.command == "baseline":
                cmd_baseline(conn, dry_run=args.dry_run)
    except psycopg.OperationalError as exc:
        sys.exit(f"\n  Could not connect to database: {exc}\n")


if __name__ == "__main__":
    main()
