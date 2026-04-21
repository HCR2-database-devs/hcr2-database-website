# Final Cutover Scope

## Migrated

- Public data browsing.
- Records search, filters, sorting and CSV export.
- News display.
- Public submission validation path.
- Auth status and logout.
- Admin record workflows.
- Admin catalog workflows.
- Pending submission approval and rejection.
- News posting.
- Maintenance controls.
- DB integrity check.
- DB backup create/list/download/delete.
- Admin SVG icon upload for maps, vehicles and tuning parts.

## Not Migrated As Browser Admin Features

- PostgreSQL restore.
- SQL import from the admin UI.

## Reason

Restore and SQL import are destructive PostgreSQL operations.

They should be handled with reviewed operational tooling such as `pg_restore`, managed database backups, or deployment jobs.

## Impact

The product workflows no longer need the PHP stack.

Backup creation/list/download/delete are available in the React admin.

Restore/import still need external operational tooling before production runbooks are complete.
