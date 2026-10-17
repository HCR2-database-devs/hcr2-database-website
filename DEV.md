# Development

The `scripts/dev/*.ps1` helpers are PowerShell and assume Windows. On Linux and
macOS run the three processes directly instead — see
[Linux / macOS](#linux--macos) below.

## Common Commands

Reset and seed the local PostgreSQL database:

```powershell
.\scripts\dev\reset-dev-database.ps1
```

Start PostgreSQL, FastAPI and Vite:

```powershell
.\scripts\dev\start-app-stack.ps1 -RestartFastApi -RestartFrontend
```

Stop Docker services:

```powershell
.\scripts\dev\stop-dev-stack.ps1
```

Run the full smoke test:

```powershell
node .\scripts\dev\test_system_smoke.mjs
```

## Backend Checks

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m pytest
cd ..
```

## Frontend Checks

```powershell
cd frontend
npm run build
cd ..
```

## Smoke Coverage

`scripts/dev/test_system_smoke.mjs` verifies:

- public API routes
- frontend proxying
- auth status
- public submit validation
- public pages
- records filters
- news modal
- dark mode
- admin API workflows
- admin page rendering
- maintenance controls
- DB integrity check
- backup create/list/download/delete

## Linux / macOS

The dev stack is three processes: PostgreSQL, FastAPI and Vite.

### 1. Environment

```bash
cp .env.dev.example .env
```

`.env` at the repo root is read by both the backend and the migration runner
(`app/core/config.py` resolves `REPO_ROOT/.env` first, then `backend/.env`).

### 2. Database

```bash
docker compose -f infra/dev/docker-compose.yml up -d
```

This seeds `hcr2_dev` on port `54329` from `infra/dev/postgres/init/`. That init
script covers the core game tables only — **not** the community tables — so apply
the remaining migrations once:

```bash
python3 scripts/migrate.py status
python3 scripts/migrate.py up
```

`hcr2_account_linking` needs the Phase 4 migration applied too, otherwise
community profile endpoints fail with a database error because
`PROFILE_COLUMNS` selects from `hcr2_account_link`.

To wipe and re-seed:

```bash
docker compose -f infra/dev/docker-compose.yml down -v
docker compose -f infra/dev/docker-compose.yml up -d
```

### 3. Backend

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Check it with `curl http://127.0.0.1:8000/health`.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite serves on `http://localhost:5173` and proxies `/api`, `/auth` and `/health`
to `http://127.0.0.1:8000` (override with `VITE_PROXY_TARGET`).

### 5. Sign in

`scripts/dev/make-dev-wc-token.ps1` only runs on Windows. On Linux, mint a dev
token with the same shared secret from `.env`:

```bash
cd backend
. .venv/bin/activate
python3 -c "
import base64, hashlib, hmac, json, time
from app.core.config import get_settings
s = get_settings()
b = lambda r: base64.urlsafe_b64encode(r).decode().rstrip('=')
h = b(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode())
p = b(json.dumps({'sub': 'dev-beta', 'username': 'Dev Beta',
                  'exp': int(time.time()) + 86400}).encode())
g = b(hmac.new(s.auth_shared_secret.encode(),
               f'{h}.{p}'.encode(), hashlib.sha256).digest())
print(f'{h}.{p}.{g}')"
```

Use `dev-beta` for `sub` to get **beta** access (Phase 4 ships `BETA`) and
`dev-admin` to get **admin** access, matching `BETA_DISCORD_IDS` and
`ALLOWED_DISCORD_IDS` in `.env.dev.example`. Replace `sub` with `username` to
see a display name.

Set it as the `WC_TOKEN` cookie in the browser:

- Chrome / Edge: DevTools → Application → Cookies → `http://localhost:5173`
- Firefox: DevTools → Storage → Cookies → `localhost:5173`

## Phase 4 quick check

With a `dev-beta` token signed in, open <http://localhost:5173/account> and use
the **Linked HCR2 Account** card. To test the admin queue as well, sign in a
second browser profile with a `dev-admin` token and open `/admin` →
**Community** → **HCR2 account links**.

Useful dev overrides:

- `FEATURE_HCR2_ACCOUNT_LINKING=ENABLED` to open the feature to any signed-in
  user.
- `HCR2_LINK_CODE_REROLL_COOLDOWN_SECONDS=1` to iterate on the reroll flow
  without waiting 10 seconds.
