# 02 - Target Architecture

Date: 2026-04-20

This document defines the target architecture and the compatibility rules for moving from the legacy PHP/HTML/CSS/JavaScript application to FastAPI and React/Vite/TypeScript.

## Target Repository Layout

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- api/
|   |   |-- core/
|   |   |-- db/
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- services/
|   |   |-- repositories/
|   |   `-- utils/
|   `-- tests/
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   |-- pages/
|   |   |-- components/
|   |   |-- features/
|   |   |-- services/
|   |   |-- hooks/
|   |   |-- lib/
|   |   |-- types/
|   |   |-- assets/
|   |   `-- styles/
|   `-- tests/
|-- docs/migration/
|-- scripts/
|-- infra/
`-- legacy/
```

The `legacy/` folder should be introduced only when route and asset compatibility are controlled. Until then, the legacy files should remain in place.

## Backend Architecture

Target stack:

- FastAPI.
- Pydantic and Pydantic Settings.
- PostgreSQL.
- Repository/service separation.
- Contract tests for legacy-compatible JSON.

Target modules:

- `app/main.py`: app factory, middleware and router registration.
- `app/api/v1/`: versioned routers.
- `app/core/config.py`: environment and settings.
- `app/core/security.py`: JWT, API key and admin access helpers.
- `app/core/errors.py`: shared error responses.
- `app/db/`: database connection lifecycle.
- `app/schemas/`: Pydantic request/response schemas.
- `app/repositories/`: SQL/data access.
- `app/services/`: business rules.
- `app/utils/`: small shared helpers.

## Backend Compatibility Mapping

| Legacy PHP | FastAPI target |
| --- | --- |
| `auth/config.php` | `core/config.py`, `db/session.py`, `core/errors.py` |
| `auth/check_auth.php` | `core/security.py`, auth dependencies |
| `auth/status.php` | `api/v1/auth.py` |
| `auth/logout.php` | `api/v1/auth.py` |
| `php/load_data.php` | `api/v1/public.py`, repositories |
| `php/api_records.php` | `api/v1/records.py` |
| `php/get_news.php` | `api/v1/news.py` |
| `auth/post_news.php` | `api/v1/news.py` |
| `php/get_hcaptcha_sitekey.php` | `api/v1/submissions.py` |
| `php/public_submit.php` | `api/v1/submissions.py` |
| `php/submit_record.php` | `api/v1/admin_records.py` |
| `php/delete_record.php` | `api/v1/admin_records.py` |
| `php/set_questionable.php` | `api/v1/admin_records.py` |
| `php/assign_setup.php` | `api/v1/admin_records.py` |
| `php/add_map.php` | `api/v1/admin_catalog.py` |
| `php/add_vehicle.php` | `api/v1/admin_catalog.py` |
| `php/add_tuning_part.php` | `api/v1/admin_catalog.py` |
| `php/add_tuning_setup.php` | `api/v1/admin_catalog.py` |
| `auth/admin_pending.php` | `api/v1/admin_submissions.py` |
| `auth/admin_actions.php` | `api/v1/admin_ops.py` |
| `php/maintenance_status.php` | `api/v1/maintenance.py` |
| `php/set_maintenance.php` | `api/v1/maintenance.py` |

During migration, clean `/api/v1/...` routes can coexist with legacy-compatible aliases or proxy routes.

## Frontend Architecture

Target stack:

- React.
- Vite.
- TypeScript.
- React Router.
- TanStack Query.
- Legacy CSS imported first for visual parity.

Target structure:

```text
frontend/src/
|-- app/             # App, router, query client
|-- pages/           # Public, admin, privacy, maintenance pages
|-- components/      # Shared UI and layout components
|-- features/        # Domain features
|-- services/        # API clients and query keys
|-- hooks/
|-- lib/
|-- types/
|-- assets/
`-- styles/
```

## Frontend Feature Mapping

| Legacy area | React target |
| --- | --- |
| `index.html` public shell | `pages/PublicHomePage.tsx`, layout components |
| Header/nav/login/logout/admin buttons | `components/layout`, `features/auth` |
| Dark mode | `features/theme` |
| `fetchData` data views | `features/public-data` |
| Records table and filters | `features/records` |
| Stats rendering | `features/stats` |
| Public submit modal | `features/submissions` |
| News modal | `features/news` |
| Note modal | `features/records` |
| `privacy.html` | `pages/PrivacyPage.tsx` |
| `maintenance.html` | `pages/MaintenancePage.tsx` |
| `php/admin.php` | `pages/AdminPage.tsx`, `features/admin` |

## TypeScript Domain Types

Initial public data contracts:

```ts
export interface MapItem {
  idMap: number;
  nameMap: string;
}

export interface VehicleItem {
  idVehicle: number;
  nameVehicle: string;
}

export interface PlayerItem {
  idPlayer: number;
  namePlayer: string;
  country?: string | null;
}

export interface TuningPart {
  idTuningPart: number;
  nameTuningPart: string;
}

export interface TuningSetup {
  idTuningSetup: number;
  parts: Array<{ nameTuningPart: string }>;
}

export interface RecordItem {
  idRecord: number;
  distance: number;
  current: number;
  idTuningSetup?: number | null;
  questionable: number;
  questionable_reason?: string;
  map_name: string;
  vehicle_name: string;
  player_name: string;
  player_country?: string | null;
  tuning_parts?: string | null;
}
```

## Compatibility Rules

- Do not remove PHP routes until FastAPI replacements are tested.
- Do not change public JSON field names without an adapter.
- Do not change visual output during React migration.
- Serve assets at the same `/img/...` paths at first.
- Preserve `WC_TOKEN` authentication semantics.
- Preserve hCaptcha, honeypot and rate-limit behavior.
- Preserve maintenance-mode semantics.
- Preserve admin behavior before replacing `php/admin.php`.
- Treat PostgreSQL schema verification as mandatory before changing SQL assumptions.

## Backend Read-Only Endpoint Target

The first concrete backend migration should implement:

- `GET /api/v1/maps`
- `GET /api/v1/vehicles`
- `GET /api/v1/players`
- `GET /api/v1/tuning-parts`
- `GET /api/v1/tuning-setups`
- `GET /api/v1/records`
- compatibility endpoint for `GET /php/load_data.php?type=...`

These routes should be read-only and contract-tested before mutation endpoints are ported.
