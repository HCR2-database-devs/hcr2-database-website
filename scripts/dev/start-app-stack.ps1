param(
    [switch]$RestartFastApi,
    [switch]$RestartFrontend
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$backendRoot = Join-Path $repoRoot "backend"
$frontendRoot = Join-Path $repoRoot "frontend"
$fastApiPidFile = Join-Path $backendRoot "fastapi-dev.pid"
$frontendPidFile = Join-Path $frontendRoot "vite-dev.pid"

function Get-ListeningProcessId([int]$Port) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        return [int]$listener.OwningProcess
    }
    return $null
}

function Get-ProcessInfo([int]$ProcessId) {
    return Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
}

function Test-TextContains([string]$Text, [string]$Needle) {
    return $Text.IndexOf($Needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
}

function Test-ProjectProcess([int]$ProcessId, [string]$ServiceName) {
    $processInfo = Get-ProcessInfo $ProcessId
    if ($null -eq $processInfo) {
        return $false
    }

    $commandLine = [string]$processInfo.CommandLine
    $executablePath = [string]$processInfo.ExecutablePath

    if ($ServiceName -eq "FastAPI") {
        $expectedPython = Join-Path $backendRoot ".venv\Scripts\python.exe"
        return (
            $executablePath.Equals($expectedPython, [System.StringComparison]::OrdinalIgnoreCase) -and
            (Test-TextContains $commandLine "uvicorn") -and
            (Test-TextContains $commandLine "app.main:app")
        )
    }

    if ($ServiceName -eq "Vite") {
        return (
            (Test-TextContains $commandLine $frontendRoot) -and
            (Test-TextContains $commandLine "vite") -and
            (Test-TextContains $commandLine "--port 5173")
        )
    }

    return $false
}

function Get-ProjectPidFromFile([string]$PidFile, [string]$ServiceName) {
    if (-not (Test-Path -LiteralPath $PidFile)) {
        return $null
    }

    $rawPid = (Get-Content -LiteralPath $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    $processId = 0
    if (-not [int]::TryParse($rawPid, [ref]$processId)) {
        Remove-Item -LiteralPath $PidFile -ErrorAction SilentlyContinue
        return $null
    }

    if (Test-ProjectProcess $processId $ServiceName) {
        return $processId
    }

    Remove-Item -LiteralPath $PidFile -ErrorAction SilentlyContinue
    return $null
}

function Wait-PortReleased([int]$Port) {
    for ($i = 1; $i -le 20; $i++) {
        if ($null -eq (Get-ListeningProcessId $Port)) {
            return
        }
        Start-Sleep -Milliseconds 250
    }
    throw "Port $Port was not released after stopping the project process."
}

function Stop-ProjectService([string]$ServiceName, [int]$Port, [string]$PidFile) {
    $processIds = @()
    $pidFromFile = Get-ProjectPidFromFile $PidFile $ServiceName
    if ($null -ne $pidFromFile) {
        $processIds += $pidFromFile
    }

    $listenerPid = Get-ListeningProcessId $Port
    if ($null -ne $listenerPid) {
        if (-not (Test-ProjectProcess $listenerPid $ServiceName)) {
            $processInfo = Get-ProcessInfo $listenerPid
            $processName = if ($processInfo) { $processInfo.Name } else { "unknown" }
            throw "$ServiceName cannot be restarted safely: port $Port is used by PID $listenerPid ($processName), which was not started from this project."
        }
        $processIds += $listenerPid
    }

    foreach ($processId in ($processIds | Select-Object -Unique)) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($null -ne $process) {
            Write-Output "Stopping project $ServiceName process on port ${Port}: PID $processId $($process.ProcessName)"
            Stop-Process -Id $processId -Force
        }
    }

    Remove-Item -LiteralPath $PidFile -ErrorAction SilentlyContinue
    Wait-PortReleased $Port
}

function Wait-HttpOk([string]$Url, [string]$Name) {
    Write-Output "Waiting for $Name at $Url..."
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
                return $response
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    throw "$Name did not become reachable at $Url."
}

function Join-ProcessArguments([string[]]$ArgumentList) {
    return ($ArgumentList | ForEach-Object {
        $argument = [string]$_
        if ($argument -match '[\s"]') {
            '"' + ($argument -replace '"', '\"') + '"'
        } else {
            $argument
        }
    }) -join " "
}

function Invoke-ProjectCommand(
    [string]$FilePath,
    [string[]]$ArgumentList,
    [string]$WorkingDirectory,
    [int]$TimeoutSeconds,
    [string]$Description
) {
    Write-Host "$Description..."
    $process = $null
    try {
        $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $FilePath
        $startInfo.Arguments = Join-ProcessArguments $ArgumentList
        $startInfo.WorkingDirectory = $WorkingDirectory
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true

        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $startInfo
        if (-not $process.Start()) {
            throw "$Description could not start $FilePath."
        }
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            $process.Kill()
            throw "$Description timed out after ${TimeoutSeconds}s."
        }

        $output = $process.StandardOutput.ReadToEnd().Trim()
        $errorOutput = $process.StandardError.ReadToEnd().Trim()
        if ($output) {
            Write-Host $output
        }
        if ($errorOutput) {
            Write-Host $errorOutput
        }

        $exitCode = $process.ExitCode
        if ($exitCode -ne 0) {
            throw "$Description failed with exit code $exitCode."
        }
    } finally {
        if ($null -ne $process) {
            $process.Dispose()
        }
    }
}

