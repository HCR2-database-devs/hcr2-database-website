# PostgreSQL API audit

Date: 2026-04-22

## Scope

Audited PHP endpoints exposed under `/php`, `/auth`, and `/index.php` for the SQLite to PostgreSQL migration. Verification was run with `API_DRY_RUN=1` so write routes executed inside transactions that were rolled back, hCaptcha was mocked, and file/maintenance side effects were skipped.

## How to rerun

```bash
./scripts/dry_run_api_check.sh
```

The script starts `php -S 127.0.0.1:8765 -t .` with `API_DRY_RUN=1`, generates a temporary admin JWT from local env config without printing secrets, runs endpoint checks, and fails on HTTP 5xx or suspicious PHP server log entries.

## Endpoint map

| Endpoint | Method | Access | DB / side effects | Status |
| --- | --- | --- | --- | --- |
| `/index.php` | GET | public | maintenance HTML gate | syntax checked |
| `/php/load_data.php?type=maps` | GET | public, maintenance gated | `_map` | passed |
| `/php/load_data.php?type=vehicles` | GET | public, maintenance gated | `_vehicle` | passed |
| `/php/load_data.php?type=players` | GET | public, maintenance gated | `_player` | passed |
| `/php/load_data.php?type=tuning_parts` | GET | public, maintenance gated | `_tuningpart` | passed |
| `/php/load_data.php?type=tuning_setups` | GET | public, maintenance gated | `_tuningsetup`, `_tuningsetupparts`, `_tuningpart` | passed |
| `/php/load_data.php?type=records` | GET | public, maintenance gated | `_worldrecord` joins | passed |
| `/php/api_records.php` | GET | API key | `_worldrecord` joins, filters, pagination | passed |
| `/php/get_news.php` | GET | public, maintenance gated | `news` + `_news` | passed |
| `/php/get_hcaptcha_sitekey.php` | GET | public | config only | passed |
| `/php/maintenance_status.php` | GET | public/admin-aware | maintenance flag | passed |
| `/php/public_submit.php` | POST | public, hCaptcha | `_pendingsubmission`, hCaptcha | passed dry-run |
| `/php/submit_record.php` | POST | admin JWT | `_worldrecord`, `_player` | passed dry-run |
| `/php/delete_record.php` | POST | admin JWT | `_worldrecord` delete | passed dry-run |
| `/php/set_questionable.php` | POST | admin JWT | `_worldrecord` update | passed dry-run |
| `/php/assign_setup.php` | POST | admin JWT | `_worldrecord`, `_tuningsetup` | passed dry-run |
| `/php/add_map.php` | POST | admin JWT | `_map`, optional icon upload | passed dry-run |
| `/php/add_vehicle.php` | POST | admin JWT | `_vehicle`, optional icon upload | passed dry-run |
| `/php/add_tuning_part.php` | POST | admin JWT | `_tuningpart`, optional icon upload | passed dry-run |
| `/php/add_tuning_setup.php` | POST | admin JWT | `_tuningsetup`, `_tuningsetupparts` | passed dry-run |
| `/php/set_maintenance.php` | POST | admin JWT | maintenance flag file | passed dry-run |
| `/auth/status.php` | GET | public with optional JWT | session/auth status | passed |
| `/auth/logout.php` | GET | public | clears cookie/session | syntax checked only |
| `/auth/admin_pending.php` | GET | admin JWT | `_pendingsubmission` joins | passed |
| `/auth/admin_pending.php` | POST | admin JWT | approve/reject pending submissions | SQL corrected, dry-run path covered where possible |
| `/auth/admin_actions.php` | GET/POST | admin JWT | backup listing/integrity/delete | passed for safe GET, delete dry-run guarded |
| `/auth/post_news.php` | POST | admin JWT | `news` insert | passed dry-run |
| `/php/admin.php` | GET | admin JWT | admin UI | syntax checked |
| `/php/test_curl.php`, `/test_curl.php` | GET/CLI | test utility | external HTTP diagnostics | syntax checked only |

