# Test Status

Date: 2026-04-20

This document records what was actually executed during the second-pass audit.

## Executed Tests and Checks

### Git Branch and Workspace

Command:

```powershell
git status --short --branch
```

Result:

- Branch: `refactor/fastapi-react-migration`
- Workspace was clean before second-pass edits.

Status: Passed

### Backend Unit Tests

Command:

```powershell
.\.venv\Scripts\python -m pytest
```

Working directory:

```text
backend
```

Result:

```text
collected 9 items
tests\test_config.py ...
tests\test_health.py ..
tests\test_security.py ....
9 passed
```

Status: Passed

### Backend Lint

Command:

```powershell
.\.venv\Scripts\python -m ruff check .
```

Working directory:

```text
backend
```

Result:

```text
All checks passed!
```

Status: Passed

### FastAPI Import and Route Listing

Command:

```powershell
@'
from app.main import create_app
app = create_app()
print(app.title)
print('\n'.join(sorted(route.path for route in app.routes if hasattr(route, 'path'))))
'@ | .\.venv\Scripts\python -
```

Working directory:

```text
backend
```

Result:

```text
HCR2 Records API
/api/v1/health
/docs
/docs/oauth2-redirect
/health
/openapi.json
/redoc
```

Status: Passed

### FastAPI Startup Smoke Test

Command:

```powershell
$process = Start-Process -FilePath '.\.venv\Scripts\python.exe' -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8123') -WorkingDirectory (Get-Location) -PassThru -WindowStyle Hidden
try {
  Start-Sleep -Seconds 3
  $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8123/health' -UseBasicParsing -TimeoutSec 10
  Write-Output "STATUS=$($response.StatusCode)"
  Write-Output $response.Content
} finally {
  if ($process -and -not $process.HasExited) {
    Stop-Process -Id $process.Id -Force
    $process.WaitForExit()
  }
}
```

Working directory:

```text
backend
```

Result:

```text
STATUS=200
{"status":"ok","service":"HCR2 Records API","version":"0.1.0"}
```

Status: Passed

### PHP Syntax Validation

Command:

```powershell
Get-ChildItem -Recurse -File -Filter *.php | ForEach-Object { php -l $_.FullName }
```

Result:

- All PHP files reported `No syntax errors detected`.

Status: Passed

### Legacy JavaScript Syntax Check

Command:

```powershell
node --check js\script.js
```

Result:

- No syntax error output.

Status: Passed

### Asset Coverage Against Latest SQLite Snapshot

Command:

```powershell
python <snapshot/icon comparison script>
```

Compared:

- `backups/main-20260403-073123.sqlite`
- `img/map_icons`
- `img/vehicle_icons`
- `img/tuning_parts_icons`

Result:

```text
Map: database_names=22 svg_files=22 missing=0 extra=0
Vehicle: database_names=34 svg_files=34 missing=0 extra=0
TuningPart: database_names=19 svg_files=19 missing=0 extra=0
```

Status: Passed for the historical SQLite snapshot.

### SQLite Snapshot Readability

Command:

```powershell
python <table count script>
```

Result:

```text
Map=22
Vehicle=34
Player=247
TuningPart=19
TuningSetup=172
TuningSetupParts=650
WorldRecord=753
PendingSubmission=241
News=32
```

Status: Passed

## Checks That Failed or Were Corrected

### Python Heredoc Attempt

An initial Python import command used Bash-style heredoc syntax, which PowerShell rejected. The check was rerun with PowerShell-compatible syntax and passed.

This was a shell invocation issue only, not an application failure.

## Tests Not Executable Yet

### Frontend Install

Command attempted:

```powershell
if (Test-Path package.json) { npm install --dry-run } else { Write-Output 'NO_PACKAGE_JSON' }
```

Result:

```text
NO_PACKAGE_JSON
```

Reason:

- There is no React/Vite frontend scaffold yet.
- There is no `package.json`.

Status: Not executable

### Frontend Build

Not executed.

Reason:

- No `frontend/` directory.
- No Vite config.
- No TypeScript config.
- No package scripts.

Status: Not executable

### Frontend Type Check

Not executed.

Reason:

- No TypeScript frontend exists yet.

Status: Not executable

### Database Integration Tests

Not executed.

Reason:

- No local `.env` with database credentials.
- No test PostgreSQL database.
- No FastAPI repositories or business endpoints yet.

Status: Not executable

### Legacy Runtime End-to-End Test

Not executed.

Reason:

- The legacy runtime requires real `.env` values, including `AUTH_SHARED_SECRET` and PostgreSQL credentials.
- The public and admin endpoints depend on a configured database.

Status: Not executable

### hCaptcha Validation

Not executed.

Reason:

- No hCaptcha keys are configured locally.
- The FastAPI hCaptcha service is not implemented yet.

Status: Not executable

### Discord Login Flow

Not executed.

Reason:

- Login depends on the external `https://auth.hcr2.xyz/login` service.
- No local OAuth callback or token generation flow is configured for manual end-to-end testing.

Status: Not executable

## Current Test Confidence

| Area | Confidence |
| --- | --- |
| Backend scaffold health | High |
| Backend config parsing | High |
| Backend token helper | High |
| Legacy PHP syntax | High |
| Legacy JS syntax | Medium |
| Legacy runtime behavior | Low |
| FastAPI business behavior | Low |
| React frontend | Low |
| End-to-end integration | Low |
