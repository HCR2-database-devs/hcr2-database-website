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

- Existing architecture audit and migration documentation.
- Isolated FastAPI backend scaffold in `backend/`.
- Centralized backend configuration.
- Basic security helpers for the existing `WC_TOKEN` model.
- Database configuration placeholder for the existing PostgreSQL setup.
- Health endpoints and backend tests.

No legacy PHP endpoint has been replaced yet.
No public visual output has been intentionally changed.

## Repository Layout

```text
.
|-- backend/                 # New FastAPI backend scaffold
|   |-- app/
|   |   |-- api/             # Versioned API routers
|   |   |-- core/            # Settings, errors and security helpers
|   |   |-- db/              # Database configuration/session helpers
|   |   |-- models/          # Future database models
|   |   |-- repositories/    # Future data access layer
|   |   |-- schemas/         # Future Pydantic schemas
|   |   |-- services/        # Future business services
|   |   `-- utils/
|   |-- tests/
|   |-- pyproject.toml
|   `-- README.md
|-- docs/
|   `-- migration/           # Migration audit, mappings and plan
|-- auth/                    # Legacy auth/admin PHP endpoints
|-- php/                     # Legacy PHP endpoints and admin page
|-- css/                     # Legacy styles
|-- js/                      # Legacy public JavaScript
|-- img/                     # Public assets and icons
|-- backups/                 # Historical SQLite snapshots
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

These files define the baseline behavior that must be preserved while the project is rebuilt.

## Backend Scaffold

The new backend lives in `backend/`.

Implemented so far:

- FastAPI app factory.
- `/health`
- `/api/v1/health`
- Pydantic settings.
- Environment parsing compatible with the legacy `.env` style.
- `WC_TOKEN` verification helper.
- Basic database configuration object.
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
- Historical SQLite snapshots in `backups/` if they are no longer needed as archives.

Deletion must happen only after route usage, tests and visual checks confirm that the replacement is complete.

## Next Migration Step

The next safe technical step is to port the public read-only data endpoints to FastAPI:

- maps
- vehicles
- players
- tuning parts
- tuning setups
- records

Those endpoints should first match the legacy JSON contracts before the frontend is changed.
