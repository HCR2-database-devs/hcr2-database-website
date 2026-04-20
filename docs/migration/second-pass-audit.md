# Second-Pass Migration Audit

Date: 2026-04-20
Branch: `refactor/fastapi-react-migration`

This second-pass audit compares the current migration branch against the legacy PHP/HTML/CSS/JavaScript application. It focuses on what has actually been migrated, what is still legacy-only, what exists but is not wired yet, and what blocks end-to-end validation.

## Executive Result

The migration is not functionally complete yet.

The repository currently contains:

- the full legacy application,
- migration documentation,
- an isolated FastAPI backend scaffold,
- backend health checks,
- backend configuration and security helpers,
- backend tests for health, configuration parsing and token helpers.

The repository does not yet contain:

- a React/Vite/TypeScript frontend,
- migrated public data endpoints in FastAPI,
- migrated admin endpoints in FastAPI,
- migrated public UI components,
- migrated admin UI components,
- front/back integration wiring,
- a runnable end-to-end development setup.

This is not a failure of the current branch; it means the branch is still in the early stabilization/backend-scaffold phase, not in a completed migration phase.

## What Has Been Migrated or Prepared Correctly

### Documentation

The migration documentation exists in English under `docs/migration/`:

- `existing-architecture-audit.md`
- `routes-and-flows.md`
- `backend-mapping.md`
- `frontend-mapping.md`
- `database-mapping.md`
- `migration-plan.md`

This documentation covers the legacy architecture, route inventory, backend mapping, frontend mapping, database mapping and migration plan.

### Backend Scaffold

The new backend exists under `backend/`.

Implemented:

- FastAPI application factory in `backend/app/main.py`.
- Versioned API router in `backend/app/api/v1/router.py`.
- Health endpoint at `/health`.
- Health endpoint at `/api/v1/health`.
- Pydantic settings in `backend/app/core/config.py`.
- Legacy-compatible environment list parsing.
- `WC_TOKEN` HMAC JWT verification helper in `backend/app/core/security.py`.
- Admin allowlist helper.
- Database configuration object in `backend/app/db/session.py`.
- Pytest and Ruff configuration in `backend/pyproject.toml`.

### Backend Tests

Backend tests now cover:

- root health endpoint,
- versioned health endpoint,
- environment list parsing,
- PostgreSQL DSN construction,
- `DATABASE_URL` precedence,
- valid `WC_TOKEN` signature verification,
- invalid signature rejection,
- expired token rejection,
- Discord admin allowlist behavior.

### Environment Examples

The root `.env.example` now includes both legacy and backend scaffold variables:

- `APP_NAME`
- `APP_VERSION`
- `ENVIRONMENT`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASS`
- `DATABASE_URL`
- `AUTH_SHARED_SECRET`
- `ALLOWED_DISCORD_IDS`
- `API_KEYS`
- `HCAPTCHA_SITE_KEY`
- `HCAPTCHA_SECRET_KEY`
- `CORS_ORIGINS`

The previous inline `AUTH_SHARED_SECRET= #login handler` example has been replaced by a separate comment and an empty value.

### Legacy App Preservation

The legacy application is still present and has not been destructively modified:

- `index.php`
- `index.html`
- `php/`
- `auth/`
- `js/script.js`
- `css/style.css`
- `img/`

This is important because the migrated backend and frontend do not yet replace the legacy functionality.

### Assets

Assets were checked against the latest SQLite snapshot:

- Map names: 22 database rows, 22 SVG icons, 0 missing.
- Vehicle names: 34 database rows, 34 SVG icons, 0 missing.
- Tuning part names: 19 database rows, 19 SVG icons, 0 missing.

This check only validates the historical SQLite snapshot, not the live PostgreSQL production data.

## What Is Still Missing

### Frontend

There is no `frontend/` directory.

Missing:

- Vite scaffold.
- React app.
- TypeScript configuration.
- React Router setup.
- TanStack Query setup.
- Public page components.
- Records table component.
- Filters, sorting and CSV export port.
- Stats port.
- Public submission modal port.
- News modal port.
- Privacy page route.
- Maintenance page route.
- Admin React UI.
- Frontend tests.
- Frontend build, lint and type-check scripts.

