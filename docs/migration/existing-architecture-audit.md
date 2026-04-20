# Existing Architecture Audit

Date: 2026-04-20
Working branch: `refactor/fastapi-react-migration`

This document captures the current state of the project before the FastAPI and React migration. It is intentionally descriptive: the goal is to preserve the existing behavior first, then migrate it safely.

## Executive Summary

The current application is a legacy PHP, HTML, CSS and vanilla JavaScript website.

- Public UI: `index.html`, `css/style.css`, `js/script.js`.
- Public entry point: `index.php`, which checks maintenance mode and then serves `index.html`.
- Backend: procedural PHP endpoints split between `php/` and `auth/`.
- Admin UI: `php/admin.php`, a protected standalone PHP page with embedded HTML, CSS and JavaScript.
- Authentication: signed `WC_TOKEN` JWT cookie, validated with `AUTH_SHARED_SECRET`.
- Admin authorization: Discord user id allowlist from `ALLOWED_DISCORD_IDS`.
- Active database expected by the code: PostgreSQL through PDO.
- Historical database snapshots: SQLite files in `backups/`.
- Assets: logos, favicons, maintenance image and SVG icons under `img/`.

The migration must not reinterpret the product. It must keep the current features, data contracts, access rules, validations and visual output while progressively introducing a clean architecture.

## Current Top-Level Structure

```text
.
|-- index.php
|-- index.html
|-- maintenance.html
|-- privacy.html
|-- README.md
|-- test_curl.php
|-- auth/
|   |-- admin_actions.php
|   |-- admin_pending.php
|   |-- check_auth.php
|   |-- config.php
|   |-- logout.php
|   |-- post_news.php
|   `-- status.php
|-- php/
|   |-- add_map.php
|   |-- add_tuning_part.php
|   |-- add_tuning_setup.php
|   |-- add_vehicle.php
|   |-- admin.php
|   |-- api_records.php
|   |-- assign_setup.php
|   |-- delete_record.php
|   |-- get_hcaptcha_sitekey.php
|   |-- get_news.php
|   |-- load_data.php
|   |-- maintenance_helpers.php
|   |-- maintenance_status.php
|   |-- public_submit.php
|   |-- set_maintenance.php
|   |-- set_questionable.php
|   |-- submit_record.php
|   `-- test_curl.php
|-- js/
|   `-- script.js
|-- css/
|   |-- style.css
|   `-- style_dark_mode.css
|-- img/
|   |-- map_icons/
|   |-- vehicle_icons/
|   `-- tuning_parts_icons/
`-- backups/
    |-- main-20260326-023356.sqlite
    `-- main-20260403-073123.sqlite