function Test-BackendDependencies {
    $python = Join-Path $backendRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $python)) {
        return $false
    }
    Write-Host "Checking backend Python dependencies..."
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & $python -c "import fastapi, uvicorn, psycopg, pydantic_core._pydantic_core" *> $null
        $dependencyExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($dependencyExitCode -eq 0) {
        return $true
    }
    Write-Host "Backend dependency check failed; repairing backend virtualenv."
    return $false
}

function Repair-BackendDependencies {
    $python = Join-Path $backendRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $python)) {
        throw "Backend virtualenv is missing at $python. Create it first with: cd backend; python -m venv .venv"
    }

    Invoke-ProjectCommand `
        $python `
        @("-m", "pip", "install", "--upgrade", "--force-reinstall", "--no-cache-dir", "pydantic", "pydantic-settings") `
        $backendRoot `
        300 `
        "Repairing backend pydantic packages"

    if (Test-BackendDependencies) {
        return
    }

    Invoke-ProjectCommand `
        $python `
        @("-m", "pip", "install", "-e", ".[dev]") `
        $backendRoot `
        600 `
        "Ensuring backend editable dependencies"
}

function Ensure-BackendDependencies {
    if (Test-BackendDependencies) {
        return
    }
    Repair-BackendDependencies
    if (-not (Test-BackendDependencies)) {
        throw "Backend dependencies are still broken after repair."
    }
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

Write-Output "Preparing local application stack..."

if ($RestartFastApi) {
    Stop-ProjectService "FastAPI" 8000 $fastApiPidFile
}

if ($RestartFrontend) {
    Stop-ProjectService "Vite" 5173 $frontendPidFile
}

& (Join-Path $PSScriptRoot "start-dev-stack.ps1")

if ($null -eq (Get-ListeningProcessId 8000)) {
    Ensure-BackendDependencies
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
        -WindowStyle Hidden `
        -PassThru
    Set-Content -LiteralPath $fastApiPidFile -Value $process.Id -Encoding ascii
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
        -WindowStyle Hidden `
        -PassThru
    Set-Content -LiteralPath $frontendPidFile -Value $process.Id -Encoding ascii
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

Write-Output "Application stack ready:"
Write-Output "- PostgreSQL: 127.0.0.1:54329"
Write-Output "- FastAPI: http://127.0.0.1:8000"
Write-Output "- React/Vite: http://127.0.0.1:5173"
