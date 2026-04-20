# 03 - Migration Roadmap

Date: 2026-04-20

This document tracks what is complete, what is missing, and the intended implementation order.

## Done

Documentation:

- Current-state baseline.
- Target architecture.
- Roadmap.
- Test and blocker summary.
- Git history cleanup plan.

Git hygiene:

- SQLite snapshots removed from the current Git index.
- `.gitignore` hardened for local database snapshots, `.env.*`, frontend dependencies and build output.
- history rewrite procedure documented but not executed.

Backend:

- FastAPI app factory.
- `/health`.
- `/api/v1/health`.
- Pydantic settings.
- environment list parsing.
- PostgreSQL DSN construction.
- PostgreSQL connection helper.
- `WC_TOKEN` verification helper.
- admin allowlist helper.
- public read-only repositories.
- public read-only services.
- Pydantic schemas for public data, news, auth and hCaptcha.
- clean public data endpoints.
- legacy `load_data.php` compatibility endpoint.
- auth status/logout compatibility routes.
- news and hCaptcha site key routes.
- backend tests for health, config, security, service dispatch and route wiring.

Frontend:

- Vite + React + TypeScript scaffold.
- React Router.
- TanStack Query.
- frontend API client.
- auth status polling.
- dark mode state using the legacy `data-theme` contract.
- copied legacy CSS and assets under `frontend/public/`.
- initial public shell and public data views.
- production build.

Legacy preservation:

- legacy PHP/HTML/CSS/JS files remain in place.
- legacy assets remain in place.

## Missing

Backend:

- public submission route,
- admin routes,
- maintenance routes,
- API-key records route,
- database-backed tests.

Frontend:

- records filters and export,
- public submission,
- full news modal behavior,
- admin UI.

Operations:

- Docker/compose setup,
- seed/test database setup,
- local auth token workflow,
- local hCaptcha testing strategy,
- visual regression setup.

## Phase 1 - Documentation Consolidation

Status: done.

Tasks:

- replace overlapping migration documents with four numbered runbooks,
- add Git history cleanup plan,
- update README links,
- keep project documentation English-only.

## Phase 2 - Git Tracking and History Hygiene

Tasks:

- audit tracked files for secrets, dumps, caches and local-only artifacts,
- update `.gitignore`,
- untrack current local-only files when safe,
- document files that may require history rewrite,
- do not rewrite history without explicit, coordinated approval.

Status: current-index cleanup done; history rewrite not executed.

## Phase 3 - FastAPI Read-Only Backend

Status: route wiring done; live PostgreSQL validation pending.

Priority order:

1. database session and query helper,
2. Pydantic schemas,
3. public repositories,
4. public services,
5. `/api/v1/maps`,
6. `/api/v1/vehicles`,
7. `/api/v1/players`,
8. `/api/v1/tuning-parts`,
9. `/api/v1/tuning-setups`,
10. `/api/v1/records`,
11. `/php/load_data.php?type=...` compatibility route,
12. contract tests with mocked repository outputs or fixture data.

Non-goals for this phase:

- no admin mutations,
- no public submissions,
- no schema changes,
- no legacy route removal.

## Phase 4 - FastAPI Low-Risk Public Utilities

Status: route wiring done; live PostgreSQL and real-cookie validation pending.

Priority order:

1. `/auth/status.php` compatibility route,
2. `/auth/logout.php` compatibility route,
3. clean `/api/v1/auth/status`,
4. clean `/api/v1/auth/logout`,
5. `/php/get_news.php`,
6. `/php/get_hcaptcha_sitekey.php`,
7. clean news and hCaptcha routes.

## Phase 5 - React/Vite Frontend Scaffold

Status: initial scaffold done; visual parity and full behavior are pending.

Tasks:

- create `frontend/`,
- add React, Vite and TypeScript,
- add React Router,
- add TanStack Query,
- configure dev proxy,
- expose or copy legacy assets without changing `/img/...` paths,
- import legacy CSS,
- port public shell, header, footer and navigation.

## Phase 6 - React Public Views

Status: initial public data views exist; full legacy behavior is pending.

Priority order:

1. auth status controls,
2. dark mode,
3. mobile menu behavior,
4. maps view,
5. vehicles view,
6. tuning parts view,
7. players view,
8. records view,
9. records filters and sorting,
10. CSV export,
11. stats,
12. public submission modal,
13. news modal,
14. note modal,
15. privacy and maintenance routes.

## Phase 7 - Admin Migration

Admin should be migrated after public read-only and public UI are stable.

Priority order:

1. admin auth dependency,
2. admin records endpoints,
3. admin catalog endpoints,
4. pending submission endpoints,
5. admin news endpoint,
6. maintenance admin endpoint,
7. admin operations endpoint,
8. React admin page.

## Progress Checklist

Backend read-only:

- [ ] database session implemented
- [ ] schemas implemented
- [ ] repositories implemented
- [ ] services implemented
- [ ] maps endpoint
- [ ] vehicles endpoint
- [ ] players endpoint
- [ ] tuning parts endpoint
- [ ] tuning setups endpoint
- [ ] records endpoint
- [ ] `load_data.php` compatibility endpoint
- [ ] tests for response contracts

Frontend:

- [ ] Vite scaffold
- [ ] TypeScript config
- [ ] Router
- [ ] TanStack Query
- [ ] API client
- [ ] legacy CSS import
- [ ] public shell
- [ ] public data views
- [ ] records filters
- [ ] stats
- [ ] modals
- [ ] visual checks

Cleanup:

- [ ] sensitive tracked files audited
- [ ] `.gitignore` hardened
- [ ] current tracking cleanup done
- [ ] history cleanup plan documented
- [ ] history rewrite decision made separately
