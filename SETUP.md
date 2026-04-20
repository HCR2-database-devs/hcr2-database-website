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

## Start Local Stack

```powershell
.\scripts\dev\reset-dev-database.ps1
.\scripts\dev\start-app-stack.ps1 -RestartFastApi -RestartFrontend
```

Open `http://127.0.0.1:5173`.

## Demo Admin Cookie

Generate a local admin token:

```powershell
.\scripts\dev\make-dev-wc-token.ps1
```

Set the printed `WC_TOKEN` value as a browser cookie for `127.0.0.1`, then open `/admin`.
