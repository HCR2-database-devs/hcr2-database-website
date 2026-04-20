# Blocking Items

Date: 2026-04-20

This document lists what still blocks real end-to-end validation and final migration.

## Critical Blockers

### No React Frontend Exists

Impact:

- Frontend install, build, lint and type-check cannot be executed.
- Public UI migration cannot be compared against legacy.
- Front/back integration cannot be tested.

Needed:

- `frontend/` scaffold with Vite, React and TypeScript.
- `package.json` scripts.
- React Router.
- TanStack Query.
- Asset serving strategy.
- Legacy CSS import.

### No FastAPI Business Endpoints Exist Yet

Impact:

- The new backend does not replace any legacy product behavior.
- The frontend cannot consume migrated data.
- Contract comparison is limited to documentation and legacy code inspection.

Needed:

- Public read-only endpoints first.
- Legacy-compatible response schemas.
- Repository and service layers.
- Contract tests.

### No Local Database Configuration

Impact:

- Legacy endpoints cannot be tested at runtime.
- FastAPI repositories cannot be integration-tested.
- Production schema assumptions cannot be verified.

Needed:

- A local `.env` with PostgreSQL credentials, or
- a Docker-based PostgreSQL dev database, plus
- schema migration or seed scripts, plus
- representative test data.

### Production PostgreSQL Schema Is Not Verified

Impact:

- SQLite snapshots differ from the current PHP table names and expected fields.
- Porting SQL without schema verification risks subtle data bugs.

Needed:

- Production schema dump or safe read-only schema inspection.
- Confirmation of `_worldrecord.idRecord`.
- Confirmation of `_worldrecord.questionable_reason`.
- Index and constraint review.

### External Auth Is Not Locally Reproducible End-to-End

Impact:

- The login button depends on `https://auth.hcr2.xyz/login`.
- Admin flows cannot be manually tested without a valid `WC_TOKEN`.

Needed:

- A documented local admin token generation method, or
- a development auth bypass that is explicitly disabled outside development, or
- a test-only signed token fixture for API tests.

### hCaptcha Is Not Locally Testable End-to-End

Impact:

- Public submissions cannot be fully validated locally.

Needed:

- Development hCaptcha keys, or
- mocked hCaptcha verification for automated tests, plus
- clear environment documentation.

## Important Non-Blocking Gaps

### No Docker or Compose Setup

Impact:

- Local onboarding remains manual.
- Database-dependent tests are harder to reproduce.

Needed later:

- `docker-compose.yml` for PostgreSQL.
- Optional backend service.
- Optional frontend service after React scaffold exists.

### No Seed or Fixture Script

Impact:

- Contract tests cannot compare stable records without a known dataset.

Needed later:

- Seed script based on sanitized data.
- Test fixture loader.
- Clear reset instructions.

### No Visual Regression Workflow

Impact:

- React migration cannot prove visual parity.

Needed later:

- Playwright setup.
- Legacy screenshot baseline.
- React screenshot comparison.
- Desktop and mobile viewports.

### Legacy Backup Behavior Is Operationally Incomplete

Impact:

- Admin UI exposes backup/import/restore controls, but PostgreSQL support is intentionally incomplete.

Needed later:

- Decide whether to keep unsupported responses, hide disabled controls, or implement proper PostgreSQL backup operations.
- This should be treated as an ops decision, not a silent migration change.

## What the Project Owner Must Provide for Full Validation

To complete realistic end-to-end validation, the project needs:

1. PostgreSQL connection settings for a safe local or staging database.
2. A confirmed production schema or read-only schema dump.
3. Safe test data or a seed dataset.
4. `AUTH_SHARED_SECRET` for generating local `WC_TOKEN` test cookies, or a dedicated development auth plan.
5. hCaptcha development credentials or approval to use mocked verification in local tests.
6. Clarification on PostgreSQL backup/import/restore expectations.

## Current Recommendation

Do not remove any legacy code yet.

The next implementation phase should focus on read-only FastAPI endpoints and tests. This provides the safest path because it does not mutate production data and gives the future React frontend stable contracts to consume.
