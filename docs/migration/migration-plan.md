# Migration Plan

Date: 2026-04-20

Goal: move the existing project to FastAPI and React without functional, data or visual regressions.

## Non-Negotiable Principles

- No big bang rewrite.
- No product changes unless explicitly requested.
- Legacy routes remain available while legacy code depends on them.
- JSON response shapes remain compatible.
- Existing visual output is the reference.
- Existing assets are preserved.
- Legacy behavior that looks suspicious is documented before being changed.
- Legacy code is removed only after the replacement has been verified.

## Target Repository Layout

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- api/
|   |   |-- core/
|   |   |-- db/
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- services/
|   |   |-- repositories/
|   |   `-- utils/
|   `-- tests/
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   |-- pages/
|   |   |-- components/
|   |   |-- features/
|   |   |-- services/
|   |   |-- hooks/
|   |   |-- lib/
|   |   |-- types/
|   |   |-- assets/
|   |   `-- styles/
|   `-- tests/
|-- docs/
|   `-- migration/
|-- scripts/
|-- infra/
`-- legacy/
```

The `legacy/` folder should not be introduced too early. The current PHP, HTML, CSS and JavaScript files should remain in place until routing and asset compatibility are fully controlled.

## Phase A - Stabilization and Documentation

Purpose: define the baseline before changing behavior.

Deliverables:

- Architecture audit.
- Route and flow mapping.
- Backend mapping.
- Frontend mapping.
- Database mapping.
- Migration plan.
- Initial FastAPI scaffold.

Completed so far:

- Dedicated branch created.
- Migration documentation added.
- FastAPI backend scaffold added.
- Backend health checks added.
- Basic backend tests added.

Exit criteria:

- Documentation exists in English.
- The legacy app remains untouched.
- The new backend scaffold is isolated.
- Tests pass.

## Phase B - FastAPI Backend Compatibility

Purpose: reproduce the legacy backend behavior behind a clean FastAPI architecture.

Order:

1. Configuration and application factory.
2. Database connection setup.
3. Read-only public data endpoints.
4. Auth status and logout compatibility.
5. Public news.
6. hCaptcha site key and public submissions.
7. Admin record management.
8. Admin catalog management.
9. Pending submission review.
10. Maintenance mode.
11. API-key records endpoint.
12. Admin operations.

Compatibility strategy:

- Add clean `/api/v1/...` routes.
- Add or proxy legacy-compatible routes where needed.
- Keep PHP active until equivalent FastAPI behavior is verified.

Testing strategy:

- Unit tests for services and pure rules.
- Contract tests for JSON response shapes.
- Auth token tests.
- hCaptcha tests with mocks.
- Repository tests with a controlled database or query-level fixtures.

Exit criteria:

- Public read-only endpoints match legacy output.
- Sensitive mutations are covered by tests.
- Admin behavior is reproduced before any UI replacement.

## Phase C - React Frontend Migration

Purpose: rebuild the current UI in React, Vite and TypeScript without visual changes.

Order:

1. Scaffold Vite React TypeScript.
2. Add React Router.
3. Add TanStack Query.
4. Preserve existing asset paths.
5. Import legacy CSS.
6. Recreate the public shell.
7. Port auth controls, dark mode and mobile menu behavior.
8. Port read-only views.
9. Port records filters, sorting, sharing and CSV export.
10. Port stats.
11. Port public submission and news modals.
12. Port privacy and maintenance pages.
13. Port admin UI last.

Testing strategy:

- TypeScript checks.
- Unit tests for filters and calculations.
- Playwright screenshots for desktop and mobile.
- Manual comparison against legacy where needed.

Exit criteria:

- The React UI visually matches the legacy UI.
- Legacy deep links still work.
- Public flows are unchanged.

## Phase D - Controlled Cutover

Purpose: connect React to FastAPI and retire legacy code only after verification.

Steps:

1. Configure local proxy/dev routing.
2. Compare PHP and FastAPI endpoint responses.
3. Compare legacy and React screenshots.
4. Run public and admin workflows.
5. Keep a rollback path.
6. Switch public frontend only after verification.
7. Switch admin only after all admin flows are covered.
8. Remove legacy code only when no route or asset depends on it.

## Recommended Commit Sequence

1. `docs: add existing architecture migration audit`
2. `feat: bootstrap FastAPI backend structure`
3. `docs: translate migration documentation and update readme`
4. `feat: add FastAPI database configuration`
5. `feat: port public read-only data endpoints`
6. `feat: add auth compatibility endpoints`
7. `feat: port public submissions and news endpoints`
8. `feat: port admin record endpoints`
9. `chore: scaffold React Vite TypeScript frontend`
10. `refactor: port public shell with legacy styles`
11. `feat: port public data views with TanStack Query`
12. `feat: port records filters and stats views`
13. `feat: connect React frontend to FastAPI`
14. `docs: finalize migration runbook`

## Major Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Production PostgreSQL differs from snapshots | Data bugs | Inspect production schema before migrations |
| UI is string-built in legacy JS | Visual differences | Preserve CSS and compare screenshots |
| Auth depends on external OAuth | Local testing gaps | Use signed token fixtures |
| hCaptcha is external | Flaky tests | Mock the verification service |
| Admin is large and sensitive | Regression risk | Migrate admin last |
| PostgreSQL backups are not implemented | Operational confusion | Keep current unsupported responses first |
| Encoding issues | Text regressions | Verify in browser before changing copy |

## Non-Regression Checklist

Backend:

- `load_data` fields match legacy output.
- Auth returns `logged`, `allowed`, `id`, `username`.
- Maintenance returns HTTP 503 as before.
- Public submissions keep hCaptcha, honeypot and rate-limit rules.
- Admin approval replaces the map/vehicle record.
- Tuning setup duplicates are rejected.
- API-key records filters still work.

Frontend:

- Header and buttons match.
- Tables match.
- Filters and sorting match.
- Stats match.
- Dark mode works.
- Modals work.
- Icons and flags load.
- Deep links work.
- CSV export matches.

## Current Decision

The next safe implementation step is to migrate the read-only public data endpoints into FastAPI while keeping all PHP endpoints available.
