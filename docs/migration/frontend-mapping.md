# Frontend Mapping

Date: 2026-04-20

This document maps the legacy public and admin frontend to the target React, Vite and TypeScript architecture.

## Current Frontend

Files:

- `index.html`: public page shell and modals.
- `js/script.js`: public behavior and rendering.
- `css/style.css`: primary styling, responsive rules and dark mode.
- `css/style_dark_mode.css`: existing alternate stylesheet, not currently referenced by `index.html`.
- `php/admin.php`: admin HTML/CSS/JavaScript rendered by PHP.
- `privacy.html`: static page.
- `maintenance.html`: static page.

There is currently no frontend build system, no component model, no client-side routing and no TypeScript.

## Target Frontend Structure

```text
frontend/
|-- index.html
|-- package.json
|-- tsconfig.json
|-- vite.config.ts
|-- src/
|   |-- app/
|   |   |-- App.tsx
|   |   |-- router.tsx
|   |   `-- queryClient.ts
|   |-- pages/
|   |-- components/
|   |-- features/
|   |-- services/
|   |-- hooks/
|   |-- lib/
|   |-- types/
|   |-- assets/
|   `-- styles/
`-- tests/
```

Initial rule: import the legacy CSS first and preserve existing class names until the React output is visually verified.

## Public Home Page

Legacy source: `index.html`

Current elements:

- Header gradient.
- Logo and title.
- Public navigation buttons.
- Discord login.
- Admin and logout controls.
- Dark mode toggle.
- Auth warning.
- Dynamic data and stats containers.
- About and guideline sections.
- Public submission modal.
- News modal.
- Record note modal.
- Footer with GitHub version and privacy link.

React target:

- `pages/PublicHomePage.tsx`
- `components/layout/Header.tsx`
- `components/layout/Footer.tsx`
- `features/auth/AuthControls.tsx`
- `features/theme/DarkModeToggle.tsx`
- `features/data/PublicDataView.tsx`

## Public Data Views

Legacy behavior:

- Buttons call `fetchData(type)`.
- `php/load_data.php?type=...` returns JSON.
- `displayData()` renders tables through string-built HTML.

React target:

- TanStack Query for data fetching.
- TypeScript types for every response shape.
- Dedicated components per view:
  - maps
  - vehicles
  - players
  - tuning parts
  - records

Routing decision:

- Keep legacy query parameters such as `?view=records` at first.
- React Router may also provide clean routes later, but legacy links must remain valid.

## Records View

Current columns:

- Distance
- Status
- Notes
- Map Name
- Vehicle Name
- Tuning Parts
- Player Name
- Player Country
- Share

Current filters:

- text search across player, map, vehicle and notes
- map selection
- vehicle selection
- tuning part selection, requiring every selected part
- distance greater-than-or-equal or less-than-or-equal
- only questionable
- only verified

Current sorting:

- default map and vehicle order
- distance ascending
- distance descending
- newest by `idRecord`

React target:

- `features/records/RecordsTable.tsx`
- `features/records/RecordsFilters.tsx`
- `features/records/recordFilters.ts`
- `features/records/exportRecordsCsv.ts`

These functions should be testable without the DOM.

## Stats View

Legacy source: `displayStats()` and `updateVehicleStats()` in `js/script.js`.

Current sections:

- Vehicle statistics.
- Vehicle rankings by adventure stars.
- Top 10 players by record count.
- Records by country.
- Map statistics.
- Map rankings by adventure stars.
- Tuning part statistics.
- Overall statistics.

Current business rules:

- Special maps:
  - `Forest Trials`
  - `Intense City`
  - `Raging Winter`
- Special map stars:
  - `distance >= 5000` gives `15000`
  - otherwise `distance * 3`
- Other map stars:
  - `distance >= 10000` gives `10000`
  - otherwise `distance`
- Countries with count `<= 5` are grouped under `Other countries`.

React target:

- `features/stats/StatsView.tsx`
- `features/stats/statsCalculations.ts`
- unit tests for all calculations.

## Players View

Legacy behavior:

- Players are loaded from `type=players`.
- Records are loaded separately to compute each player's current record count.
- Filters:
  - text search by player or country
  - country selection
  - record count greater-than-or-equal or less-than-or-equal

React target:

- `features/players/PlayersView.tsx`
- `features/players/playerFilters.ts`
- TanStack queries for players and records.

## Public Submission Modal

Legacy behavior:

- Loads maps, vehicles and tuning parts.
- Loads hCaptcha site key.
- Renders hCaptcha.
- Validates required fields, positive distance, 3 or 4 tuning parts and hCaptcha response.
- Sends honeypot fields and timing fields to the backend.

React target:

- `features/submissions/PublicSubmissionModal.tsx`
- `services/submissionsApi.ts`
- TanStack mutation.

The hCaptcha integration must remain behavior-compatible.

## News Modal

Legacy behavior:

- Fetches `/php/get_news.php`.
- Renders title, content, author and date.
- Marks news as read in local storage.

React target:

- `features/news/NewsModal.tsx`
- `services/newsApi.ts`
- `useNewsQuery`.

## Authentication Controls

Legacy behavior:

- Poll `/auth/status.php` on load.
- Retry after one second.
- Poll every 30 seconds.
- Login goes to `https://auth.hcr2.xyz/login`.
- Logout goes to `auth/logout.php`.
- Admin goes to `php/admin.php`.

