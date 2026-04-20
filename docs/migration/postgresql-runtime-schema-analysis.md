# PostgreSQL Runtime Schema Analysis

Date: 2026-04-20
Branch: `refactor/fastapi-react-migration`

This document describes the PostgreSQL schema that the current legacy PHP code actually expects at runtime. It is based on static analysis of the legacy PHP backend, not on the historical SQLite snapshots.

## Scope

Inspected runtime files:

- `auth/config.php`
- `auth/check_auth.php`
- `auth/status.php`
- `auth/admin_pending.php`
- `auth/admin_actions.php`
- `auth/post_news.php`
- `php/load_data.php`
- `php/api_records.php`
- `php/public_submit.php`
- `php/submit_record.php`
- `php/delete_record.php`
- `php/set_questionable.php`
- `php/assign_setup.php`
- `php/add_map.php`
- `php/add_vehicle.php`
- `php/add_tuning_part.php`
- `php/add_tuning_setup.php`
- `php/get_news.php`
- `php/get_hcaptcha_sitekey.php`
- `php/maintenance_status.php`
- `php/set_maintenance.php`
- `php/admin.php`
- `index.php`

## Connection Contract

The PHP legacy runtime uses `auth/config.php` and requires these environment variables:

- `AUTH_SHARED_SECRET`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASS`

Optional variables used by legacy behavior:

- `ALLOWED_DISCORD_IDS`
- `API_KEYS`
- `HCAPTCHA_SITE_KEY`
- `HCAPTCHA_SECRET_KEY`

The PHP runtime does not read `DATABASE_URL`. It builds a PDO DSN as:

```text
pgsql:host=<DB_HOST>;port=<DB_PORT>;dbname=<DB_NAME>
```

## Critical PostgreSQL Casing Finding

The PHP SQL uses unquoted camelCase identifiers such as `idMap`, `nameMap`, `idRecord`, `questionable_reason`, `PendingSubmission`, and `News`.

In PostgreSQL, unquoted identifiers are folded to lowercase. Therefore, the SQL expression `idMap` addresses a column named `idmap`, not a quoted column named `"idMap"`.

Runtime implication:

- a PostgreSQL table with quoted camelCase columns such as `"idMap"` would not satisfy these queries;
- the directly queryable physical columns must be lowercase equivalents such as `idmap`, `namemap`, `idrecord`;
- response field casing from PostgreSQL may be lowercase unless the SQL uses quoted aliases.

This is an important divergence from the frontend code, which often reads camelCase JSON keys like `idMap`, `nameMap`, `idVehicle`, `idRecord`, and `idTuningSetup`. The demo schema can add generated camelCase shadow columns for `SELECT *` endpoints, but SQL aliases like `AS idRecord` are still expected to return lowercase `idrecord` unless the PHP query is changed.

This casing issue must be validated against the real production database before any final migration decision.

## Runtime Tables

### `_map`

Used by:

- `php/load_data.php`
- `php/add_map.php`
- `php/submit_record.php`
- `auth/admin_pending.php`
- `php/api_records.php`

Columns used by PHP:

| Logical name in PHP SQL | PostgreSQL runtime identifier | Required | Notes |
| --- | --- | --- | --- |
| `idMap` | `idmap` | Yes | Manual id generation uses `MAX(idMap) + 1`. |
| `nameMap` | `namemap` | Yes | Duplicate check and public labels. |
| `special` | `special` | Optional | Returned by `SELECT *`; not written by PHP. |

Minimum behavior:

- `idmap` must be unique and stable.
- `namemap` should be unique for admin duplicate checks.

### `_vehicle`

Used by:

- `php/load_data.php`
- `php/add_vehicle.php`
- `php/submit_record.php`
- `auth/admin_pending.php`
- `php/api_records.php`

Columns used by PHP:

| Logical name in PHP SQL | PostgreSQL runtime identifier | Required | Notes |
| --- | --- | --- | --- |
| `idVehicle` | `idvehicle` | Yes | Manual id generation uses `MAX(idVehicle) + 1`. |
| `nameVehicle` | `namevehicle` | Yes | Duplicate check and public labels. |

### `_player`

Used by:

- `php/load_data.php`
- `php/submit_record.php`
- `auth/admin_pending.php`
- `php/api_records.php`

Columns used by PHP:

| Logical name in PHP SQL | PostgreSQL runtime identifier | Required | Notes |
| --- | --- | --- | --- |
| `idPlayer` | `idplayer` | Yes | Existing player validation; pending approval can create players with `MAX(idPlayer) + 1`. |
| `namePlayer` | `nameplayer` | Yes | Public/admin labels and duplicate lookup by exact name in pending approval. |
| `country` | `country` | Optional | Public display and API filters. |

### `_tuningpart`

Used by:

- `php/load_data.php`
- `php/add_tuning_part.php`
- `php/add_tuning_setup.php`
- `auth/admin_pending.php`
- `php/api_records.php`

Columns used by PHP:

| Logical name in PHP SQL | PostgreSQL runtime identifier | Required | Notes |
| --- | --- | --- | --- |
| `idTuningPart` | `idtuningpart` | Yes | Used in setup links. |
| `nameTuningPart` | `nametuningpart` | Yes | Public labels, duplicate check, pending approval lookup. |

Important behavior:

- `php/add_tuning_part.php` inserts only `nameTuningPart`, so `idtuningpart` needs an identity/default value.
- `nametuningpart` should be unique.

### `_tuningsetup`

Used by:

- `php/load_data.php`
- `php/add_tuning_setup.php`
- `auth/admin_pending.php`
- `php/assign_setup.php`
- `php/api_records.php`

Columns used by PHP:

| Logical name in PHP SQL | PostgreSQL runtime identifier | Required | Notes |
| --- | --- | --- | --- |
| `idTuningSetup` | `idtuningsetup` | Yes | Setup id. |

Important behavior:

- `php/add_tuning_setup.php` runs `INSERT INTO _tuningsetup DEFAULT VALUES` and then uses `$db->lastInsertId()`.
- `auth/admin_pending.php` manually creates setup ids using `MAX(idTuningSetup) + 1`.
- The schema needs to tolerate both identity/default insertion and manual id insertion.

### `_tuningsetupparts`

Used by:

- `php/load_data.php`
- `php/add_tuning_setup.php`
- `auth/admin_pending.php`
- `php/api_records.php`

Columns used by PHP:

| Logical name in PHP SQL | PostgreSQL runtime identifier | Required | Notes |
| --- | --- | --- | --- |
| `idTuningSetup` | `idtuningsetup` | Yes | Links to `_tuningsetup`. |
| `idTuningPart` | `idtuningpart` | Yes | Links to `_tuningpart`. |

Important behavior:

- Duplicate setup detection assumes the join table can be grouped by setup id.
- A setup must contain 3 or 4 parts according to PHP validation.

### `_worldrecord`

Used by:

- `php/load_data.php`
- `php/api_records.php`
- `php/submit_record.php`
- `php/delete_record.php`
- `php/set_questionable.php`
- `php/assign_setup.php`
- `auth/admin_pending.php`

Columns used by PHP:

| Logical name in PHP SQL | PostgreSQL runtime identifier | Required | Notes |
| --- | --- | --- | --- |
| `idRecord` | `idrecord` | Yes | Used for admin actions and API output. Needs identity/default. |
| `idMap` | `idmap` | Yes | Links to `_map`; record replacement deletes by map + vehicle. |
| `idVehicle` | `idvehicle` | Yes | Links to `_vehicle`; record replacement deletes by map + vehicle. |
| `idPlayer` | `idplayer` | Yes for current joins | Public `load_data.php` uses an inner join to `_player`. |
| `distance` | `distance` | Yes | Must be positive in PHP validation. |
| `current` | `current` | Yes | Public and API queries filter `current = 1`. |
| `idTuningSetup` | `idtuningsetup` | Optional | Links to `_tuningsetup`. |
| `questionable` | `questionable` | Yes | Expected to be `0` or `1`. |
| `questionable_reason` | `questionable_reason` | Optional | Used in public notes/search. |

Important behavior:

- `php/submit_record.php` deletes all existing records for a map/vehicle pair before inserting the new current record.
- `auth/admin_pending.php` also deletes by map/vehicle before approving a pending submission.
- `auth/admin_pending.php` inserts a world record with `RETURNING idRecord`.
- `php/load_data.php` requires `questionable_reason`, even though the old SQLite snapshots did not include it.
- `php/api_records.php` groups only by `wr.idRecord`, which works in PostgreSQL only if the database can infer functional dependency from `idrecord` as the primary key.

### `PendingSubmission`

Used by:

- `php/public_submit.php`
- `auth/admin_pending.php`

PostgreSQL runtime table name if unquoted:

- `pendingsubmission`

Columns used by PHP:

| Logical name in PHP SQL | PostgreSQL runtime identifier | Required | Notes |
| --- | --- | --- | --- |
| `id` | `id` | Yes | Needs identity/default. |
| `idMap` | `idmap` | Yes | Links to `_map`; nullable only if accepting incomplete data. |
| `idVehicle` | `idvehicle` | Yes | Links to `_vehicle`. |
| `distance` | `distance` | Yes | Positive by public validation. |
| `playerName` | `playername` | Yes | Submitted player label. |
| `playerCountry` | `playercountry` | Optional | Stored from public form. |
| `tuningParts` | `tuningparts` | Optional | Comma-separated tuning part names. |
| `submitterIp` | `submitterip` | Optional | Used for rate limiting; sensitive data. |
| `status` | `status` | Yes | Must default to `pending` for public submissions. |
| `submitted_at` | `submitted_at` | Yes | Must default to current timestamp; used for ordering and rate limit window. |

Important behavior:

- `php/public_submit.php` inserts without `status` and `submitted_at`; both need defaults.
- `auth/admin_pending.php` reads pending submissions with `p.*` and aliases `mapName`, `vehicleName`.
- Public submission rate limiting uses `NOW() - INTERVAL '1 hour'`.

### `News`

Used by:

- `php/get_news.php`
- `auth/post_news.php`

PostgreSQL runtime table name if unquoted:

- `news`

Columns used by PHP:

| Logical name in PHP SQL | PostgreSQL runtime identifier | Required | Notes |
| --- | --- | --- | --- |
| `id` | `id` | Yes | Needs identity/default. |
| `title` | `title` | Yes | Admin posting strips tags before insert. |
| `content` | `content` | Yes | Admin posting strips tags before insert. |
| `author` | `author` | Optional | From `$_SESSION['discord']['username']`. |
| `created_at` | `created_at` | Yes | Must default to current timestamp. |

## Non-Database Runtime State

The maintenance feature does not use the database. It uses a root-level `MAINTENANCE` flag file:

- `php/maintenance_helpers.php`
- `php/maintenance_status.php`
- `php/set_maintenance.php`
- `index.php`

Admin authorization is based on:

- signed `WC_TOKEN` cookie,
- `AUTH_SHARED_SECRET`,
- `ALLOWED_DISCORD_IDS`,
- PHP session state.

hCaptcha depends on:

- `HCAPTCHA_SITE_KEY`,
- `HCAPTCHA_SECRET_KEY`,
- external verification against `https://hcaptcha.com/siteverify`.

