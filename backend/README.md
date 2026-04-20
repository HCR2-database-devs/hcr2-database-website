# HCR2 Records Backend

FastAPI backend for the HCR2 records application.

## Run Locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Checks

```powershell
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m pytest
```

## Main Routes

- `GET /health`
- `GET /api/v1/maps`
- `GET /api/v1/vehicles`
- `GET /api/v1/players`
- `GET /api/v1/tuning-parts`
- `GET /api/v1/tuning-setups`
- `GET /api/v1/records`
- `GET /api/v1/news`
- `GET /api/v1/auth/status`
- `GET /api/v1/admin/records`
- `GET /api/v1/admin/pending`

Admin write routes require a valid `WC_TOKEN` cookie.
