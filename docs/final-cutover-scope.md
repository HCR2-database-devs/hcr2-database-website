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

## Not Migrated As Browser Admin Features

- PostgreSQL database download.
- PostgreSQL backup creation.
- PostgreSQL restore.
- SQL import from the admin UI.

## Reason

The PHP admin endpoint already reported PostgreSQL backup, restore and import as unsupported.

For PostgreSQL, these tasks should be handled with operational tools such as `pg_dump`, `pg_restore`, managed database backups, or CI/deployment jobs.

## Impact

The product workflows no longer need the PHP stack.

Database operations still need external operational tooling before production runbooks are complete.
