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
9 passed
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
- `WC_TOKEN` HMAC verification.
- invalid token signature rejection.
- expired token rejection.
- admin allowlist helper.

Validated with static checks:

- PHP files parse.
- legacy JavaScript parses.
- historical SQLite snapshots are readable.
- historical icon coverage is complete.

Not validated:

- live PostgreSQL access,
- legacy PHP runtime behavior,
- migrated FastAPI business behavior,
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

- not executable because there is no local/staging PostgreSQL `.env` and no FastAPI repositories yet.

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
2. no FastAPI business endpoints,
3. no local PostgreSQL database configuration,
4. no verified production schema dump,
5. no local auth-token generation workflow,
6. no hCaptcha development or mock setup.

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
| Backend scaffold | High | Health, config and security tests pass. |
| Backend business migration | Low | Business endpoints are not implemented yet. |
| Frontend migration | Low | React frontend does not exist yet. |
| Admin migration | Low | Admin remains legacy-only. |
| Integration | Low | No migrated frontend and no migrated business APIs. |
| End-to-end readiness | Low | Missing frontend, DB config, secrets and business routes. |
