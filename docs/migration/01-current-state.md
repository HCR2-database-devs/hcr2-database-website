# 01 - Current State

Date: 2026-04-20
Branch: `refactor/fastapi-react-migration`

This document is the compact baseline for the migration. It describes the legacy system, the routes and flows that must be preserved, the sensitive behavior, and the real current state of the migration branch.

## Executive Summary

The product is still primarily the legacy PHP/HTML/CSS/vanilla JavaScript application. The migration branch currently contains:

- the full legacy app,
- migration documentation,
- an isolated FastAPI backend scaffold,
- backend health endpoints,
- backend configuration and security helpers,
- backend tests for health, configuration and JWT helpers.

The branch does not yet contain:

- a React/Vite/TypeScript frontend,
- FastAPI business endpoints,
- FastAPI repositories/services for legacy data,
- migrated admin features,
- front/back integration.

The current migration confidence is high for the scaffold and low for product-level replacement.

## Legacy Architecture

```text
.
|-- index.php                 # Public entry point, maintenance-aware
|-- index.html                # Legacy public page
|-- maintenance.html
|-- privacy.html
|-- auth/                     # Legacy auth/admin PHP endpoints
|-- php/                      # Legacy public/admin PHP endpoints and admin page
|-- js/script.js              # Legacy public UI behavior
|-- css/style.css             # Primary legacy styling and dark mode
|-- css/style_dark_mode.css   # Legacy extra stylesheet, not linked by index.html
|-- img/                      # Public assets and game icons
|-- backups/                  # Historical SQLite snapshots
|-- backend/                  # New FastAPI scaffold
`-- docs/migration/           # Migration runbooks
```

Important legacy files:

- `index.php`: checks maintenance mode and serves `index.html`.
- `index.html`: public shell, modals and navigation.
- `js/script.js`: public rendering, filters, stats, auth UI, hCaptcha, news and mobile menu behavior.
- `css/style.css`: visual source of truth for the public UI.
- `php/admin.php`: protected admin panel with embedded HTML/CSS/JS.
- `auth/config.php`: environment loading, PostgreSQL PDO connection and security headers.
- `auth/check_auth.php`: `WC_TOKEN` JWT validation and admin authorization.

## Critical Public Routes

| Route | Purpose | Current owner |
| --- | --- | --- |
| `/` or `/index.php` | Public entry point | Legacy PHP |
| `/index.html` | Public page shell | Legacy HTML |
| `/privacy.html` | Privacy page | Legacy HTML |
| `/maintenance.html` | Maintenance page | Legacy HTML |
| `/php/load_data.php?type=maps` | Maps data | Legacy PHP |
| `/php/load_data.php?type=vehicles` | Vehicles data | Legacy PHP |
| `/php/load_data.php?type=players` | Players data | Legacy PHP |
| `/php/load_data.php?type=tuning_parts` | Tuning parts data | Legacy PHP |
| `/php/load_data.php?type=tuning_setups` | Tuning setup data | Legacy PHP |
| `/php/load_data.php?type=records` | Current records | Legacy PHP |
| `/php/get_news.php` | Public news | Legacy PHP |
| `/php/get_hcaptcha_sitekey.php` | hCaptcha site key | Legacy PHP |
| `/php/public_submit.php` | Public record submission | Legacy PHP |
| `/php/api_records.php` | API-key records endpoint | Legacy PHP |

## Critical Admin Routes

| Route | Purpose | Current owner |
| --- | --- | --- |
| `/php/admin.php` | Admin UI | Legacy PHP |
| `/auth/status.php` | Login/admin status | Legacy PHP |
| `/auth/logout.php` | Logout | Legacy PHP |
| `/php/submit_record.php` | Create/replace record | Legacy PHP |
| `/php/delete_record.php` | Delete record | Legacy PHP |
| `/php/set_questionable.php` | Update verification status | Legacy PHP |
| `/php/assign_setup.php` | Assign tuning setup | Legacy PHP |
| `/php/add_vehicle.php` | Add vehicle and optional icon | Legacy PHP |
| `/php/add_map.php` | Add map and optional icon | Legacy PHP |
| `/php/add_tuning_part.php` | Add tuning part and optional icon | Legacy PHP |
| `/php/add_tuning_setup.php` | Add tuning setup | Legacy PHP |
| `/auth/admin_pending.php` | Review public submissions | Legacy PHP |
| `/auth/post_news.php` | Post news | Legacy PHP |
| `/auth/admin_actions.php` | Backups and integrity actions | Legacy PHP |
| `/php/maintenance_status.php` | Maintenance status | Legacy PHP |
| `/php/set_maintenance.php` | Toggle maintenance | Legacy PHP |

## Public Flows to Preserve

- Open public page through `/` or `/index.php`.
- Check maintenance before serving or using JSON routes.
- Display maps, vehicles, players, tuning parts and records from `load_data`.
- Filter records by search text, map, vehicle, tuning parts, distance, questionable and verified status.
- Sort records by default order, distance and newest.
- Export filtered records to CSV.
- Share deep links using `view`, `recordId` and `map`.
- Render map, vehicle and tuning icons from `/img/...`.
- Render country flags through `flagcdn.com`.
- Show stats derived from current records.
- Toggle dark mode through `localStorage.darkMode` and `[data-theme="dark"]`.
- Open public submission modal with hCaptcha and honeypots.
- Open news and note modals.
- Poll auth status and show login/logout/admin controls.

## Admin Flows to Preserve

- Protect admin with `WC_TOKEN` and `ALLOWED_DISCORD_IDS`.
- Create or replace current records.
- Delete records.
- Mark records verified/questionable with optional notes.
- Assign tuning setups to records.
- Add maps, vehicles and tuning parts, including optional SVG upload validation.
- Add tuning setups and reject duplicates.
- Review pending public submissions.
- Approve submissions by replacing the map/vehicle record and optionally creating a tuning setup.
- Reject submissions.
- Post news.
- List/delete backup files and run integrity check.
- Toggle maintenance mode.

## Data Model Snapshot

The active code expects PostgreSQL tables with names such as:

- `_map`
- `_vehicle`
- `_player`
- `_tuningpart`
- `_tuningsetup`
- `_tuningsetupparts`
- `_worldrecord`
- `PendingSubmission`
- `News`

Historical SQLite snapshots contain similar tables without the underscore prefix. They are useful references but not authoritative for production.

Important fields expected by the legacy runtime include:

- maps: `idMap`, `nameMap`
- vehicles: `idVehicle`, `nameVehicle`
- players: `idPlayer`, `namePlayer`, `country`
- tuning parts: `idTuningPart`, `nameTuningPart`
- records: `idRecord`, `distance`, `current`, `idTuningSetup`, `questionable`, `questionable_reason`, `map_name`, `vehicle_name`, `player_name`, `player_country`, `tuning_parts`

## Assets

Key assets are still served from `img/`:

- site logo and favicons,
- Discord logo,
- maintenance image,
- map SVG icons,
- vehicle SVG icons,
- tuning part SVG icons.

The icon naming convention is lowercase, spaces replaced with `_`, and only `[a-z0-9_-]` retained.

Against the latest SQLite snapshot, all expected map, vehicle and tuning part SVG icons were present.

## Sensitive Legacy Points

- `php/delete_record.php` appears to require `php/auth/check_auth.php`, while the actual auth folder is at project root.
- `php/add_tuning_setup.php` requires 3 or 4 parts server-side, while admin JavaScript currently allows 2 to 4 before the request.
- `submit_record.php` accepts a new player payload but does not create that player.
- `auth/admin_actions.php` still exposes backup/import/restore controls, but several PostgreSQL actions intentionally return unsupported errors.
- SQLite backup files include historical data and must be handled carefully from a Git/privacy perspective.
- Some terminal output shows encoding artifacts; do not rewrite copy without browser verification.

## Current Migration Reality

Migrated or prepared:

- FastAPI scaffold.
- Health routes.
- Environment parsing.
- JWT helper.
- Admin allowlist helper.
- Basic database configuration object.
- Backend tests.

Not migrated:

- public data endpoints,
- auth routes,
- news routes,
- hCaptcha route,
- public submission route,
- admin endpoints,
- React frontend,
- frontend assets/CSS integration,
- end-to-end startup workflow.
