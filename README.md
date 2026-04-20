# HCR2 Adventure Records Database

Unofficial Hill Climb Racing 2 adventure records website and database.

This branch is currently being migrated from a legacy PHP, HTML, CSS and vanilla JavaScript application toward a cleaner architecture based on:

- FastAPI for the backend API
- React, Vite and TypeScript for the frontend
- React Router for frontend routing
- TanStack Query for API calls and caching
- PostgreSQL for the active database

The migration is intentionally progressive. The legacy application is still present and must keep working until each replacement part is verified.

## Current Refactor Status

The refactor has started with the safest pieces:

- Consolidated migration runbooks in `docs/migration/`.
- Git tracking cleanup for local database snapshots.
- Isolated FastAPI backend in `backend/`.
- Centralized backend configuration.
- Basic security helpers for the existing `WC_TOKEN` model.
- PostgreSQL connection helper using the existing environment contract.
- Repository/service/schema layers for public read-only data.
- Legacy-compatible FastAPI routes for public data, auth status/logout, news and hCaptcha site key.
- Clean `/api/v1/...` routes for the future React frontend.
- React/Vite/TypeScript frontend scaffold in `frontend/`.
- React Router, TanStack Query, legacy CSS/assets and initial public views.
- Backend tests and Ruff linting.
- Frontend install and production build.

No legacy PHP file has been removed yet.
No public visual output has been intentionally changed.

## Repository Layout

```text
.
|-- backend/                 # New FastAPI backend scaffold
|   |-- app/
|   |   |-- api/             # Versioned API routers
|   |   |-- core/            # Settings, errors and security helpers
|   |   |-- db/              # Database configuration and connection helpers
|   |   |-- models/          # Future database models
|   |   |-- repositories/    # SQL data access layer
|   |   |-- schemas/         # Pydantic schemas
|   |   |-- services/        # Business/service layer
|   |   `-- utils/
|   |-- tests/
|   |-- pyproject.toml
|   `-- README.md
|-- frontend/                # New React/Vite/TypeScript frontend scaffold
|   |-- public/              # Copied legacy CSS and assets for parity-first migration
|   |-- src/
|   |-- package.json
|   `-- vite.config.ts
|-- docs/
|   `-- migration/           # Migration audit, mappings and plan
|-- auth/                    # Legacy auth/admin PHP endpoints
|-- php/                     # Legacy PHP endpoints and admin page
|-- css/                     # Legacy styles
|-- js/                      # Legacy public JavaScript
|-- img/                     # Public assets and icons
|-- backups/                 # Local-only historical SQLite snapshots, ignored by Git
|-- index.php                # Legacy public entry point
|-- index.html               # Legacy public page
|-- maintenance.html
`-- privacy.html
```

## Migration Documentation

The migration documentation is in `docs/migration/`:

- `01-current-state.md`
- `02-target-architecture.md`
- `03-migration-roadmap.md`
- `04-test-and-blockers.md`
- `history-cleanup-plan.md`

These files define the baseline behavior that must be preserved while the project is rebuilt.

## Migrated Backend

The new backend lives in `backend/`.

Implemented so far:

- FastAPI app factory.
- `/health`
- `/api/v1/health`
- Pydantic settings.
- Environment parsing compatible with the legacy `.env` style.
- `WC_TOKEN` verification helper.
- PostgreSQL connection helper.
- Public read-only repositories and services.
- Pydantic schemas for migrated public contracts.
- Legacy compatibility routes:
  - `/php/load_data.php?type=maps`
  - `/php/load_data.php?type=vehicles`
  - `/php/load_data.php?type=players`
  - `/php/load_data.php?type=tuning_parts`
  - `/php/load_data.php?type=tuning_setups`
  - `/php/load_data.php?type=records`
  - `/auth/status.php`
  - `/auth/logout.php`
  - `/php/get_news.php`
  - `/php/get_hcaptcha_sitekey.php`
- Clean API routes:
  - `/api/v1/maps`
  - `/api/v1/vehicles`
  - `/api/v1/players`
  - `/api/v1/tuning-parts`
  - `/api/v1/tuning-setups`
  - `/api/v1/records`
  - `/api/v1/auth/status`
  - `/api/v1/auth/logout`
  - `/api/v1/news`
  - `/api/v1/hcaptcha/sitekey`
- Pytest and Ruff setup.

Run it locally:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m uvicorn app.main:app --reload
```

Health checks:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/v1/health`

## Environment

Root legacy variables:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASS
AUTH_SHARED_SECRET
ALLOWED_DISCORD_IDS
API_KEYS
HCAPTCHA_SITE_KEY
HCAPTCHA_SECRET_KEY
```

The backend scaffold also supports:

```text
APP_NAME
APP_VERSION
ENVIRONMENT
DATABASE_URL
CORS_ORIGINS
```

Use `.env.example` and `backend/.env.example` as references.

## Frontend Scaffold

The new frontend lives in `frontend/`.

Implemented so far:

- Vite + React + TypeScript.
- React Router routes for the public shell and public data views.
- TanStack Query client.
- Centralized API fetch helper.
- Auth status polling.
- Dark mode persistence using the legacy `data-theme` contract.
- Copied legacy `css/style.css` and `img/` assets under `frontend/public/`.
- Initial pages for home, maps, vehicles, players, tuning parts, tuning setups, records, stats, privacy and maintenance.

Run it locally:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

By default Vite proxies `/api`, `/auth`, `/php` and `/health` to `http://127.0.0.1:8000`. Use `frontend/.env.example` as the reference for frontend variables.

## Legacy Application

The legacy application is still the functional product.

Important legacy entry points:

- `index.php`
- `index.html`
- `php/load_data.php`
- `php/admin.php`
- `auth/status.php`
- `auth/check_auth.php`

Important legacy assets:

- `css/style.css`
- `js/script.js`
- `img/`

During the migration, this code should stay in place until the FastAPI and React replacements are complete and verified.

## What Will Be Removed Later

Nothing in this list should be deleted yet.

After the new backend and frontend fully replace the legacy behavior, the following legacy pieces should be reviewed for removal or archival:

- PHP endpoints in `php/` and `auth/` that have confirmed FastAPI replacements.
- `php/admin.php` after the React admin area is complete.
- `js/script.js` after the public React UI is complete.
- Legacy standalone HTML pages once React routes cover them.
- Duplicate or unused CSS after visual parity is verified.
- Copied frontend assets/CSS can be deduplicated after the final asset serving strategy is chosen.
- Local SQLite snapshots in `backups/` are now ignored by Git. A coordinated history rewrite is still required if the historical database files must be fully purged from repository history.

Deletion must happen only after route usage, tests and visual checks confirm that the replacement is complete.

## Next Migration Step

The next safe technical step is to validate the new read-only FastAPI endpoints against a safe PostgreSQL database, then continue porting the legacy public UI behaviors into React.

The legacy PHP app remains the user-facing product until the React frontend reaches visual and behavioral parity.
