# Git History Cleanup Plan

Date: 2026-04-20
Branch: `refactor/fastapi-react-migration`

This document records the third-pass audit for files that should not remain tracked, and the separate list of files that may require a coordinated Git history rewrite.

## Audit Summary

The audit checked:

- currently tracked files,
- suspicious filenames in the full Git history,
- common secret/config/cache/build patterns,
- tracked file sizes,
- SQLite snapshot schemas without exposing row contents.

No committed `.env` file or private key was found. Environment example files contain empty placeholders only.

The main finding is that database snapshots are present in the repository and in history. The current snapshots include `PendingSubmission.submitterIp` and user-submitted names/countries, so they should be treated as sensitive operational data rather than source code.

## Files To Stop Tracking Now

These files are currently tracked and should be removed from the Git index while remaining available locally if needed:

| Path | Reason | Criticality |
| --- | --- | --- |
| `backups/main-20260326-023356.sqlite` | Historical database snapshot; includes pending submissions and submitter IP column. | High |
| `backups/main-20260403-073123.sqlite` | Historical database snapshot; includes pending submissions and submitter IP column. | High |

Recommended current cleanup:

```powershell
git rm --cached backups/main-20260326-023356.sqlite backups/main-20260403-073123.sqlite
```

The files should also be covered by `.gitignore` so new local snapshots are not accidentally recommitted.

## Files To Purge From Git History

These paths appear in Git history and are candidates for a full history rewrite:

| Path or pattern | Reason | Criticality |
| --- | --- | --- |
| `main.sqlite` | Historical database file present across many commits. | High |
| `main.sqlite.backup` | Historical backup copy. | High |
| `backups/main-*.sqlite` | Historical database snapshots, including current tracked files and older removed snapshots. | High |

Observed historical paths:

- `main.sqlite`
- `main.sqlite.backup`
- `backups/main-20260101-121739.sqlite`
- `backups/main-20260101-165619.sqlite`
- `backups/main-20260326-023356.sqlite`
- `backups/main-20260403-073123.sqlite`

## Current Tracking Ignore Rules

The `.gitignore` should cover:

- local `.env` variants while keeping `.env.example` files,
- Python virtualenvs and caches,
- frontend dependency/build output,
- local database snapshots and data exports,
- logs and temporary backup artifacts.

## History Rewrite Impact

Purging files from history is disruptive:

- commit hashes change,
- open branches based on old commits need to be rebased or recreated,
- collaborators must reclone or carefully reset,
- any existing pull requests may need to be recreated,
- force-pushing rewritten refs is required,
- GitHub may keep unreachable objects for some time until garbage collection.

Because of this, the current branch should not rewrite history automatically without explicit coordination. The safe path is to first stop tracking the files now, then schedule the history rewrite when collaborators and deployment refs can be managed.

## Proposed History Purge Procedure

Recommended tool: `git filter-repo`.

Preparation:

```powershell
git status --short
git branch backup/pre-history-cleanup
```

Rewrite command:

```powershell
git filter-repo --invert-paths --path main.sqlite --path main.sqlite.backup --path-glob "backups/*.sqlite"
```

Verification:

```powershell
git log --all -- main.sqlite main.sqlite.backup backups
git log --all --name-only --pretty=format: | Select-String -Pattern "main.sqlite|backups/.*\\.sqlite"
```

Expected verification result: no matching paths remain in history.

Remote update, after owner approval:

```powershell
git push --force-with-lease --all
git push --force-with-lease --tags
```

Post-rewrite actions:

- ask every collaborator to reclone or reset to the rewritten branch,
- invalidate any local copies of the database snapshots,
- keep only sanitized seed data in future commits,
- document a safe fixture/seed strategy before database-backed tests are added.

## Decision For This Pass

Execute current-index cleanup and `.gitignore` hardening now.

Do not rewrite history in this pass unless the repository owner explicitly approves the force-push workflow and collaborator impact.
