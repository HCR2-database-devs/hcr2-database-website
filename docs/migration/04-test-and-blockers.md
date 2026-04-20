# 04 - Test and Blockers

Date: 2026-04-20

This document records what is currently validated, what is not testable yet, and what blocks full end-to-end validation.

## Tests Executed

Backend unit tests:

```powershell
cd backend
.\.venv\Scripts\python -m pytest
```

Latest known result:

```text
21 passed
```

Backend lint:

```powershell
cd backend
.\.venv\Scripts\python -m ruff check .
```

Latest known result:

```text
All checks passed!
```

FastAPI startup smoke test:

```powershell
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8123
```

Verified response:

```text
GET /health -> 200
{"status":"ok","service":"HCR2 Records API","version":"0.1.0"}
```

FastAPI compatibility smoke test:

```text
GET /php/load_data.php?type=unknown -> 200
{"error":"Invalid data type"}
```

Frontend install:

```powershell
cd frontend
npm install
```

Latest known result:

```text
added 77 packages
found 0 vulnerabilities
```

Frontend build:

```powershell
cd frontend
npm run build
```

Latest known result:

```text
tsc -b && vite build
built successfully
```

PHP syntax validation:

```powershell
Get-ChildItem -Recurse -File -Filter *.php | ForEach-Object { php -l $_.FullName }
```

Latest known result:

- all PHP files passed syntax validation.

Legacy JavaScript syntax validation:

```powershell
node --check js\script.js
```

Latest known result:

- no syntax errors reported.

Historical SQLite snapshot readability:

- latest snapshot was readable,
- table counts were collected,
- icon coverage against map/vehicle/tuning-part names was complete.

Legacy runtime regression against local PostgreSQL demo data:

```powershell
.\scripts\dev\reset-dev-database.ps1
.\scripts\dev\start-dev-stack.ps1
python scripts\dev\test_legacy_regression.py
```

Latest known result:

- public index, CSS and logo passed,
- maintenance status passed,
- read-only public data routes for maps, vehicles, players, tuning parts, tuning setups and records passed,
- news and hCaptcha site-key routes passed,
- auth status passed for logged-out and signed development admin-token cases,
- admin pending list and integrity check passed,
- known PostgreSQL/API issues are marked as expected failures in `legacy-regression-check.md`.

## What Is Actually Validated

Validated with tests:

- FastAPI app imports.
- health routes respond.
- environment list parsing.
- PostgreSQL DSN construction.
- `DATABASE_URL` precedence.
- database connection helper rejects missing configuration.
- `WC_TOKEN` HMAC verification.
- invalid token signature rejection.
- expired token rejection.
- admin allowlist helper.
- public data service dispatch for maps, vehicles, players, tuning parts, tuning setups and records.
- legacy `load_data.php` compatibility errors for missing and invalid types.
- clean `/api/v1/maps` route wiring.
- legacy news route wiring.
- legacy hCaptcha site key route wiring.
- legacy auth status logged-out shape.
- React/Vite/TypeScript production build.
- React Router and TanStack Query compile successfully.
- local PostgreSQL dev schema can be initialized and seeded.
- legacy PHP runtime can read the local PostgreSQL demo data.
- legacy admin read-only status can be checked with a signed development token.

Validated with static checks:

- PHP files parse.
- legacy JavaScript parses.
- historical SQLite snapshots are readable.
- historical icon coverage is complete.

Not validated:

- production PostgreSQL access,
- migrated FastAPI SQL behavior against production/staging data,
- React visual parity,
- full React UI behavior,
- migrated admin behavior,
- successful hCaptcha submission behavior,
- external Discord login,
- end-to-end flows.

## Tests Not Executable Yet

Production database integration:

- not executable because there is no verified production schema dump and no production/staging fixture database. A local PostgreSQL demo database now exists for development checks.

Legacy browser end-to-end:

- not fully executable yet because browser-level admin navigation and full public submission success still need safe hCaptcha/auth handling.

hCaptcha:

- successful submission is not executable without development hCaptcha credentials or mocked verification.

Discord OAuth:

- not executable locally because login depends on `https://auth.hcr2.xyz/login` and a valid signed cookie.

Visual regression:

- not executable because React UI parity pages and visual baselines are not complete yet.

## Blocking Items

Critical blockers:

1. no verified production schema dump,
2. no hCaptcha development or mock setup,
3. no database-backed contract tests for the migrated FastAPI read-only routes against representative PostgreSQL data,
4. no visual regression baseline for React parity,
5. known legacy PostgreSQL incompatibility in `php/api_records.php`,
6. known legacy include-path issue in `php/delete_record.php`.

Important non-critical blockers:

1. visual regression workflow is not defined,
2. PostgreSQL backup/import/restore behavior is not finalized,
3. browser-level admin checks are not automated,
4. production casing behavior must be confirmed before changing PHP aliases.

## Needed From Project Owner

To fully validate the migration, the project needs:

- production schema dump or read-only schema inspection,
- representative seed data or sanitized fixtures,
- hCaptcha development credentials or approval to mock verification,
- decision on whether historical SQLite backups should remain in Git,
- decision on PostgreSQL backup/import/restore expectations.

## Confidence Levels

| Area | Confidence | Reason |
| --- | --- | --- |
| Legacy preservation | High | Legacy files remain in place and parse. |
| Documentation | High | Consolidated runbooks exist and are English-only. |
| Backend scaffold | High | Health, config, security and route wiring tests pass. |
| Backend read-only migration | Medium | Routes, services and SQL repositories exist; production/staging database validation is still missing. |
| Backend write/admin migration | Low | Public submissions and admin features are not implemented yet. |
| Frontend scaffold | Medium | React/Vite builds and initial routes exist; full UI parity is pending. |
| Admin migration | Low | Admin remains legacy-only. |
| Integration | Medium-Low | Local legacy/PostgreSQL integration exists; migrated frontend/backend integration remains incomplete. |
| End-to-end readiness | Low | Missing frontend parity, production schema validation, hCaptcha handling and browser-level validation. |
