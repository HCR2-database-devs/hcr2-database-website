# Main Alignment Report

Date: 2026-04-22

## Compared Branches

- Refactor branch: `refactor/fastapi-react-migration`
- Target branch: `origin/main`
- Merge base: `ff55f47629d4100f9b80cd0ad5cfee7090cf4972`

`main` kept evolving the legacy PHP runtime while the refactor branch moved the product to FastAPI, React/Vite and PostgreSQL. A direct merge would have restored the PHP root layout and removed major parts of the refactor, so the useful `main` changes were ported into the new architecture instead.

## Important Differences From Main

- `main` normalized the PostgreSQL database to lowercase `snake_case` names.
- `main` consolidated duplicate logical tables into canonical `news` and `pending_submission`.
- `main` replaced application-side `MAX(id)+1` allocation with PostgreSQL sequences and `RETURNING`.
- `main` kept frontend-compatible camelCase JSON keys for public PHP endpoints.
- The refactor branch kept FastAPI/React as the official runtime and the old PHP app isolated under `to_delete/`.

## Changes Integrated Into The Refactor

- Added the SQL migrations from `main` under `migrations/`.
- Updated the local dev schema and seed data in `infra/dev/postgres/init/`.
- Updated FastAPI repositories and services to use canonical tables:
  - `map`
  - `vehicle`
  - `player`
  - `tuning_part`
  - `tuning_setup`
  - `tuning_setup_part`
  - `world_record`
  - `pending_submission`
  - `news`
- Preserved camelCase response keys for public data and PHP-compatible endpoints.
- Ported `/php/api_records.php` to FastAPI with API key checks, filters, limit and offset.
- Added FastAPI compatibility routes for the legacy admin PHP paths still likely to be hit during transition.
- Added `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `DB_SCHEMA` and `PGSCHEMA` support.
- Updated tests and the system smoke script for the canonical schema.

## Conflict Decisions

- The PHP root layout from `main` was not restored because it contradicts the refactor target.
- Runtime code now uses the canonical schema only; legacy underscore tables are migration inputs, not application dependencies.
- Frontend-facing responses keep camelCase keys even though SQL uses `snake_case`.
- Browser-based restore and arbitrary SQL import remain out of scope because they are destructive database operations.
- FastAPI application backups remain supported and now dump canonical tables plus sequence positions.

## Sensitive Files Updated

- `backend/app/api/compat.py`
- `backend/app/api/v1/public.py`
- `backend/app/core/config.py`
- `backend/app/db/session.py`
- `backend/app/repositories/public_data.py`
- `backend/app/repositories/news.py`
- `backend/app/services/admin_service.py`
- `backend/app/services/public_data_service.py`
- `backend/app/services/public_submission_service.py`
- `infra/dev/postgres/init/001_schema.sql`
- `infra/dev/postgres/init/002_seed_demo.sql`
- `scripts/dev/test_system_smoke.mjs`
- `migrations/*.sql`

## Validation

Passed:

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m pytest
python -m compileall app tests

cd ..\frontend
npm run build

cd ..
git diff --check
.\scripts\dev\reset-dev-database.ps1
.\scripts\dev\start-app-stack.ps1 -RestartFastApi -RestartFrontend
node .\scripts\dev\test_system_smoke.mjs
```

The smoke test passed after shortening generated admin test names so they respect the production schema limits from `main`:

- map name: 19 chars max
- vehicle name: 16 chars max
- tuning part name: 17 chars max

## Watch Points

- Rehearse production migrations on a staging clone.
- Validate production data constraints after migration.
- Check real external `/php/api_records.php` clients.
- Check SVG upload permissions on the deployed filesystem.