React target:

- `features/auth/useAuthStatus.ts`
- TanStack Query with `refetchInterval: 30000`.
- Keep legacy URLs until the new admin area is ready.

## Admin UI

Legacy source: `php/admin.php`

Migration order:

1. Keep the PHP admin page during the early backend migration.
2. Port admin APIs to FastAPI with contract tests.
3. Build a React admin page only after the APIs are stable.
4. Compare every admin workflow before removing the PHP page.

React target:

- `pages/AdminPage.tsx`
- `features/admin/records`
- `features/admin/catalog`
- `features/admin/submissions`
- `features/admin/news`
- `features/admin/maintenance`
- `features/admin/operations`

## Assets and Static Paths

Paths to preserve:

- `/img/hcrdatabaselogo.png`
- `/img/Discord-Symbol-Blurple.png`
- `/img/map_icons/*.svg`
- `/img/vehicle_icons/*.svg`
- `/img/tuning_parts_icons/*.svg`
- `/img/maintenanceon.png`
- favicons and manifest under `/img/`

Vite should serve these paths without forcing immediate markup changes.

## Styles

Primary source: `css/style.css`

Important areas:

- Header and navigation.
- Mobile menu.
- Buttons.
- Tables.
- Modals.
- Form containers.
- Record filters and dropdowns.
- Stats blocks and charts.
- Public records responsive table.
- Dark mode via `[data-theme="dark"]`.

Migration rule:

- Import the CSS as legacy CSS first.
- Preserve class names and DOM structure where needed.
- Extract styles only after screenshot comparison.

## TypeScript Types

Initial domain types:

```ts
export interface MapItem {
  idMap: number;
  nameMap: string;
}

export interface VehicleItem {
  idVehicle: number;
  nameVehicle: string;
}

export interface PlayerItem {
  idPlayer: number;
  namePlayer: string;
  country?: string | null;
}

export interface TuningPart {
  idTuningPart: number;
  nameTuningPart: string;
}

export interface TuningSetup {
  idTuningSetup: number;
  parts: Array<{ nameTuningPart: string }>;
}

export interface RecordItem {
  idRecord: number;
  distance: number;
  current: number;
  idTuningSetup?: number | null;
  questionable: number;
  questionable_reason?: string;
  map_name: string;
  vehicle_name: string;
  player_name: string;
  player_country?: string | null;
  tuning_parts?: string | null;
}
```

## Frontend Migration Order

1. Scaffold Vite React TypeScript.
2. Copy or expose legacy assets at the same public paths.
3. Import legacy CSS.
4. Recreate the public shell.
5. Add auth status, dark mode and mobile menu behavior.
6. Port maps, vehicles and tuning parts views.
7. Port players view.
8. Port records view with filters, sorting and CSV export.
9. Port stats calculations and UI.
10. Port public submission and news modals.
11. Port privacy and maintenance pages.
12. Port admin UI last.

## Visual Non-Regression Checks

For every migrated screen:

- Compare legacy and React screenshots on desktop.
- Compare legacy and React screenshots on mobile.
- Verify dark mode.
- Verify text does not overlap.
- Verify icons and flags load.
- Verify modals.
- Verify filters and sorting.
- Verify existing labels and copy.
