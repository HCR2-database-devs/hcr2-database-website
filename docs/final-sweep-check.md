# Final Sweep Check

## Open Items At Start

- Admin "Database & Backups" was visible but only integrity was connected.
- Admin catalog icon file inputs were visible but not sent to FastAPI.
- Public submit modal kept hCaptcha markup but did not load/render the configured site key.
- Smoke checks did not cover backup routes or multipart admin catalog routes.

## Corrected And Connected

- Added FastAPI admin backup routes for create, list, download and delete.
- Added an application SQL backup generator for the known PostgreSQL tables.
- Connected the React admin backup block to the new routes.
- Kept SQL import/restore disabled with explicit UI copy because they are destructive operations.
- Added multipart FastAPI catalog routes for map, vehicle and tuning-part icon uploads.
- Updated React admin catalog forms to send optional SVG icons.
- Loaded the hCaptcha site key in the public submit modal and prepared widget rendering.
- Extended system smoke tests for backups, multipart admin routes and hCaptcha site key display.

## Recovered During Sweep

- `.sql` backups are now ignored by Git.
- News smoke validation no longer depends on one seed item being present in the latest 10 news.
- The seeded pending submission flow is verified after resetting the dev database.

## Working Now

- Public data pages, records filters, stats, news modal, dark mode and public submit modal.
- Admin record submit/status/assign/delete workflows.
- Admin catalog additions through JSON and multipart form routes.
- Pending submission approval.
- News posting.
- Maintenance controls.
- Integrity check.
- Backup create/list/download/delete.

## Still Not Implemented

- Browser-based PostgreSQL restore.
- Browser-based SQL import.

These remain intentionally out of the React admin because they are destructive and need reviewed operational tooling.

## Verification Run

- `backend`: `python -m ruff check .`
- `backend`: `python -m pytest` (`24 passed`)
- `frontend`: `npm run build`
- dev DB reset: `scripts/dev/reset-dev-database.ps1`
- stack restart: `scripts/dev/start-app-stack.ps1 -RestartFastApi -RestartFrontend`
- system smoke: `node scripts/dev/test_system_smoke.mjs`
