# UI Parity Check

## Scope

This pass focused on faithfully porting the visible legacy UI into React, without redesigning the product.

Covered areas:

- Public shell: header, navigation, auth buttons, news button, submit button, dark mode toggle, footer.
- Public home page: legacy sections, text order, image, guidelines, stats/news/follow sections.
- Public data views: maps, vehicles, players, tuning parts, tuning setups, records.
- Records UI: legacy filter rows, multi-dropdown filters, distance filters, status filters, CSV export, note modal, share button.
- Secondary pages: privacy and maintenance as standalone pages.
- Stats page: detailed legacy-style sections, tables, bar charts, country pie area, tuning stats, overall stats.
- Admin page: legacy standalone layout, topbar, sequential form containers, pending submissions, news, database/backup area, maintenance controls.

## Corrected Differences

- Replaced the simplified React shell with the legacy header/footer structure and ids.
- Restored the legacy home page content and section order.
- Replaced simplified records filters with the legacy filter layout and visible controls.
- Restored legacy modal ids, close buttons, titles, and action areas.
- Moved privacy and maintenance outside the public shell to match the standalone legacy pages.
- Reworked stats from four summary cards into the legacy detailed statistics layout.
- Reworked the React admin page to match the legacy standalone form-container layout.
- Fixed React runtime warnings from invalid legacy HTML nesting while preserving the same visible layout.
- Fixed public records row keys for PostgreSQL lowercase `idrecord` responses.
- Updated smoke checks to validate standalone pages and formatted distances correctly.

## Remaining Notes

- The admin "Database & Backups" block now supports backup create/list/download/delete and integrity checks through FastAPI.
- SQL import and restore remain visibly disabled because they are destructive PostgreSQL operations.
- Public hCaptcha markup keeps the legacy ids and now loads the configured site key; real submission still depends on the external hCaptcha service.
- This pass used runtime smoke checks and DOM/text verification. Pixel-level screenshot diffing was not added.

## Verified

- `npm run build` in `frontend`
- `python -m pytest` in `backend`
- `node scripts/dev/test_system_smoke.mjs` against the local FastAPI/Vite/PostgreSQL stack
