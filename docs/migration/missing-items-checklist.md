# Missing Items Checklist

Date: 2026-04-20

This checklist tracks gaps found during the second-pass migration audit.

## Backend Routes

| Legacy route | Migrated route exists | Status |
| --- | --- | --- |
| `/php/load_data.php?type=maps` | No | Missing |
| `/php/load_data.php?type=vehicles` | No | Missing |
| `/php/load_data.php?type=players` | No | Missing |
| `/php/load_data.php?type=tuning_parts` | No | Missing |
| `/php/load_data.php?type=tuning_setups` | No | Missing |
| `/php/load_data.php?type=records` | No | Missing |
| `/php/api_records.php` | No | Missing |
| `/auth/status.php` | No | Missing |
| `/auth/logout.php` | No | Missing |
| `/php/get_hcaptcha_sitekey.php` | No | Missing |
| `/php/public_submit.php` | No | Missing |
| `/php/get_news.php` | No | Missing |
| `/auth/post_news.php` | No | Missing |
| `/php/submit_record.php` | No | Missing |
| `/php/delete_record.php` | No | Missing |
| `/php/set_questionable.php` | No | Missing |
| `/php/assign_setup.php` | No | Missing |
| `/php/add_vehicle.php` | No | Missing |
| `/php/add_map.php` | No | Missing |
| `/php/add_tuning_part.php` | No | Missing |
| `/php/add_tuning_setup.php` | No | Missing |
| `/auth/admin_pending.php` | No | Missing |
| `/auth/admin_actions.php` | No | Missing |
| `/php/maintenance_status.php` | No | Missing |
| `/php/set_maintenance.php` | No | Missing |

## Backend Modules

| Area | Status |
| --- | --- |
| Settings | Present |
| Health routes | Present |
| Auth token helper | Present but not wired to routes |
| Admin auth dependency | Missing |
| Database connection lifecycle | Missing |
| Public repositories | Missing |
| Admin repositories | Missing |
| Pydantic schemas | Missing |
| Business services | Missing |
| hCaptcha service | Missing |
| Maintenance service | Missing |
| Error handling compatibility | Partial |
| API-key dependency | Missing |

## Frontend Public UI

| Legacy feature | React migration status |
| --- | --- |
| Public shell/header/footer | Missing |
| Public navigation buttons | Missing |
| Auth controls | Missing |
| Dark mode toggle | Missing |
| Mobile menu | Missing |
| About/guidelines sections | Missing |
| Maps view | Missing |
| Vehicles view | Missing |
| Players view | Missing |
| Tuning parts view | Missing |
| Records view | Missing |
| Records filters | Missing |
| Records sorting | Missing |
| CSV export | Missing |
| Share links/deep links | Missing |
| Stats view | Missing |
| Public submission modal | Missing |
| hCaptcha widget integration | Missing |
| News modal | Missing |
| Note modal | Missing |
| Privacy route | Missing |
| Maintenance route | Missing |

## Frontend Admin UI

| Legacy admin feature | React migration status |
| --- | --- |
| Admin access guard | Missing |
| Submit/replace record form | Missing |
| Delete record form | Missing |
| Questionable status form | Missing |
| Assign tuning setup form | Missing |
| Add vehicle form | Missing |
| Add map form | Missing |
| Add tuning part form | Missing |
| Add tuning setup form | Missing |
| Pending submissions list | Missing |
| Approve/reject submission actions | Missing |
| News posting form | Missing |
| Backup list/delete actions | Missing |
| Integrity check action | Missing |
| Maintenance controls | Missing |

## Assets

| Asset group | Status |
| --- | --- |
| Root public images | Present in legacy `img/` |
| Map SVG icons | Present for latest SQLite snapshot |
| Vehicle SVG icons | Present for latest SQLite snapshot |
| Tuning part SVG icons | Present for latest SQLite snapshot |
| React public asset copy/serving strategy | Missing |
| Asset checks against live PostgreSQL data | Not executable yet |

## Styles

| Style area | Status |
| --- | --- |
| Legacy `css/style.css` | Present |
| Legacy dark-mode rules | Present in `style.css` |
| React style import | Missing |
| Visual regression screenshots | Missing |
| CSS extraction plan | Documented but not executed |

## Environment and Runtime

| Item | Status |
| --- | --- |
| Root `.env.example` | Updated |
| Backend `.env.example` | Present |
| Real `.env` | Missing locally |
| PostgreSQL connection settings | Missing locally |
| Discord auth secret | Missing locally |
| hCaptcha keys | Missing locally |
| Frontend package scripts | Missing |
| Backend package config | Present |
| Docker or compose file | Missing |
| Seed/test database script | Missing |
| One-command local startup script | Missing |

## Tests

| Test area | Status |
| --- | --- |
| Backend unit tests | Present and passing |
| Backend lint | Present and passing |
| Backend startup smoke test | Passing |
| PHP syntax lint | Passing |
| JS syntax check | Passing |
| Frontend install/build/type-check | Not executable |
| Database integration tests | Not executable |
| Legacy runtime test | Not executable without `.env` and database |
| End-to-end tests | Missing |

## High-Priority Missing Items

1. Implement FastAPI database connection and repositories.
2. Port public read-only endpoints with legacy-compatible JSON.
3. Add contract tests for public endpoints.
4. Add auth dependencies and status/logout routes.
5. Add public news and hCaptcha site key routes.
6. Add public submission route with hCaptcha mockability.
7. Scaffold React/Vite/TypeScript frontend after backend read-only contracts are stable.
8. Keep admin migration for a later, dedicated phase.
