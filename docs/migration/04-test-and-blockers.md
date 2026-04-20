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

Validated with static checks:

- PHP files parse.
- legacy JavaScript parses.
- historical SQLite snapshots are readable.
- historical icon coverage is complete.

Not validated:

- live PostgreSQL access,
- legacy PHP runtime behavior,
- migrated FastAPI SQL behavior against production/staging data,
- frontend build,
- React UI,
- admin migration,
- hCaptcha behavior,
- external Discord login,
- end-to-end flows.

## Tests Not Executable Yet

Frontend install/build/type-check:

- not executable because `frontend/` and `package.json` do not exist yet.

Database integration:

- not executable because there is no local/staging PostgreSQL `.env`, no verified production schema dump and no sanitized fixture database.

Legacy runtime end-to-end:

- not executable without real `.env` values and a PostgreSQL database.

hCaptcha:

- not executable without development hCaptcha credentials or mocked verification.

Discord OAuth:

- not executable locally because login depends on `https://auth.hcr2.xyz/login` and a valid signed cookie.

Visual regression:

- not executable because React UI does not exist yet.

## Blocking Items

Critical blockers:

1. no React frontend scaffold,
2. no local PostgreSQL database configuration,
3. no verified production schema dump,
4. no local auth-token generation workflow,
5. no hCaptcha development or mock setup,
6. no database-backed contract tests for the new read-only routes.

Important non-critical blockers:

1. no Docker/compose setup,
2. no seed or fixture script,
3. no visual regression workflow,
4. PostgreSQL backup/import/restore behavior is not finalized.

## Needed From Project Owner

To fully validate the migration, the project needs:

- safe PostgreSQL credentials for local or staging testing,
- production schema dump or read-only schema inspection,
- representative seed data or sanitized fixtures,
- `AUTH_SHARED_SECRET` for local signed-cookie tests or a development auth plan,
- hCaptcha development credentials or approval to mock verification,
- decision on whether historical SQLite backups should remain in Git,
- decision on PostgreSQL backup/import/restore expectations.

## Confidence Levels

| Area | Confidence | Reason |
| --- | --- | --- |
| Legacy preservation | High | Legacy files remain in place and parse. |
| Documentation | High | Consolidated runbooks exist and are English-only. |
| Backend scaffold | High | Health, config, security and route wiring tests pass. |
| Backend read-only migration | Medium | Routes, services and SQL repositories exist; live database validation is still missing. |
| Backend write/admin migration | Low | Public submissions and admin features are not implemented yet. |
| Frontend migration | Low | React frontend does not exist yet. |
| Admin migration | Low | Admin remains legacy-only. |
| Integration | Low | No migrated frontend and no live database-backed validation. |
| End-to-end readiness | Low | Missing frontend, DB config, secrets and browser-level validation. |