### Backend API

FastAPI currently exposes only:

- `/health`
- `/api/v1/health`
- OpenAPI documentation routes.

All business endpoints are still legacy-only.

Missing FastAPI equivalents:

- public data endpoints,
- records API-key endpoint,
- auth status/logout compatibility endpoints,
- public hCaptcha site key endpoint,
- public submission endpoint,
- public news endpoint,
- admin record endpoints,
- admin catalog endpoints,
- pending submission endpoints,
- admin news posting endpoint,
- maintenance endpoints,
- admin operations endpoints.

### Backend Business Logic

Still not ported:

- database queries from `php/load_data.php`,
- record filtering in `php/api_records.php`,
- hCaptcha verification from `php/public_submit.php`,
- public submission rate limiting,
- pending submission approval/rejection,
- record replacement logic,
- record deletion,
- questionable status updates,
- tuning setup assignment,
- map/vehicle/tuning part creation,
- SVG upload validation,
- tuning setup duplicate detection,
- maintenance flag behavior,
- news creation and retrieval,
- admin backup/integrity behavior.

### Database Integration

The backend can build a DSN string but does not yet open database connections or run queries.

Missing:

- connection lifecycle,
- repository implementations,
- schema models or typed query results,
- contract tests using database fixtures,
- production schema validation,
- seed/test data strategy.

### Admin

The admin area is entirely legacy-only.

Missing in the migrated stack:

- admin route protection in FastAPI,
- admin API endpoints,
- React admin page,
- admin forms,
- admin pending submissions,
- admin backup/integrity UI,
- admin maintenance controls,
- admin news posting.

### Integration

There is no migrated front/back integration yet.

Missing:

- frontend API client,
- Vite proxy,
- CORS validation against a real frontend,
- route compatibility aliases,
- end-to-end startup command,
- end-to-end test workflow.

## Existing but Not Wired

The following pieces exist but are not connected to product behavior yet:

- `backend/app/core/security.py`: token helpers exist, but no FastAPI auth dependency or auth route consumes them.
- `backend/app/db/session.py`: database config exists, but no repository opens a connection.
- `backend/app/repositories/`: package exists, but no repositories are implemented.
- `backend/app/services/`: package exists, but no services are implemented.
- `backend/app/schemas/`: package exists, but no Pydantic response/request schemas are implemented.
- `backend/app/models/`: package exists, but no models are implemented.
- `CORS_ORIGINS`: setting exists, but there is no React frontend to exercise it.
- `/health` and `/api/v1/health`: endpoints work, but no frontend consumes them.

## Corrections Made During This Second Pass

Low-risk corrections made:

- Expanded the root `.env.example` to include the backend scaffold variables.
- Cleaned the `AUTH_SHARED_SECRET` example so copying `.env.example` does not accidentally create a non-empty placeholder secret.
- Added backend tests for configuration parsing and DSN construction.
- Added backend tests for `WC_TOKEN` verification and admin allowlist behavior.

No legacy behavior or visual output was changed.

## Confidence Levels

| Area | Confidence | Reason |
| --- | --- | --- |
| Legacy preservation | High | Legacy files remain in place and PHP syntax checks pass. |
| Migration documentation | High | Documentation is present, English-only in project docs, and maps the current state. |
| Backend scaffold | High | FastAPI imports, starts and health endpoints respond. Tests pass. |
| Backend business migration | Low | Only health/config/security scaffolding exists; business endpoints are not ported. |
| Frontend migration | Low | No React/Vite frontend exists yet. |
| Admin migration | Low | Admin remains entirely legacy-only. |
| Front/back integration | Low | No frontend and no business API routes are available to integrate. |
| End-to-end readiness | Low | Missing database config, secrets, frontend scaffold and migrated routes. |

## Recommended Next Step

The next safe implementation step is to port the public read-only data endpoints into FastAPI with strict legacy-compatible JSON contracts:

1. maps
2. vehicles
3. players
4. tuning parts
5. tuning setups
6. records

Do not start the React migration until these read-only backend contracts are implemented and testable.
