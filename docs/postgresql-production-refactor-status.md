# PostgreSQL Production Refactor Status (2026-04-22)

## Objective
Move from mixed legacy schema (`_news`, `_pendingsubmission`, weak typing/nullability) to a professional, stable, evolutive canonical model with zero data loss.

## What Was Applied Safely In Production
- Ran data-safe backup before schema work:
  - `backups/postgres-pre-phase2-20260422-094144.dump`
- Applied `migrations/20260422_consolidate_news_and_pending.up.sql` successfully.
- Consolidated data to canonical tables:
  - `news`: 33 rows (copied/upserted from `_news`)
  - `pendingsubmission`: 285 rows (copied/upserted from `_pendingsubmission`)
- Tightened canonical constraints and defaults:
  - `news`: non-null `id/title/content/created_at`, default timestamp.
  - `pendingsubmission`: non-null core fields + status default/check.
- Added performance indexes:
  - `news_created_at_id_desc_idx`
  - `pendingsubmission_status_submitted_idx`
  - `pendingsubmission_map_vehicle_idx`
- Updated API read path:
  - `php/get_news.php` now reads canonical `news` only.

## Current Blocker For Full Legacy Table Hardening
The app role (`hcr2user`) does **not own** legacy core tables (`_map`, `_vehicle`, `_player`, `_tuningpart`, `_tuningsetup`, `_tuningsetupparts`, `_worldrecord`, `_news`, `_pendingsubmission`) which are owned by `postgres`.

Because of this, full in-place ALTER migrations on those legacy tables fail with:
- `must be owner of table _map`

## Why This Is Still Safe Right Now
- No destructive changes were applied to legacy tables.
- Canonical tables now contain complete migrated rows for news and pending submissions.
- Application endpoints continue working after migration and now use the canonical news source.
- Legacy data remains available as rollback reference.

## Final Step To Unlock Full Refactor
Run one ownership alignment once as `postgres` (or a superuser), then execute normalization migration:

```sql
ALTER TABLE _map OWNER TO hcr2user;
ALTER TABLE _vehicle OWNER TO hcr2user;
ALTER TABLE _player OWNER TO hcr2user;
ALTER TABLE _tuningpart OWNER TO hcr2user;
ALTER TABLE _tuningsetup OWNER TO hcr2user;
ALTER TABLE _tuningsetupparts OWNER TO hcr2user;
ALTER TABLE _worldrecord OWNER TO hcr2user;
ALTER TABLE _news OWNER TO hcr2user;
ALTER TABLE _pendingsubmission OWNER TO hcr2user;
```

Then rerun:
- `migrations/20260422_normalize_postgresql_schema.up.sql`
- `tests/post_migration_integrity.php`

## Validation Commands Used
- API smoke check: `php -r '$_GET["limit"]=12; include "php/get_news.php";'`
- Canonical row counts: SQL count checks on `news`, `_news`, `pendingsubmission`, `_pendingsubmission`
- Canonical integrity test: `tests/canonical_tables_integrity.php`
