# Admin

Admin access is controlled by the `WC_TOKEN` cookie.

The backend verifies the token with `AUTH_SHARED_SECRET` and checks the Discord id against `ALLOWED_DISCORD_IDS`.

## Local Admin Access

Generate a development token:

```powershell
.\scripts\dev\make-dev-wc-token.ps1
```

Set the printed `WC_TOKEN` cookie for `127.0.0.1`, then open:

```text
http://127.0.0.1:5173/admin
```

## Available Workflows

The React admin page supports:

- submit or replace a record
- delete a record
- mark records as verified or questionable
- assign a tuning setup to a record without one
- add vehicles
- add maps
- add tuning parts
- add tuning setups
- list pending public submissions
- approve or reject pending submissions
- post news
- enable or disable maintenance mode
- run a DB integrity check
- create, list, download and delete application SQL backups

## Operational Note

PostgreSQL restore and arbitrary SQL import are not implemented as in-app admin actions. Use reviewed database tooling such as `pg_restore` and deployment-level backups for destructive operations.
