param(
    [switch]$RestartFastApi,
    [switch]$RestartFrontend
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$backendRoot = Join-Path $repoRoot "backend"
$frontendRoot = Join-Path $repoRoot "frontend"

function Get-ListeningProcessId([int]$Port) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        return [int]$listener.OwningProcess
    }
    return $null
}

function Stop-Listener([int]$Port) {
    $processId = Get-ListeningProcessId $Port
    if ($null -eq $processId) {
        return
    }
    if ($processId -le 0) {
        throw "Port $Port is occupied by a system process and cannot be restarted safely."
    }

    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    Write-Output "Stopping listener on port ${Port}: PID $processId $($process.ProcessName)"
    Stop-Process -Id $processId -Force
    Start-Sleep -Seconds 2
}

function Wait-HttpOk([string]$Url, [string]$Name) {
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
                return $response
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    throw "$Name did not become reachable at $Url."
}

function Set-BackendDevEnvironment {
    $env:DB_HOST = "127.0.0.1"
    $env:DB_PORT = "54329"
    $env:DB_NAME = "hcr2_dev"
    $env:DB_USER = "hcr2_dev"
    $env:DB_PASS = "hcr2_dev_password"
    $env:AUTH_SHARED_SECRET = "dev-only-hcr2-secret"
    $env:ALLOWED_DISCORD_IDS = "dev-admin"
    $env:API_KEYS = "dev-api-key"
    $env:HCAPTCHA_SITE_KEY = "dev-hcaptcha-site-key"
    $env:HCAPTCHA_SECRET_KEY = "dev-hcaptcha-secret-key"
    $env:CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
}

& (Join-Path $PSScriptRoot "start-dev-stack.ps1")

if ($RestartFastApi) {
    Stop-Listener 8000
}

if ($null -eq (Get-ListeningProcessId 8000)) {
    Set-BackendDevEnvironment
    $stdout = Join-Path $backendRoot "fastapi-dev.log"
    $stderr = Join-Path $backendRoot "fastapi-dev.err.log"
    Remove-Item -LiteralPath $stdout, $stderr -ErrorAction SilentlyContinue

    $process = Start-Process `
        -FilePath (Join-Path $backendRoot ".venv\Scripts\python.exe") `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $backendRoot `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru
    Write-Output "Started FastAPI: http://127.0.0.1:8000 (PID $($process.Id))"
} else {
    Write-Output "FastAPI port 8000 is already in use; keeping the existing listener."
}

Wait-HttpOk "http://127.0.0.1:8000/health" "FastAPI" | Out-Null
try {
    Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/api/v1/maps" -TimeoutSec 10 | Out-Null
} catch {
    throw "FastAPI is reachable but cannot read demo data. Re-run with -RestartFastApi if an old process is using port 8000."
}

if ($RestartFrontend) {
    Stop-Listener 5173
}

if ($null -eq (Get-ListeningProcessId 5173)) {
    $stdout = Join-Path $frontendRoot "vite-dev.log"
    $stderr = Join-Path $frontendRoot "vite-dev.err.log"
    Remove-Item -LiteralPath $stdout, $stderr -ErrorAction SilentlyContinue

    $process = Start-Process `
        -FilePath "npm.cmd" `
        -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "5173") `
        -WorkingDirectory $frontendRoot `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru
    Write-Output "Started Vite: http://127.0.0.1:5173 (PID $($process.Id))"
} else {
    Write-Output "Vite port 5173 is already in use; keeping the existing listener."
}

Wait-HttpOk "http://127.0.0.1:5173/" "Vite" | Out-Null
try {
    Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5173/api/v1/maps" -TimeoutSec 10 | Out-Null
} catch {
    throw "Vite is reachable but the FastAPI proxy cannot load demo data."
}

Write-Output "Migrated stack ready:"
Write-Output "- PostgreSQL: 127.0.0.1:54329"
Write-Output "- Legacy PHP: http://127.0.0.1:18080"
Write-Output "- FastAPI: http://127.0.0.1:8000"
Write-Output "- React/Vite: http://127.0.0.1:5173"
