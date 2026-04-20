# Migrated System Functional Check

Date: 2026-04-20
Branch: `refactor/fastapi-react-migration`

This report records the first end-to-end functional verification of the migrated stack: PostgreSQL demo database, FastAPI backend, React/Vite frontend, and the remaining legacy PHP routes used for comparison.

## Runtime Context

Local services used:

- PostgreSQL demo database: `127.0.0.1:54329`
- Legacy PHP: `http://127.0.0.1:18080`
- FastAPI: `http://127.0.0.1:8000`
- React/Vite: `http://127.0.0.1:5173`

The stack was started with:

```powershell
.\scripts\dev\start-migrated-stack.ps1
```

The script starts the Docker dev stack, starts FastAPI with explicit development DB/auth/hCaptcha variables when needed, starts Vite when needed, and verifies that both FastAPI and the Vite proxy can read demo data.

## Commands Executed

Migrated stack functional smoke test:

```powershell
node scripts\dev\test_migrated_system.mjs
```

Result: passed.

Coverage:

- FastAPI health,
- FastAPI CORS for the local Vite origin,
- FastAPI `/api/v1` maps, vehicles, players, tuning parts, tuning setups, records, news and hCaptcha site key,
- Vite proxy for the same read-only API routes,
- FastAPI auth status for logged-out and signed development admin-cookie cases,
- React routes `/`, `/maps`, `/vehicles`, `/players`, `/tuning-parts`, `/tuning-setups`, `/records`, `/stats`, `/privacy`, `/maintenance`,
- rendered demo data in browser,
- logo asset loading,
- dark mode toggle setting `data-theme="dark"`.

Legacy regression check:

```powershell
python scripts\dev\test_legacy_regression.py
```

Result: passed.

Backend tests:

```powershell
cd backend
.\.venv\Scripts\python -m pytest
```

Result: `22 passed`.

Backend lint:

```powershell
cd backend
.\.venv\Scripts\python -m ruff check .
```

Result: passed.

Frontend build:

```powershell
cd frontend
npm run build
```

Result: passed.

PHP syntax checks:

```powershell
docker compose -f infra\dev\docker-compose.yml exec -T legacy sh -lc "php -l /app/php/api_records.php && php -l /app/php/delete_record.php"
```

Result: passed.

## Fixes Made

### FastAPI environment list parsing

Bug: FastAPI crashed when started with normal development environment variables such as `ALLOWED_DISCORD_IDS=dev-admin`. `pydantic-settings` attempted to parse list fields as JSON before the custom list validator ran.

Fix: list settings now use `NoDecode`, so comma/newline-separated legacy-style environment variables are accepted consistently.

Impact: FastAPI can now start with `.env.dev.example` values or the development start script and connect to the demo PostgreSQL database.

### Migrated stack startup

Bug: it was easy to have a FastAPI process listening on `8000` without the dev DB variables, which made `/health` pass while every data route failed with `Database error`.

Fix: added `scripts/dev/start-migrated-stack.ps1`, which starts and verifies the migrated stack and can restart FastAPI/Vite explicitly with `-RestartFastApi -RestartFrontend`.

Impact: local development now has a single command that proves the stack is actually wired, not merely listening.

### Migrated functional smoke test

Bug: no reusable test proved that FastAPI, Vite proxying, React rendering and demo data display worked together.

Fix: added `scripts/dev/test_migrated_system.mjs`, a dependency-free Node/Chrome DevTools smoke test for the migrated system.

Impact: the migrated read-only surface can now be checked with one command after starting the stack.

### Legacy `api_records.php` PostgreSQL compatibility

Bug: authorized `php/api_records.php` failed on PostgreSQL because the query selected many non-aggregated columns while grouping only by `wr.idRecord`.

Fix: grouped every selected non-aggregated column.

Impact: the endpoint now returns records against the local PostgreSQL demo database and can be used for comparison with the migrated API.

### Legacy `delete_record.php` auth include path

Bug: `php/delete_record.php` required `php/auth/check_auth.php`, which does not exist.

Fix: changed the include path to `../auth/check_auth.php`, matching the other authenticated PHP endpoints.

Impact: the route now reaches authorization and returns the legacy success shape for an authorized no-op delete test.

## Working Now

- PostgreSQL demo database initializes and serves representative seed data.
- FastAPI starts with development env values.
- FastAPI read-only public data routes return real PostgreSQL demo data.
- FastAPI legacy-compatible read-only routes return real PostgreSQL demo data.
- FastAPI auth status works for logged-out and signed development admin-token cases.
- CORS allows the local Vite origin.
- Vite proxies API calls to FastAPI.
- React public shell renders in a real browser.
- React public data pages render maps, vehicles, players, tuning parts, tuning setups and records.
- React stats page computes visible stats from FastAPI records.
- React dark mode toggle changes the legacy `data-theme` contract.
- Critical frontend assets load from `frontend/public`.
- Legacy regression checks pass against the same demo database.

## Still Not Fully Migrated

- Full legacy records UI behavior is not ported yet: filters, sorting, detailed record table formatting and export-like behaviors still belong to legacy JavaScript.
- News modal is not ported; the React header button remains disabled.
- Public submission modal and successful hCaptcha submission flow are not ported.
- Admin UI is not migrated to React/FastAPI.
- Mutating admin operations are not migrated to FastAPI.
- Browser-level visual parity checks are not automated yet.
- Production/staging PostgreSQL schema parity is not proven; the current validation uses the local inferred demo schema.

## Remaining Reasons

- The migration deliberately prioritized read-only public routes before write/admin behavior.
- hCaptcha success needs development credentials or an approved mock strategy.
- Discord OAuth login still depends on the external auth provider; local tests use signed development cookies.
- Visual parity needs stable screenshots/baselines before legacy UI can be replaced with confidence.
- Admin and write flows need separate migration passes because they mutate data and carry higher regression risk.

## Real Completion Level

| Area | Completion | Notes |
| --- | ---: | --- |
| Migrated backend implemented scope | 90% | Read-only public data, news, hCaptcha site key and auth status work against local PostgreSQL. |
| Overall backend migration | 45% | Write flows, admin operations and production schema validation remain. |
| Migrated frontend implemented scope | 80% | Current React pages render and load data; many legacy UI behaviors are still intentionally pending. |
| Overall frontend migration | 30% | The public shell exists, but full records UX, modals, submissions and admin are not ported. |
| Front/back/database integration for migrated read-only flows | 85% | Verified through FastAPI, Vite proxy and browser-rendered React pages. |
| Legacy still required | Yes | Admin, submissions, full public records interactions, news modal and visual parity baseline remain legacy-dependent. |
