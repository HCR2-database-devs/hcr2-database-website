# HCR2 Records Backend

FastAPI backend scaffold for the progressive migration from the legacy PHP app.

This scaffold is intentionally isolated: it does not replace any legacy PHP route yet.

## Local setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn app.main:app --reload
```

Health endpoints:

- `GET /health`
- `GET /api/v1/health`

## Configuration

Copy `backend/.env.example` or the root `.env.example` to `.env`, then fill the same variables used by the legacy PHP app.

The first migration phases must keep these contracts compatible:

- PostgreSQL settings: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`
- JWT auth: `AUTH_SHARED_SECRET`, `ALLOWED_DISCORD_IDS`
- API keys: `API_KEYS`
- hCaptcha: `HCAPTCHA_SITE_KEY`, `HCAPTCHA_SECRET_KEY`

