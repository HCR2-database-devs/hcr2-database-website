# Routes and Flows

Date: 2026-04-20

This document maps the current routes and user/admin flows before migration.

## HTML Pages

| Route | File | Purpose | Protection |
| --- | --- | --- | --- |
| `/` or `/index.php` | `index.php` | Main public entry point | Maintenance check |
| `/index.html` | `index.html` | Static public page | Client-side maintenance check |
| `/maintenance.html` | `maintenance.html` | Static maintenance page | Public |
| `/privacy.html` | `privacy.html` | Privacy policy | Public |
| `/php/admin.php` | `php/admin.php` | Admin panel | `WC_TOKEN` + Discord allowlist |

## Public Endpoints

| Method | Route | File | Output | Notes |
| --- | --- | --- | --- | --- |
| GET | `/php/maintenance_status.php` | `php/maintenance_status.php` | `{ maintenance, allowed }` | Uses admin session if available |
| GET | `/php/load_data.php?type=maps` | `php/load_data.php` | map list | Maintenance-aware |
| GET | `/php/load_data.php?type=vehicles` | `php/load_data.php` | vehicle list | Maintenance-aware |
| GET | `/php/load_data.php?type=players` | `php/load_data.php` | player list | Maintenance-aware |
| GET | `/php/load_data.php?type=tuning_parts` | `php/load_data.php` | tuning part list | Ordered by `nameTuningPart` |
| GET | `/php/load_data.php?type=tuning_setups` | `php/load_data.php` | setup list with parts | Aggregated from setup tables |
| GET | `/php/load_data.php?type=records` | `php/load_data.php` | current records | `wr.current = 1` |
| GET | `/php/get_news.php?limit=10` | `php/get_news.php` | `{ news: [...] }` | Limit clamped by existing behavior |
| GET | `/php/get_hcaptcha_sitekey.php` | `php/get_hcaptcha_sitekey.php` | `{ sitekey }` | Fails if hCaptcha is not configured |
| POST | `/php/public_submit.php` | `php/public_submit.php` | `{ success, message }` or `{ error }` | hCaptcha, honeypot and rate limit |
| GET | `/php/api_records.php` | `php/api_records.php` | `{ records, count }` | API key required |

## Auth Endpoints

| Method | Route | File | Purpose |
| --- | --- | --- | --- |
| GET | `/auth/status.php` | `auth/status.php` | Returns login and admin status |
| GET | `/auth/logout.php` | `auth/logout.php` | Clears session and `WC_TOKEN`, then redirects to `/` |

Login is currently external: the public button redirects to `https://auth.hcr2.xyz/login`, which is expected to set `WC_TOKEN`.

## Admin Endpoints

| Method | Route | File | Purpose |
| --- | --- | --- | --- |
| POST | `/php/submit_record.php` | `php/submit_record.php` | Create or replace a record |
| POST | `/php/delete_record.php` | `php/delete_record.php` | Delete a record |
| POST | `/php/set_questionable.php` | `php/set_questionable.php` | Update verification/questionable status |
| POST | `/php/assign_setup.php` | `php/assign_setup.php` | Assign a tuning setup |
| POST | `/php/add_vehicle.php` | `php/add_vehicle.php` | Add a vehicle and optional SVG icon |
| POST | `/php/add_map.php` | `php/add_map.php` | Add a map and optional SVG icon |
| POST | `/php/add_tuning_part.php` | `php/add_tuning_part.php` | Add a tuning part and optional SVG icon |
| POST | `/php/add_tuning_setup.php` | `php/add_tuning_setup.php` | Add a tuning setup |
| GET | `/auth/admin_pending.php` | `auth/admin_pending.php` | List pending submissions |
| POST | `/auth/admin_pending.php` | `auth/admin_pending.php` | Approve or reject a pending submission |
| POST | `/auth/post_news.php` | `auth/post_news.php` | Post news |
| GET | `/auth/admin_actions.php?action=download_db` | `auth/admin_actions.php` | Returns 501 for PostgreSQL |
| POST | `/auth/admin_actions.php` | `auth/admin_actions.php` | List/delete backups and run integrity checks |
| POST | `/php/set_maintenance.php` | `php/set_maintenance.php` | Toggle maintenance |

## Public Browsing Flow

1. The user opens `/`.
2. `index.php` blocks non-admin users if maintenance mode is enabled.
3. `index.html` also checks `/php/maintenance_status.php`.
4. Public buttons call `fetchData(type)` or `fetchStats()`.
5. Data is fetched from `/php/load_data.php?type=...`.
6. `js/script.js` renders tables, filters, stats and modals.

