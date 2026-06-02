# PostgreSQL normalization report

Date: 2026-04-22

## Summary

This change adds a real PostgreSQL migration path for the imported SQLite-era schema, removes application-side `MAX(id)+1` id generation, consolidates duplicated logical tables, and adds post-migration tests plus a rehearsal script.

The production database was not migrated during this work. Verification was performed on an isolated rehearsal schema cloned from the current live tables because the database user does not have `CREATE DATABASE` permission.

## Schema Audit

Current production findings before migration:

| Table | Current issue | Migration action |
| --- | --- | --- |
| `_map` | no PK, nullable id/name, `smallint`, no sequence | convert id to integer, add sequence/default, PK, unique name, NOT NULL |
| `_vehicle` | no PK, nullable id/name, `smallint`, no sequence | convert id to integer, add sequence/default, PK, unique name, NOT NULL |
| `_player` | no PK, nullable id/name/country, `smallint`, no sequence | convert id to integer, add sequence/default, PK, unique name, NOT NULL |
| `_tuningpart` | no PK, nullable id/name, `smallint`, no sequence | convert id to integer, add sequence/default, PK, unique name, NOT NULL |
| `_tuningsetup` | no PK, nullable id, `smallint`, no sequence | convert id to integer, add sequence/default, PK |
| `_tuningsetupparts` | no PK/FK, nullable pair | add composite PK and FK constraints |
| `_worldrecord` | no `idRecord`, no PK/FK, string setup id, weak booleans | add `idRecord` sequence/PK, convert setup id to integer, add FK/check/unique current constraints |
| `news` / `_news` | duplicate logical tables, real rows in `_news` | backfill into `news`, keep `news` canonical, archive `_news` |
| `pendingsubmission` / `_pendingsubmission` | duplicate logical tables, real rows in `_pendingsubmission`, canonical missing tuning parts | add `tuningparts`, backfill into `pendingsubmission`, archive `_pendingsubmission` |

Data compatibility checks found no duplicate ids, no duplicate reference names, no duplicate current records by map/vehicle, and no FK orphans in the current dataset.

## Migrations

Added:

- `migrations/20260422_normalize_postgresql_schema.up.sql`
- `migrations/20260422_normalize_postgresql_schema.down.sql`

The up migration:

- validates data preconditions with explicit exceptions;
- creates PostgreSQL sequences and defaults;
- adds primary keys and foreign keys;
- adds `idRecord` to `_worldrecord`;
- adds a partial unique index on current records: `_worldrecord("idMap", "idVehicle") WHERE current = 1`;
- consolidates `_news` into `news`;
- consolidates `_pendingsubmission` into `pendingsubmission`;
- archives old duplicate tables under `legacy`.

The down migration is best-effort and non-destructive: it removes constraints/defaults/idRecord and restores archived legacy tables where possible. It intentionally does not delete canonical `news` or `pendingsubmission` rows.

## Code Changes

Application inserts now rely on PostgreSQL defaults and `RETURNING`:

- maps, vehicles, players, tuning parts, tuning setups, world records;
- pending submissions;
- news posts.

Removed all application-side `MAX(...)+1` id allocation from `php/`, `auth/`, `scripts/`, and `tests/`.

The API now uses:

- real numeric `idRecord`;
- canonical `news`;
- canonical `pendingsubmission`;
- `DB_SCHEMA`/`PGSCHEMA` support for isolated schema rehearsals.

`API_DRY_RUN=1` remains supported and now also bypasses hCaptcha/rate-limit effects in the endpoint campaign while preserving rollback behavior for writes.

## Tests

Added:

- `tests/post_migration_integrity.php`
- `scripts/rehearse_postgresql_migration.sh`
- updated `scripts/dry_run_api_check.sh`

Covered cases:

- PK/FK/unique constraint presence;
- id generation through PostgreSQL sequences;
- record creation;
- duplicate current record rejection;
- FK violation rejection;
- deletion blocked when dependencies exist;
- pending submission creation and status transition;
- full endpoint campaign in `API_DRY_RUN=1`;
- up and down migration rehearsal.

## Verification

Commands run:

```bash
find . -maxdepth 3 -type f -name '*.php' -print0 | xargs -0 -n1 php -l
./scripts/rehearse_postgresql_migration.sh
rg -n "MAX\\(|COALESCE\\(MAX|MAX\\s*\\(" php auth scripts tests -g '*.php' -g '*.sh'
```

Results:

- PHP syntax checks: passed.
- Migration rehearsal: passed.
- Endpoint dry-run campaign on migrated rehearsal schema: passed.
- `MAX(id)+1` search in application/test scripts: no matches.

Note: `createdb` is not allowed for the current DB user, so the rehearsal script automatically used a cloned schema inside the same database and cleaned it afterward.

## Operational Notes

Recommended rollout:

1. Take a verified PostgreSQL backup.
2. Run `./scripts/rehearse_postgresql_migration.sh` in staging.
3. Apply `migrations/20260422_normalize_postgresql_schema.up.sql` during a low-traffic window.
4. Deploy this code at the same time as the migration because it expects real `idRecord`, canonical `news`, and canonical `pendingsubmission`.
5. Run `API_DRY_RUN=1 ./scripts/dry_run_api_check.sh` after migration.
6. Run `php tests/post_migration_integrity.php` against staging or a disposable clone.

Residual risks:

- The down migration restores archived legacy tables as plain data tables; it is meant for rollback safety, not as a preferred long-term schema.
- The API still uses legacy mixed-case table/column names for core imported tables. A later migration could rename them to snake_case, but that was intentionally avoided here to reduce application blast radius.