## Initial failures found

| Area | Cause | Fix |
| --- | --- | --- |
| Mixed-case columns | PostgreSQL requires quoted identifiers for imported columns like `"idMap"`, `"nameVehicle"`, `"idTuningSetup"`; unquoted SQLite-style SQL became lowercase and failed. | Quoted affected identifiers in admin/write endpoints and tuning setup queries. |
| Missing `idRecord` | Current `_worldrecord` table has no `idRecord`, while UI and endpoints expected it. | Added a stable synthetic record key `idMap:idVehicle` for current records and updated delete/questionable/assign routes to parse it. |
| Empty tuning setup casts | `CAST(wr."idTuningSetup" AS smallint)` fails on empty strings. | Replaced with `NULLIF(wr."idTuningSetup", '')::smallint`. |
| No autoincrement on imported tables | Tables such as `_tuningpart` and `_tuningsetup` have no defaults/sequences, so `DEFAULT VALUES` or omitted ids fail. | Allocate next ids with `MAX(...) + 1` to match existing project pattern. |
| Pending submissions table mismatch | The DB has both `pendingsubmission` and `_pendingsubmission`; only `_pendingsubmission` has `tuningParts`. | Prefer `_pendingsubmission` and quote its imported columns. |
| News split across tables | Existing news data is in `_news`, while new posts use `news`. | `get_news` now reads a union of both tables; posting stays on `news`. |
| Auth inconsistency | `assign_setup` and `set_maintenance` depended on session-only admin checks, unlike other admin JSON routes. | Switched them to `ensure_authorized_json()`. |
| Wrong include path | `php/delete_record.php` required `php/auth/check_auth.php`, which does not exist. | Fixed to `../auth/check_auth.php`. |
| Strict varchar limits | PostgreSQL rejected overlong vehicle/tuning names with 500 errors. | Added explicit 400 validation for known schema limits. |
| hCaptcha dry-run and constant usage | Public submit referenced an undefined variable and would call hCaptcha during tests. | Use `HCAPTCHA_SECRET_KEY` constant and bypass hCaptcha only when `API_DRY_RUN=1`. |
| Dangerous side effects in tests | Write routes, icon uploads, maintenance toggles, backup deletion could alter state. | Added `API_DRY_RUN=1` transaction rollback and side-effect skips. |

## Files changed

- `auth/config.php`
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
- `php/set_maintenance.php`
- `scripts/dry_run_api_check.sh`
- `docs/postgresql-api-audit.md`

## Verification performed

- `php -l` on all PHP files: passed.
- Metadata inspection of PostgreSQL schemas/columns: completed.
- Query probes for quoted vs unquoted identifiers: reproduced failures.
- Local dry-run API campaign: passed all scripted checks.

## Residual risks

- `_worldrecord` still has no real primary key. The synthetic `idMap:idVehicle` key is safe for current records but cannot distinguish historical duplicates for the same map/vehicle. A future schema migration should add a real `idRecord` or composite unique key for current records.
- Imported legacy tables have weak typing and missing constraints/sequences. The code now works with them, but a planned migration should normalize defaults, primary keys, foreign keys, and timestamps.
- `admin_pending` approve/reject could not be fully exercised against a real pending row without creating persistent data; SQL paths were corrected and the general dry-run framework is in place.
- The old public `test_curl.php` utilities can perform external calls by design; they were not executed as part of the safe campaign.

## Recommendations

1. Add a real PostgreSQL migration to create primary keys, sequences, and foreign keys for `_map`, `_vehicle`, `_player`, `_worldrecord`, `_tuningpart`, `_tuningsetup`, and `_tuningsetupparts`.
2. Consolidate `news`/`_news` and `pendingsubmission`/`_pendingsubmission` into one table each after backfilling data.
3. Replace `MAX(id) + 1` allocation with sequences once schema ownership is settled.
4. Keep `API_DRY_RUN=1` in staging and CI endpoint smoke checks.
5. Add automated tests around record creation, pending approval, and current-record uniqueness after the schema is normalized.
