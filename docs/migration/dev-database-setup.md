# Development Database Setup

Date: 2026-04-20
Branch: `refactor/fastapi-react-migration`

This document explains the safe local PostgreSQL development database added for legacy and FastAPI testing.

## What Was Added

Files:

- `.env.dev.example`
- `infra/dev/docker-compose.yml`
- `infra/dev/php/Dockerfile`
- `infra/dev/postgres/init/001_schema.sql`
- `infra/dev/postgres/init/002_seed_demo.sql`
- `scripts/dev/start-dev-stack.ps1`
- `scripts/dev/reset-dev-database.ps1`
- `scripts/dev/stop-dev-stack.ps1`
- `scripts/dev/make-dev-wc-token.ps1`

Services:

- PostgreSQL 16 on host port `54329`.
- PHP 8.3 legacy server with `pdo_pgsql` on `http://127.0.0.1:8080`.

The Docker PHP service is intentional. The local Windows PHP detected during this pass is PHP 7.4 and does not include `pdo_pgsql`; the legacy code requires PHP 8+ functions such as `str_starts_with` and needs PostgreSQL PDO support.

## Start The Dev Stack

```powershell
.\scripts\dev\start-dev-stack.ps1
```

Expected local URLs:

- legacy PHP: `http://127.0.0.1:8080`
- PostgreSQL: `127.0.0.1:54329`

## Reset And Reseed The Database

```powershell
.\scripts\dev\reset-dev-database.ps1
```

This removes the Docker PostgreSQL volume and recreates the database from:

- `infra/dev/postgres/init/001_schema.sql`
- `infra/dev/postgres/init/002_seed_demo.sql`

## Stop The Dev Stack

```powershell
.\scripts\dev\stop-dev-stack.ps1
```

## Host Environment For FastAPI

For the host FastAPI backend, copy:

```text
.env.dev.example -> .env
```

The relevant development values are:

```text
DB_HOST=127.0.0.1
DB_PORT=54329
DB_NAME=hcr2_dev
DB_USER=hcr2_dev
DB_PASS=hcr2_dev_password
DATABASE_URL=postgresql://hcr2_dev:hcr2_dev_password@127.0.0.1:54329/hcr2_dev
AUTH_SHARED_SECRET=dev-only-hcr2-secret
ALLOWED_DISCORD_IDS=dev-admin
API_KEYS=dev-api-key
```

Do not commit `.env`; it remains ignored.

## Legacy Docker Environment

The Docker legacy PHP service receives environment variables directly from `infra/dev/docker-compose.yml`:

```text
DB_HOST=postgres
DB_PORT=5432
DB_NAME=hcr2_dev
DB_USER=hcr2_dev
DB_PASS=hcr2_dev_password
AUTH_SHARED_SECRET=dev-only-hcr2-secret
ALLOWED_DISCORD_IDS=dev-admin
API_KEYS=dev-api-key
```

The legacy PHP code can still load a root `.env`, but the Docker service does not require one.

## Demo Data

The seed data includes:

- 3 maps,
- 3 vehicles,
- 3 players,
- 5 tuning parts,
- 2 tuning setups,
- 3 current world records,
- 2 pending submissions,
- 2 news items.

The demo data is synthetic and does not contain production records, real submitter IPs, real auth secrets, or real hCaptcha credentials.

## Local Admin Token

Generate a development `WC_TOKEN`:

```powershell
.\scripts\dev\make-dev-wc-token.ps1
```

The token uses:

- `sub = dev-admin`
- `username = Dev Admin`
- `AUTH_SHARED_SECRET = dev-only-hcr2-secret`

To test admin pages in a browser, set the generated value as a `WC_TOKEN` cookie for `127.0.0.1`.

## Runtime Schema Strategy

The physical PostgreSQL columns are lowercase because the PHP SQL uses unquoted identifiers. For some `SELECT *` routes, the dev schema adds generated camelCase shadow columns such as `"idMap"` and `"nameMap"` so the legacy frontend can receive the camelCase keys it often expects.

This is a development compatibility measure, not proof of the production schema.

Known casing limitation:

- SQL aliases such as `AS idRecord` are still parsed by PostgreSQL as lowercase aliases unless the PHP query quotes them.
- Therefore some legacy JSON responses may expose `idrecord` instead of `idRecord`.
- This is documented in `postgresql-runtime-schema-analysis.md` and should be validated against production before changing code.

## hCaptcha Limitation

The dev setup provides placeholder hCaptcha values only. `php/public_submit.php` still verifies against the real hCaptcha API, so full public submission success is not expected unless valid development hCaptcha credentials are provided or a safe mock strategy is added.

## Safe Usage Rules

- Use this database only for development and regression testing.
- Never point this compose stack at production credentials.
- Reset with `reset-dev-database.ps1` whenever tests mutate data.
- Keep `.env` local and untracked.
