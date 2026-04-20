# Development

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