```

## File Inventory

- PHP files: 27
- HTML files: 3
- JavaScript files: 1 main file, `js/script.js`
- CSS files: 2
- SVG assets: 75
- PNG assets: 10
- SQLite snapshots: 2

The largest behavior-heavy files are:

- `js/script.js`: public UI logic, data rendering, filters, stats, modals and auth UI.
- `php/admin.php`: complete admin interface and admin-side JavaScript.
- `css/style.css`: public visual system, responsive behavior and dark mode.

## Main Entry Points

- `/` or `/index.php`: maintenance-aware public entry point.
- `/index.html`: static public page, with a synchronous maintenance status check.
- `/privacy.html`: privacy policy.
- `/maintenance.html`: static maintenance page.
- `/php/admin.php`: protected admin panel.
- `/php/*.php`: public and admin backend endpoints.
- `/auth/*.php`: authentication, admin submissions, news and admin operations.
- `/php/api_records.php`: API-key-protected records endpoint.

## Runtime and Tooling Baseline

Local tools detected during the audit:

- PHP 7.4 CLI is available.
- Node.js 22 is available.
- Python 3.13 is available.

Static validation performed:

```powershell
Get-ChildItem -Recurse -File -Filter *.php | ForEach-Object { php -l $_.FullName }
```

Result: all PHP files passed syntax validation.

## Environment Variables

The legacy `.env.example` contains:

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

Important behavior:

- `AUTH_SHARED_SECRET` is required by `auth/config.php`.
- The database connection uses a PostgreSQL DSN.
- `ALLOWED_DISCORD_IDS` and `API_KEYS` are parsed as comma-separated or newline-separated lists.
- hCaptcha requires both site key and secret key for the public submission flow.

## Authentication and Authorization

Core files:

- `auth/config.php`
- `auth/check_auth.php`
- `auth/status.php`
- `auth/logout.php`

Current rules:

- The app expects a `WC_TOKEN` cookie.
- The token is a JWT signed with HMAC SHA-256.
- Required payload fields: `sub`, `exp`; `username` is used when present.
- Expired or invalid tokens are rejected.
- Admin access requires the Discord `sub` to be listed in `ALLOWED_DISCORD_IDS`.
- Invalid tokens clear the `WC_TOKEN` cookie.
- Session cookies are configured with secure, httponly and SameSite Lax options.

These rules must be preserved in the FastAPI migration.

## Public Frontend

`index.html` defines the public shell:

- Header, logo, title and subtitle.
- Public navigation buttons.
- Discord sign-in button.
- Admin and logout buttons controlled by auth status.
- Dark mode toggle.
- Dynamic data and stats containers.
- About, record guidelines, viewing instructions, submission instructions, statistics, news and social links.
- Public submission modal.
- News modal.
- Record note modal.
- Footer with GitHub metadata and privacy link.

`js/script.js` currently owns:

- JSON fetch cache with a short TTL.
- Dark mode persistence through `localStorage.darkMode`.
- News read indicator through `localStorage.unreadNews`.
- HTML escaping.
- Country flag rendering.
- Icon rendering for maps, vehicles and tuning parts.
- Public data fetches from `php/load_data.php`.
- Records table rendering.
- Records filters, sorting, deep links and CSV export.
- Detailed stats calculations and rendering.
- Auth status polling.
- hCaptcha setup.
- Public submission handling.
- News loading.
- Mobile menu behavior.

## Admin Area

`php/admin.php` is a protected standalone admin page.

It currently supports:

- Creating or replacing a record.
- Deleting a record.
- Marking a record as verified or questionable.
- Assigning a tuning setup to a record.
- Adding vehicles, maps and tuning parts.
- Uploading optional SVG icons for maps, vehicles and tuning parts.
- Creating tuning setups.
- Reviewing pending public submissions.
- Posting news.
- Listing and deleting backup files.
- Running a database integrity check.
- Toggling maintenance mode.

The admin area is sensitive and should be migrated after the public read-only APIs and public UI are stable.

## Maintenance Mode

Core files:

- `php/maintenance_helpers.php`
- `php/maintenance_status.php`
- `php/set_maintenance.php`
- `maintenance.html`

Current behavior:

- Maintenance state is represented by a root-level `MAINTENANCE` flag file.
- Non-admin HTML requests receive an HTTP 503 maintenance page.
- Non-admin JSON requests receive HTTP 503 with:

```json
{ "error": "Site is under maintenance. Please try again later." }
```

The initial FastAPI migration should preserve this flag-file behavior.

## Assets

Critical public assets:

- `img/hcrdatabaselogo.png`
- `img/Discord-Symbol-Blurple.png`
- `img/image copy.png`
- `img/image.png`
- `img/maintenanceon.png`
- favicons and web manifest under `img/`

Dynamic icon paths:

- `/img/map_icons/<normalized-name>.svg`
- `/img/vehicle_icons/<normalized-name>.svg`
- `/img/tuning_parts_icons/<normalized-name>.svg`

The normalization rule used by the frontend is:

- lowercase
- whitespace replaced with `_`
- remove characters outside `[a-z0-9_-]`

## Existing Risk Points

- Business logic is spread across large PHP and JavaScript files.
- The public UI relies heavily on string-built HTML.
- The admin UI duplicates some public behavior in embedded JavaScript.
- The active code expects PostgreSQL table names such as `_map` and `_worldrecord`, while SQLite snapshots use names such as `Map` and `WorldRecord`.
- The current PHP code expects `questionable_reason`, but the inspected SQLite snapshots do not contain that column.
- `php/delete_record.php` appears to require `php/auth/check_auth.php`, which does not match the actual directory layout.
- `php/add_tuning_setup.php` requires 3 or 4 parts server-side, while the admin frontend currently validates 2 to 4 parts.
- `auth/admin_actions.php` still displays backup/import/restore actions, but several of them intentionally return unsupported PostgreSQL errors.
- Some characters appear incorrectly decoded in terminal output. Do not normalize text encoding without browser verification.

## Migration Rule From This Audit

The migration must be contract-first:

1. Keep the legacy behavior documented.
2. Build FastAPI endpoints that match the legacy JSON contracts.
3. Keep PHP endpoints available during transition.
4. Move the public UI to React only after the backend contracts are stable.
5. Reuse current styles and assets before extracting or improving them.
6. Add tests around behavior before deleting legacy code.