Supported data views:

- maps
- vehicles
- players
- tuning parts
- records
- stats, derived from records

## Records Flow

1. The user clicks `Get Records`.
2. The frontend calls `/php/load_data.php?type=records`.
3. Default sort:
   - map name alphabetically
   - vehicle id when available
   - vehicle name as fallback
4. Rendered columns:
   - Distance
   - Status
   - Notes
   - Map Name
   - Vehicle Name
   - Tuning Parts
   - Player Name
   - Player Country
   - Share
5. Filters:
   - text search across player, map, vehicle and notes
   - map
   - vehicle
   - tuning parts, all selected parts must be present
   - distance greater-than-or-equal or less-than-or-equal
   - only questionable
   - only verified
6. CSV export includes:
   - Distance
   - Map Name
   - Vehicle Name
   - Player Name
   - Country

## Public Submission Flow

1. The user opens the submit record modal.
2. The frontend loads maps, vehicles and tuning parts.
3. The frontend loads the hCaptcha site key.
4. Client-side validation requires:
   - map
   - vehicle
   - positive distance
   - player name
   - 3 or 4 tuning parts
   - hCaptcha response
5. The frontend posts JSON to `/php/public_submit.php`.
6. The backend validates:
   - hCaptcha token
   - required fields
   - honeypot fields
   - minimum fill time
   - positive distance
   - 3 or 4 tuning parts
   - per-IP submission rate limit
7. The backend inserts a `PendingSubmission`.
8. The user sees the current success message.

## News Flow

1. The user opens the news modal.
2. The frontend calls `/php/get_news.php`.
3. News are rendered with title, content, author and creation date.
4. `localStorage.unreadNews` is set to `false`.

## Auth Visibility Flow

1. The frontend calls `/auth/status.php`.
2. If `logged=false`, login is visible and logout/admin are hidden.
3. If `logged=true`, login is hidden and logout is visible.
4. If `allowed=true`, the admin button is visible.
5. The status is refreshed every 30 seconds.

## Admin Access Flow

1. The user opens `/php/admin.php`.
2. `ensure_authorized()` validates `WC_TOKEN`.
3. The JWT payload is copied into `$_SESSION['discord']`.
4. `sub` must exist in `ALLOWED_DISCORD_IDS`.
5. Unauthorized users are redirected or receive a 403 page.

## Admin Record Replacement Flow

1. The admin fills the record form.
2. The form loads maps, vehicles, players, tuning setups and tuning parts.
3. The frontend requires either an existing player or a new player name.
4. The backend requires map, vehicle and positive distance.
5. If `playerId` is provided, it must exist.
6. In a transaction, the backend deletes existing records for the same map and vehicle.
7. The backend inserts a new current world record.
8. The response includes the resolved map, vehicle, player and distance labels.

Important existing behavior: `newPlayerName` is accepted in the payload, but `submit_record.php` does not create the new player. Do not change this silently.

## Admin Pending Submission Flow

GET:

- List submissions with `status = 'pending'`.
- Join map and vehicle labels.
- Sort by `submitted_at DESC`.

Approve:

1. Load the pending submission.
2. Delete the existing record for the same map and vehicle.
3. Find or create the submitted player.
4. Insert a current world record.
5. If tuning parts are valid, create a tuning setup and assign it.
6. Mark the submission as `approved`.

Reject:

- Mark the submission as `rejected`.

## Maintenance Flow

1. An admin posts to `/php/set_maintenance.php`.
2. The root `MAINTENANCE` flag file is created or removed.
3. Maintenance-aware JSON endpoints return HTTP 503 for non-admin users.
4. `index.php` returns an HTTP 503 maintenance page for non-admin users.

## Deep Links

Supported query parameters:

- `view`: `maps`, `vehicles`, `players`, `tuning_parts`, `records`, `tuning_setups`
- `recordId`: scroll and highlight a record row
- `map`: scroll toward a matching map label

`mapId` can be generated by the share-link helper but is not explicitly consumed by the current deep-link handler.

## Contracts to Preserve

- Legacy route names while the legacy frontend exists.
- JSON field names and response shapes.
- Useful error messages consumed by the frontend.
- Existing id and label fields such as `idMap`, `nameMap`, `idVehicle`, `nameVehicle`, `idPlayer`, `namePlayer`.
- Current record fields such as `idRecord`, `distance`, `current`, `idTuningSetup`, `questionable`, `questionable_reason`, `map_name`, `vehicle_name`, `player_name`, `player_country`, `tuning_parts`.
- Existing auth, maintenance, hCaptcha and admin rules.
