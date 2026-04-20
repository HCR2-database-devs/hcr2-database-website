# Backend Mapping

Date: 2026-04-20

This document maps the legacy PHP backend to the target FastAPI architecture.

## Current Backend

- Procedural PHP.
- Configuration and database connection in `auth/config.php`.
- JWT verification in `auth/check_auth.php`.
- SQL embedded directly in endpoint files.
- Business rules mixed with request handling.
- No automated backend test suite in the legacy app.

## Target Backend Structure

```text
backend/
|-- app/
|   |-- main.py
|   |-- api/
|   |   `-- v1/
|   |-- core/
|   |-- db/
|   |-- models/
|   |-- schemas/
|   |-- services/
|   |-- repositories/
|   `-- utils/
`-- tests/
```

The initial target is compatibility, not redesign. FastAPI must reproduce the useful legacy contracts before any route is replaced.

## Configuration

Legacy source: `auth/config.php`

Responsibilities:

- Load `.env`.
- Read database, auth, API key and hCaptcha settings.
- Configure session cookie settings.
- Send security headers.
- Create a PostgreSQL PDO connection.
- Return safe JSON errors.

FastAPI target:

- `app/core/config.py`: Pydantic settings.
- `app/db/session.py`: database connection setup.
- `app/core/errors.py`: common error helpers.
- `app/main.py`: app factory, middleware and router registration.

## Authentication

Legacy files:

- `auth/check_auth.php`
- `auth/status.php`
- `auth/logout.php`

Required behavior:

- Read `WC_TOKEN` from cookies.
- Verify HMAC SHA-256 JWT signature with `AUTH_SHARED_SECRET`.
- Reject invalid or expired tokens.
- Require `sub` and `exp`.
- Copy `sub` and `username` into the request/session user representation.
- Check `sub` against `ALLOWED_DISCORD_IDS` for admin access.

FastAPI target:

- `app/core/security.py`
- auth dependencies such as `get_current_user()` and `require_admin()`
- compatibility routes:
  - `/auth/status.php`
  - `/auth/logout.php`
- clean API routes:
  - `/api/v1/auth/status`
  - `/api/v1/auth/logout`

## Maintenance

Legacy files:

- `php/maintenance_helpers.php`
- `php/maintenance_status.php`
- `php/set_maintenance.php`

Required behavior:

- Keep the root `MAINTENANCE` flag file at first.
- Return `{ maintenance, allowed }`.
- Return HTTP 503 for non-admin users while maintenance is enabled.

FastAPI target:

- `app/services/maintenance_service.py`
- `app/api/v1/maintenance.py`

## Public Read-Only Data

Legacy source: `php/load_data.php`

Types:

- `maps`
- `vehicles`
- `players`
- `tuning_parts`
- `tuning_setups`
- `records`

FastAPI target:

- `app/api/v1/public.py`
- repositories:
  - maps
  - vehicles
  - players
  - tuning
  - records
- schemas for the legacy JSON shapes

Compatibility route:

- `/php/load_data.php?type=...`

Clean routes:

- `/api/v1/maps`
- `/api/v1/vehicles`
- `/api/v1/players`
- `/api/v1/tuning-parts`
- `/api/v1/tuning-setups`
- `/api/v1/records`

## API-Key Records Endpoint

Legacy source: `php/api_records.php`

Required behavior:

- Accept API key from `api_key` query parameter or `X-API-Key` header.
- Check key against `API_KEYS`.
- Support filters:
  - `map`
  - `vehicle`
  - `player`
  - `country`
  - `questionable`
  - `min_distance`
  - `max_distance`
  - `q`
  - `limit`
  - `offset`
- Clamp `limit` to 1..500.
- Return `{ records, count }`.

FastAPI target:

- `app/api/v1/records.py`
- API key dependency.
- contract tests before replacement.

## Public Submissions

Legacy source: `php/public_submit.php`

Input:

- `mapId`
- `vehicleId`
- `distance`
- `playerName`
- `playerCountry`
- `tuningParts`
- `h_captcha_response`
- honeypot fields
- `form_load_time`
- `submission_time`

Required validations:

- hCaptcha token is valid.
- Required fields are present.
- Honeypot fields are empty.
- Fill time is not too fast.
- Distance is positive.
- 3 or 4 tuning parts are provided.
- Per-IP rate limit: no more than 5 submissions per hour.

FastAPI target:

- `app/schemas/submissions.py`
- `app/services/hcaptcha_service.py`
- `app/services/public_submission_service.py`
- `app/repositories/pending_submissions.py`

## Admin Record Management

Legacy files:

- `php/submit_record.php`
- `php/delete_record.php`
- `php/set_questionable.php`
- `php/assign_setup.php`

Required behavior:

- Admin access is required.
- Record replacement deletes the existing map/vehicle record before inserting the new one.
- Distance must be positive.
- Existing player ids must be validated.
- `questionable` must be 0 or 1.
- Assigning a tuning setup is blocked if the record already has one.

FastAPI target:

- `app/api/v1/admin_records.py`
- `app/services/record_service.py`
- `app/repositories/records.py`

## Admin Catalog Management

Legacy files:

- `php/add_map.php`
- `php/add_vehicle.php`
- `php/add_tuning_part.php`
- `php/add_tuning_setup.php`

Required behavior:

- Reject duplicate map, vehicle and tuning part names.
- Keep the current id generation strategy until the production schema is verified.
- Validate optional SVG uploads:
  - SVG MIME or extension.
  - Max 1 MB.
  - Content contains `<svg`.
  - Save using the current normalized file name convention.
- Reject duplicate tuning setups.
- Require 3 or 4 parts server-side for tuning setups.

FastAPI target:

- `app/api/v1/admin_catalog.py`
- `app/services/catalog_service.py`
- `app/services/icon_upload_service.py`
- `app/repositories/catalog.py`

## Pending Submissions

Legacy source: `auth/admin_pending.php`

Required behavior:

- GET lists pending submissions with map and vehicle labels.
- POST approve:
  - replace the current map/vehicle record.
  - find or create the submitted player.
  - create and assign a tuning setup when all submitted parts resolve.
  - mark the submission approved.
- POST reject:
  - mark the submission rejected.

FastAPI target:

- `app/api/v1/admin_submissions.py`
- `app/services/pending_submission_service.py`
- `app/repositories/pending_submissions.py`

## News

Legacy files:

- `php/get_news.php`
- `auth/post_news.php`

Required behavior:

- Public news are sorted by `created_at DESC`.
- Limit defaults to 10.
- Invalid or too-large limits fall back to 10.
- Admin posting strips tags from title and content.
- Author comes from the authenticated Discord username.

FastAPI target:

- `app/api/v1/news.py`
- `app/services/news_service.py`
- `app/repositories/news.py`

## Admin Operations

Legacy source: `auth/admin_actions.php`

Currently supported:

- list backup files
- delete backup files
- run `SELECT 1` integrity check

Currently unsupported for PostgreSQL:

- database download
- backup creation
- restore
- SQL import

FastAPI should initially reproduce the current behavior, including unsupported-operation responses.

## File-to-Module Mapping

| Legacy PHP file | FastAPI target |
| --- | --- |
| `auth/config.php` | `core/config.py`, `db/session.py`, `core/errors.py` |
| `auth/check_auth.php` | `core/security.py`, auth dependencies |
| `auth/status.php` | `api/v1/auth.py` |
| `auth/logout.php` | `api/v1/auth.py` |
| `php/maintenance_helpers.php` | `services/maintenance_service.py` |
| `php/maintenance_status.php` | `api/v1/maintenance.py` |
| `php/set_maintenance.php` | `api/v1/maintenance.py` |
| `php/load_data.php` | `api/v1/public.py`, repositories |
| `php/api_records.php` | `api/v1/records.py` |
| `php/public_submit.php` | `api/v1/submissions.py` |
| `php/get_hcaptcha_sitekey.php` | `api/v1/submissions.py` |
| `php/get_news.php` | `api/v1/news.py` |
| `auth/post_news.php` | `api/v1/news.py` |
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

## Backend Migration Priority

1. Configuration, app factory and health checks.
2. Database connectivity.
3. Read-only public data endpoints.
4. Auth status compatibility.
5. News endpoints.
6. Public submissions.
7. Admin record management.
8. Admin catalog management.
9. Pending submission approval/rejection.
10. Maintenance mode.
11. API-key records endpoint.
12. Admin operations compatibility.
