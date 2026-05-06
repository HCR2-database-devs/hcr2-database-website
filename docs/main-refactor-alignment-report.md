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

## Incremental Sync - 2026-05-06

`origin/main` received additional legacy PHP updates after the original alignment. The raw
`HEAD..origin/main` diff still includes the old PHP application shape, so those changes were reviewed
from the merge base and ported selectively into the FastAPI/React refactor.

### New Differences Identified

- `main` added admin news editing and deletion through `auth/edit_news.php` and
  `auth/delete_news.php`.
- `main` exposed the submitter IP in pending admin submissions.
- `main` tightened `/php/api_records.php` explicit filters so `map`, `vehicle`/`car`, `player` and
  `country` are exact case-insensitive matches, while free-text `q` remains a partial search.
- `main` expanded public site expectations around questionable records, staff credits, partnership
  content for Adam's HCR2 Bot and the Tipeee support link.

### Changes Ported

- Added FastAPI admin news update/delete services and `/api/v1/admin/news/{id}` routes.
- Added compatibility routes for `/auth/edit_news.php` and `/auth/delete_news.php`.
- Kept admin news creation compatible and now returns the created `id`, which lets tests and clients
  safely edit/delete the inserted item.
- Included `submitterIp` in pending admin payloads and rendered it in the React admin table.
- Updated record search filtering to match `main` exact-match behavior and restored the `car` alias.
- Added React admin controls for editing and deleting site news.
- Updated the home page and footer with the newer moderation, staff, partnership and support
  content, implemented in the refactored component structure instead of copying legacy HTML.

### Conflict Decisions

- The legacy PHP files from `main` were not merged back into the runtime. Their behavior was ported
  into FastAPI and React.
- `/php/api_records.php` on `main` currently omits `idRecord` from its select list; the refactor keeps
  `idRecord` because other public and admin contracts already depend on canonical record IDs.
- The Tipeee integration is represented as a normal external support link in React, without injecting
  the legacy third-party widget script into the SPA.

### Validation

Passed:

```powershell
backend\.venv\Scripts\python.exe -m ruff check backend\app backend\tests
backend\.venv\Scripts\python.exe -m pytest backend\tests
cd frontend; npm run build
git diff --check
node .\scripts\dev\test_system_smoke.mjs
```

The smoke test covered public API/proxy routes, admin CRUD, news post/edit/delete, maintenance,
backup download/delete, public UI routes, records filtering, news modal, public submission modal,
dark mode and the admin page.
