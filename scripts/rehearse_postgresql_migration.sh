#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DB=""
TMP_SCHEMA=""

cleanup() {
  if [[ -n "$TMP_DB" ]]; then
    dropdb --if-exists "$TMP_DB" >/dev/null 2>&1 || true
  fi
  if [[ -n "$TMP_SCHEMA" ]]; then
    psql -v ON_ERROR_STOP=1 "$DB_NAME" -c "DROP SCHEMA IF EXISTS \"$TMP_SCHEMA\" CASCADE" >/dev/null 2>&1 || true
    psql -v ON_ERROR_STOP=1 "$DB_NAME" -c "DROP TABLE IF EXISTS legacy._news_archived; DROP TABLE IF EXISTS legacy._pendingsubmission_archived;" >/dev/null 2>&1 || true
    psql -v ON_ERROR_STOP=1 "$DB_NAME" -c "DROP SCHEMA IF EXISTS legacy" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

cd "$ROOT_DIR"

eval "$(
php -r '
require "auth/config.php";
$c = get_database_config();
foreach (["host" => "PGHOST", "port" => "PGPORT", "user" => "PGUSER", "pass" => "PGPASSWORD", "dbname" => "DB_NAME"] as $key => $env) {
    if (isset($c[$key]) && $c[$key] !== null && $c[$key] !== "") {
        echo "export $env=" . escapeshellarg((string)$c[$key]) . ";\n";
    }
}
'
)"

if [[ -z "${DB_NAME:-}" ]]; then
  echo "DB_NAME could not be resolved from environment" >&2
  exit 1
fi

TMP_DB="${DB_NAME}_rehearsal_$(date +%s)_$$"

echo "Creating temporary database ${TMP_DB}"
if createdb "$TMP_DB" 2>/tmp/hcr2_createdb_error.log; then
  echo "Cloning current database into ${TMP_DB}"
  pg_dump --no-owner --no-acl "$DB_NAME" | psql -v ON_ERROR_STOP=1 "$TMP_DB" >/dev/null

  echo "Applying up migration"
  psql -v ON_ERROR_STOP=1 "$TMP_DB" -f migrations/20260422_normalize_postgresql_schema.up.sql >/dev/null

  echo "Running post-migration integrity tests"
  DB_NAME="$TMP_DB" PGDATABASE="$TMP_DB" php tests/post_migration_integrity.php

  echo "Running API dry-run endpoint campaign on migrated schema"
  DB_NAME="$TMP_DB" PGDATABASE="$TMP_DB" ./scripts/dry_run_api_check.sh

  echo "Checking down migration"
  psql -v ON_ERROR_STOP=1 "$TMP_DB" -f migrations/20260422_normalize_postgresql_schema.down.sql >/dev/null
else
  echo "createdb unavailable; falling back to isolated schema rehearsal"
  cat /tmp/hcr2_createdb_error.log >&2
  TMP_DB=""
  TMP_SCHEMA="migration_rehearsal_$(date +%s)_$$"
  psql -v ON_ERROR_STOP=1 "$DB_NAME" -c "CREATE SCHEMA \"$TMP_SCHEMA\"" >/dev/null
  for table in _map _vehicle _player _worldrecord _tuningpart _tuningsetup _tuningsetupparts news _news pendingsubmission _pendingsubmission; do
    psql -v ON_ERROR_STOP=1 "$DB_NAME" -c "CREATE TABLE \"$TMP_SCHEMA\".\"$table\" (LIKE public.\"$table\" INCLUDING ALL); INSERT INTO \"$TMP_SCHEMA\".\"$table\" SELECT * FROM public.\"$table\";" >/dev/null
  done

  echo "Applying up migration in schema ${TMP_SCHEMA}"
  PGOPTIONS="-c search_path=${TMP_SCHEMA},public" psql -v ON_ERROR_STOP=1 "$DB_NAME" -f migrations/20260422_normalize_postgresql_schema.up.sql >/dev/null

  echo "Running post-migration integrity tests"
  DB_SCHEMA="$TMP_SCHEMA" php tests/post_migration_integrity.php

  echo "Running API dry-run endpoint campaign on migrated schema"
  DB_SCHEMA="$TMP_SCHEMA" ./scripts/dry_run_api_check.sh

  echo "Checking down migration"
  PGOPTIONS="-c search_path=${TMP_SCHEMA},public" psql -v ON_ERROR_STOP=1 "$DB_NAME" -f migrations/20260422_normalize_postgresql_schema.down.sql >/dev/null
fi

echo "Migration rehearsal completed."
