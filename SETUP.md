# Setup

## Prerequisites

- Windows PowerShell
- Docker Desktop
- Python 3.11 or newer
- Node.js 20 or newer

## Environment

Use `.env.dev.example` for local development.

The development scripts set the required backend variables automatically:

```text
DB_HOST=127.0.0.1
DB_PORT=54329
DB_NAME=hcr2_dev
DB_USER=hcr2_dev
DB_PASS=hcr2_dev_password
AUTH_SHARED_SECRET=dev-only-hcr2-secret
ALLOWED_DISCORD_IDS=dev-admin
HCAPTCHA_SITE_KEY=dev-hcaptcha-site-key
HCAPTCHA_SECRET_KEY=dev-hcaptcha-secret-key
```

For production, provide real values in the deployment environment. Do not commit `.env`.

## Install Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
cd ..
```

## Install Frontend

```powershell
cd frontend
npm install
cd ..
```

## Start Application Stack

```powershell
.\scripts\dev\start-app-stack.ps1 -RestartFastApi -RestartFrontend
```

By default, the application stack uses PostgreSQL settings from `.env` when they are configured.
If the database is only reachable through SSH, open a local tunnel first:

```powershell
.\scripts\dev\start-ssh-tunnel.ps1 -SshHost your-ssh-host -SshUser your-ssh-user -RemoteHost 127.0.0.1 -RemotePort 5432 -LocalPort 54329
```

Then point the backend at the forwarded port in `backend/.env` or in the current shell:

```text
DB_HOST=127.0.0.1
DB_PORT=54329
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASS=your_database_password
DATABASE_URL=
```

`DATABASE_URL` has priority over the `DB_*` values, so leave it empty or update it to the local
forwarded port when using the tunnel.

If no PostgreSQL settings are configured, the script falls back to the local Docker PostgreSQL
database. You can also force the local Docker database explicitly:

```powershell
.\scripts\dev\start-app-stack.ps1 -RestartFastApi -RestartFrontend -UseLocalPostgres
```

Only use the reset script for the local Docker database:

```powershell
.\scripts\dev\reset-dev-database.ps1
```

With `-RestartFastApi` and `-RestartFrontend`, the script only stops local processes that match
this project's FastAPI or Vite commands. If another application is using port `8000` or `5173`, it
refuses to stop it and prints an error instead.

If Docker Desktop is slow to respond, the Docker startup step times out after 45 seconds by default.
You can raise the limit for one run:

```powershell
$env:DEV_DOCKER_TIMEOUT_SECONDS = "120"
.\scripts\dev\start-app-stack.ps1 -RestartFastApi -RestartFrontend
```

Open `http://127.0.0.1:5173`.

## Demo Admin Cookie

Generate a local admin token:

```powershell
.\scripts\dev\make-dev-wc-token.ps1
```

Set the printed `WC_TOKEN` value as a browser cookie for `127.0.0.1`, then open `/admin`.