## Endpoint-To-Table Matrix

| Endpoint | Tables touched | Mode |
| --- | --- | --- |
| `php/load_data.php?type=maps` | `_map` | Read |
| `php/load_data.php?type=vehicles` | `_vehicle` | Read |
| `php/load_data.php?type=players` | `_player` | Read |
| `php/load_data.php?type=tuning_parts` | `_tuningpart` | Read |
| `php/load_data.php?type=tuning_setups` | `_tuningsetup`, `_tuningsetupparts`, `_tuningpart` | Read |
| `php/load_data.php?type=records` | `_worldrecord`, `_map`, `_vehicle`, `_player`, `_tuningsetupparts`, `_tuningpart` | Read |
| `php/api_records.php` | `_worldrecord`, `_map`, `_vehicle`, `_player`, `_tuningsetupparts`, `_tuningpart` | Read |
| `php/public_submit.php` | `PendingSubmission` | Write |
| `auth/admin_pending.php` GET | `PendingSubmission`, `_map`, `_vehicle` | Read |
| `auth/admin_pending.php` approve | `PendingSubmission`, `_worldrecord`, `_player`, `_tuningsetup`, `_tuningsetupparts`, `_tuningpart` | Write |
| `auth/admin_pending.php` reject | `PendingSubmission` | Write |
| `php/submit_record.php` | `_worldrecord`, `_player`, `_map`, `_vehicle` | Write |
| `php/delete_record.php` | `_worldrecord` | Write |
| `php/set_questionable.php` | `_worldrecord` | Write |
| `php/assign_setup.php` | `_worldrecord`, `_tuningsetup` | Write |
| `php/add_map.php` | `_map` | Write |
| `php/add_vehicle.php` | `_vehicle` | Write |
| `php/add_tuning_part.php` | `_tuningpart` | Write |
| `php/add_tuning_setup.php` | `_tuningsetup`, `_tuningsetupparts` | Write |
| `php/get_news.php` | `News` | Read |
| `auth/post_news.php` | `News` | Write |
| `auth/admin_actions.php` integrity | database connection only, `SELECT 1` | Read |

