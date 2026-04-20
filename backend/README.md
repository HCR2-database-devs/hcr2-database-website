# HCR2 Records Backend

FastAPI backend for the progressive migration from the legacy PHP app.

The backend currently exposes health checks, public read-only data endpoints, auth status/logout compatibility routes, public news and hCaptcha site-key routes. The legacy PHP files remain in place until the migration is fully validated.

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

Public data endpoints:

- `GET /php/load_data.php?type=maps`
- `GET /php/load_data.php?type=vehicles`
- `GET /php/load_data.php?type=players`
- `GET /php/load_data.php?type=tuning_parts`
- `GET /php/load_data.php?type=tuning_setups`
- `GET /php/load_data.php?type=records`
- `GET /api/v1/maps`
- `GET /api/v1/vehicles`
- `GET /api/v1/players`
- `GET /api/v1/tuning-parts`
- `GET /api/v1/tuning-setups`
- `GET /api/v1/records`

Public utility endpoints:

- `GET /auth/status.php`
- `GET /auth/logout.php`
- `GET /php/get_news.php`
- `GET /php/get_hcaptcha_sitekey.php`
- `GET /api/v1/auth/status`
- `GET /api/v1/auth/logout`
- `GET /api/v1/news`
- `GET /api/v1/hcaptcha/sitekey`

## Configuration

Copy `backend/.env.example` or the root `.env.example` to `.env`, then fill the same variables used by the legacy PHP app.

The first migration phases must keep these contracts compatible:

- PostgreSQL settings: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`
- JWT auth: `AUTH_SHARED_SECRET`, `ALLOWED_DISCORD_IDS`
- API keys: `API_KEYS`
- hCaptcha: `HCAPTCHA_SITE_KEY`, `HCAPTCHA_SECRET_KEY`
