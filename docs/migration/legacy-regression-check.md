# Legacy Regression Check

Date: 2026-04-20
Branch: `refactor/fastapi-react-migration`

This report records the legacy checks executed against the local PostgreSQL demo database and the PHP legacy server. It distinguishes executed checks from static findings and keeps known legacy issues explicit.

## Environment Used

- PostgreSQL 16 from `infra/dev/docker-compose.yml`
- Database host from Windows: `127.0.0.1:54329`
- Legacy PHP 8.3 server from Docker: `http://127.0.0.1:18080`
- Demo schema: `infra/dev/postgres/init/001_schema.sql`
- Demo data: `infra/dev/postgres/init/002_seed_demo.sql`
- Regression script: `scripts/dev/test_legacy_regression.py`

The PHP service runs in Docker because the local Windows PHP available during this pass was PHP 7.4 without `pdo_pgsql`. The legacy code now requires PHP 8+ helpers such as `str_starts_with`, and PostgreSQL access needs `pdo_pgsql`.

Port `8080` was already occupied locally by another service during testing, so the dev legacy server is exposed on `18080`.

## Commands Executed

```powershell
.\scripts\dev\reset-dev-database.ps1
.\scripts\dev\start-dev-stack.ps1
python scripts\dev\test_legacy_regression.py
```

The database reset recreated and reseeded the PostgreSQL volume successfully. The stack then started with PostgreSQL healthy and the legacy PHP server reachable.

## Executed Checks

The following checks passed:

- `GET /` returns the public legacy index.
- `GET /css/style.css` serves the legacy CSS.
- `GET /img/hcrdatabaselogo.png` serves the legacy logo.
- `GET /php/maintenance_status.php` returns `maintenance = false`.
- `GET /php/load_data.php?type=maps` returns demo maps.
- `GET /php/load_data.php?type=vehicles` returns demo vehicles.
- `GET /php/load_data.php?type=players` returns demo players.
- `GET /php/load_data.php?type=tuning_parts` returns demo tuning parts.
- `GET /php/load_data.php?type=tuning_setups` returns demo tuning setups.
- `GET /php/load_data.php?type=records` returns demo records.
- `GET /php/get_news.php` returns demo news.
- `GET /php/get_hcaptcha_sitekey.php` returns the development hCaptcha site key.
- `GET /auth/status.php` without a cookie reports a logged-out user.
- `GET /auth/status.php` with a generated development `WC_TOKEN` reports an allowed admin user.
- `GET /php/api_records.php` without an API key returns `401`.
- `GET /auth/admin_pending.php` with an admin token returns pending submissions.
- `POST /auth/admin_actions.php` with `action=integrity` returns `ok = true`.
- `POST /php/public_submit.php` without a valid hCaptcha token returns the expected hCaptcha rejection.

Additional validation executed during this pass:

- targeted PHP syntax checks passed for `auth/config.php`, `php/load_data.php`, `php/get_hcaptcha_sitekey.php`, `php/api_records.php`, and `php/delete_record.php`;
- `python -m py_compile scripts\dev\test_legacy_regression.py` passed;
- backend tests passed with `21 passed`;
- backend lint passed with `ruff check .`;
- frontend production build passed with `npm run build`;
- seeded PostgreSQL counts were verified: 3 maps, 3 vehicles, 3 players, 5 tuning parts, 2 tuning setups, 3 world records, 2 pending submissions, and 2 news items.

## Known Expected Failures

These are real legacy issues observed against PostgreSQL. They are marked as `XFAIL` in the regression script only when the exact known failure signature is still present, so future unexpected breakages remain visible.

- `GET /php/api_records.php?api_key=dev-api-key` returns `500 {"error":"Database query failed"}`. Static analysis points to PostgreSQL `GROUP BY` incompatibility: the query selects many joined columns while grouping only by `wr.idRecord`.
- `POST /php/delete_record.php` returns HTTP `200` with a PHP fatal error body because it includes `__DIR__ . '/auth/check_auth.php'` from inside `php/`, which resolves to the non-existent path `php/auth/check_auth.php`.

## Fixes Made During This Pass

- `auth/config.php` now guards `safe_json_error()` and `generic_database_error()` with `function_exists`.

Reason: `php/load_data.php` and `php/get_hcaptcha_sitekey.php` define `safe_json_error()` before requiring `auth/config.php`. Without the guard, PHP fatals with a redeclaration error. The fix preserves the existing helper behavior and only prevents duplicate declarations.

## Static Findings Confirmed By Runtime

- PostgreSQL folds unquoted identifiers and aliases to lowercase. Queries such as `SELECT idMap` return column names such as `idmap`.
- Some `SELECT *` routes receive camelCase compatibility columns from the dev schema, but explicit aliases such as `AS idRecord` still return lowercase `idrecord` unless quoted in PHP.
- `php/load_data.php?type=records` is reachable, but the JSON currently exposes lowercase record identifiers in PostgreSQL.

## Not Fully Tested

- Successful public submission was not tested because `php/public_submit.php` verifies against the real hCaptcha service. The safe local check validates the rejection path only.
- Browser-level admin UI navigation was not manually tested in this pass. Admin status and read-only pending-submission endpoints were tested through HTTP with a generated signed development token.
- Mutating admin actions such as approve/reject were not executed because the current goal was to verify non-regression safely without consuming or changing demo records beyond read/integrity checks.

## Current Confidence

- Legacy public static pages and assets: high.
- Legacy read-only public data routes: medium-high, with identifier casing caveats.
- Legacy auth status with development token: high.
- Legacy admin read routes: medium.
- Legacy PostgreSQL compatibility overall: medium, because the authorized API records endpoint and `delete_record.php` still need deliberate fixes.
