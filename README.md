# HCR2 Adventure Records Database

Unofficial Hill Climb Racing 2 adventure records website.

The application is now built on one official stack:

- FastAPI backend
- React + Vite + TypeScript frontend
- React Router
- TanStack Query
- PostgreSQL

## Project Layout

```text
backend/                 FastAPI API, services, repositories and tests
frontend/                React/Vite app, public assets and styles
infra/dev/               Local PostgreSQL dev database
scripts/dev/             Local setup, reset and smoke-test scripts
docs/                    Current project notes and alignment report
to_delete/               Deprecated PHP/HTML/JS stack kept only for later deletion
```

## Main Features

- Public data views for maps, vehicles, players, tuning parts, tuning setups and records.
- Records search, filters, sorting and CSV export.
- Public news modal.
- Public record submission for admin review.
- Discord-cookie based admin access.
- Admin workflows for records, catalog data, pending submissions, news, maintenance and DB integrity.
- Local PostgreSQL demo database with seed data.

## Quick Start

```powershell
.\scripts\dev\reset-dev-database.ps1
.\scripts\dev\start-app-stack.ps1 -RestartFastApi -RestartFrontend
node .\scripts\dev\test_system_smoke.mjs
```

Local URLs:

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`
- Backend health: `http://127.0.0.1:8000/health`
- PostgreSQL: `127.0.0.1:54329`

## Documentation

- [SETUP.md](SETUP.md) explains installation and environment setup.
- [DEV.md](DEV.md) lists useful development commands.
- [ADMIN.md](ADMIN.md) explains admin access and workflows.
- [docs/README.md](docs/README.md) records the current stack, supported workflows and validation baseline.
- [docs/main-refactor-alignment-report.md](docs/main-refactor-alignment-report.md) records the `main` alignment decisions.

## Deprecated Stack

The old PHP/HTML/CSS/vanilla JS stack has been moved to `to_delete/`.

It is not part of the official runtime anymore. Keep it only as a short-term reference until the team is comfortable deleting it.