## Minimum Demo Data

To test the public legacy site:

- at least two maps,
- at least two vehicles,
- at least two players,
- at least four tuning parts,
- at least one tuning setup with three parts,
- at least one current world record,
- at least one news item.

To test admin screens safely:

- the same public data,
- at least one current record with no tuning setup for assignment tests,
- at least one `PendingSubmission` row with `status = 'pending'`,
- a local signed admin `WC_TOKEN` using `AUTH_SHARED_SECRET`,
- `ALLOWED_DISCORD_IDS` containing the token `sub`.

To test public submissions:

- hCaptcha must be mocked or a development hCaptcha secret must be provided.
- Without that, `php/public_submit.php` will correctly reject submissions before inserting.

## SQLite Snapshot Divergences

The historical SQLite snapshots are useful but are not authoritative for runtime PostgreSQL.

Observed divergences:

- SQLite table names are unprefixed (`Map`, `Vehicle`, `WorldRecord`) while PHP expects `_map`, `_vehicle`, `_worldrecord`.
- SQLite snapshots did not expose `idRecord` and `questionable_reason` on `WorldRecord`, but PHP requires both.
- PostgreSQL-specific SQL is used: `string_agg`, `NOW() - INTERVAL '1 hour'`, `RETURNING`, `DEFAULT VALUES`.
- PHP mixes manual id generation with identity/default insertion.
- PostgreSQL unquoted identifier casing can diverge from frontend camelCase expectations.

## Issues Found During Static Analysis

- `php/delete_record.php` requires `__DIR__ . '/auth/check_auth.php'` even though the file lives under `php/`; the likely intended path is `../auth/check_auth.php`. This appears to be a pre-existing legacy issue and was not changed in this pass.
- `php/assign_setup.php` authorizes using PHP session state directly instead of `ensure_authorized_json()`. It may require the admin page to have established `$_SESSION['discord']` before API calls.
- `php/api_records.php` groups by `wr.idRecord` only while selecting many non-aggregated columns. This relies on PostgreSQL primary-key functional dependency inference and can fail if the schema does not declare `idrecord` as a primary key.
- hCaptcha makes public submission end-to-end tests dependent on external credentials or an explicit mock strategy.

## Remaining Unknowns

The following cannot be proven from code alone:

- exact production PostgreSQL DDL,
- whether production uses lowercase physical columns, quoted columns, views, or another compatibility layer,
- how production handles JSON key casing for `SELECT *` endpoints,
- whether `$db->lastInsertId()` works reliably with the current production `_tuningsetup` sequence,
- final intended constraints and indexes.

The local dev database should be treated as a safe compatibility environment, not as proof of the production schema.
