param(
    [switch]$RestartFastApi,
    [switch]$RestartFrontend,
    [switch]$UseLocalPostgres
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$backendRoot = Join-Path $repoRoot "backend"
$frontendRoot = Join-Path $repoRoot "frontend"
$fastApiPidFile = Join-Path $backendRoot "fastapi-dev.pid"
$frontendPidFile = Join-Path $frontendRoot "vite-dev.pid"

$localDbHost = "127.0.0.1"
$localDbPort = "54329"
$localDbName = "hcr2_dev"
$localDbUser = "hcr2_dev"
$localDbPass = "hcr2_dev_password"

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

function Test-FastApiHealthSignature {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2
        return (
            $health.status -eq "ok" -and
            $health.service -eq "HCR2 Records API"
        )
    } catch {
        return $false
    }
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
        $isExpectedPython = $executablePath.Equals($expectedPython, [System.StringComparison]::OrdinalIgnoreCase)
        $isUvicornApp = (
            (Test-TextContains $commandLine "uvicorn") -and
            (Test-TextContains $commandLine "app.main:app") -and
            (Test-TextContains $commandLine "--port") -and
            (Test-TextContains $commandLine "8000")
        )

        return (
            $isUvicornApp -and
            ($isExpectedPython -or (Test-FastApiHealthSignature))
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

function Save-ListeningPid([int]$Port, [string]$PidFile) {
    $listenerPid = Get-ListeningProcessId $Port
    if ($null -ne $listenerPid) {
        Set-Content -LiteralPath $PidFile -Value $listenerPid -Encoding ascii
    }
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

function Get-WebExceptionDetails([System.Management.Automation.ErrorRecord]$ErrorRecord) {
    if ($null -eq $ErrorRecord.Exception.Response) {
        return $ErrorRecord.Exception.Message
    }

    $statusCode = [int]$ErrorRecord.Exception.Response.StatusCode
    $body = ""
    try {
        $stream = $ErrorRecord.Exception.Response.GetResponseStream()
        if ($null -ne $stream) {
            $reader = [System.IO.StreamReader]::new($stream)
            $body = $reader.ReadToEnd()
            $reader.Dispose()
        }
    } catch {
        $body = ""
    }

    if ([string]::IsNullOrWhiteSpace($body)) {
        return "HTTP $statusCode"
    }
    return "HTTP ${statusCode}: $body"
}

function Read-EnvFile([string]$Path) {
    $values = @{}
    if (-not (Test-Path -LiteralPath $Path)) {
        return $values
    }

    foreach ($line in (Get-Content -LiteralPath $Path)) {
        $trimmed = $line.Trim()
        if ($trimmed -eq "" -or $trimmed.StartsWith("#")) {
            continue
        }
        $separatorIndex = $trimmed.IndexOf("=")
        if ($separatorIndex -lt 1) {
            continue
        }
        $key = $trimmed.Substring(0, $separatorIndex).Trim()
        $value = $trimmed.Substring($separatorIndex + 1).Trim()
        if (
            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))
        ) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        $values[$key.ToUpperInvariant()] = $value
    }
    return $values
}

function Get-ConfiguredValue([hashtable]$Values, [string]$Name) {
    $lookupName = $Name.ToUpperInvariant()
    if ($Values.ContainsKey($lookupName) -and -not [string]::IsNullOrWhiteSpace($Values[$lookupName])) {
        return $Values[$lookupName]
    }

    $environmentValue = [Environment]::GetEnvironmentVariable($Name, "Process")
    if (-not [string]::IsNullOrWhiteSpace($environmentValue)) {
        return $environmentValue
    }

    return $null
}

function Test-LocalPostgresConfig(
    [string]$HostValue,
    [string]$PortValue,
    [string]$NameValue,
    [string]$UserValue,
    [string]$PassValue
) {
    return (
        $HostValue -eq $localDbHost -and
        ($PortValue -eq $localDbPort -or [string]::IsNullOrWhiteSpace($PortValue)) -and
        $NameValue -eq $localDbName -and
        $UserValue -eq $localDbUser -and
        $PassValue -eq $localDbPass
    )
}

function Test-ConfiguredDatabase([hashtable]$Values) {
    $databaseUrl = Get-ConfiguredValue $Values "DATABASE_URL"
    if (-not [string]::IsNullOrWhiteSpace($databaseUrl)) {
        return $true
    }

    $hostValue = Get-ConfiguredValue $Values "DB_HOST"
    if ([string]::IsNullOrWhiteSpace($hostValue)) {
        $hostValue = Get-ConfiguredValue $Values "PGHOST"
    }
    $portValue = Get-ConfiguredValue $Values "DB_PORT"
    if ([string]::IsNullOrWhiteSpace($portValue)) {
        $portValue = Get-ConfiguredValue $Values "PGPORT"
    }
    $nameValue = Get-ConfiguredValue $Values "DB_NAME"
    if ([string]::IsNullOrWhiteSpace($nameValue)) {
        $nameValue = Get-ConfiguredValue $Values "PGDATABASE"
    }
    $userValue = Get-ConfiguredValue $Values "DB_USER"
    if ([string]::IsNullOrWhiteSpace($userValue)) {
        $userValue = Get-ConfiguredValue $Values "PGUSER"
    }
    $passValue = Get-ConfiguredValue $Values "DB_PASS"
    if ([string]::IsNullOrWhiteSpace($passValue)) {
        $passValue = Get-ConfiguredValue $Values "PGPASSWORD"
    }

    if (Test-LocalPostgresConfig $hostValue $portValue $nameValue $userValue $passValue) {
        return $false
    }

    return (
        -not [string]::IsNullOrWhiteSpace($hostValue) -and
        -not [string]::IsNullOrWhiteSpace($nameValue) -and
        -not [string]::IsNullOrWhiteSpace($userValue) -and
        -not [string]::IsNullOrWhiteSpace($passValue)
    )
}

function Get-BackendEnvValues {
    $values = @{}
    foreach ($envFile in @((Join-Path $repoRoot ".env"), (Join-Path $backendRoot ".env"))) {
        $fileValues = Read-EnvFile $envFile
        foreach ($key in $fileValues.Keys) {
            $values[$key] = $fileValues[$key]
        }
    }
    return $values
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

function Set-EnvDefault([hashtable]$Values, [string]$Name, [string]$Value) {
    if ([string]::IsNullOrWhiteSpace((Get-ConfiguredValue $Values $Name))) {
        [Environment]::SetEnvironmentVariable($Name, $Value, "Process")
    }
}

function Set-BackendDevEnvironment([hashtable]$Values) {
    Set-EnvDefault $Values "AUTH_SHARED_SECRET" "dev-only-hcr2-secret"
    Set-EnvDefault $Values "ALLOWED_DISCORD_IDS" "dev-admin"
    Set-EnvDefault $Values "API_KEYS" "dev-api-key"
    Set-EnvDefault $Values "HCAPTCHA_SITE_KEY" "dev-hcaptcha-site-key"
    Set-EnvDefault $Values "HCAPTCHA_SECRET_KEY" "dev-hcaptcha-secret-key"
    Set-EnvDefault $Values "CORS_ORIGINS" "http://localhost:5173,http://127.0.0.1:5173"
}

function Set-LocalPostgresEnvironment {
    [Environment]::SetEnvironmentVariable("DATABASE_URL", "", "Process")
    [Environment]::SetEnvironmentVariable("PGHOST", "", "Process")
    [Environment]::SetEnvironmentVariable("PGPORT", "", "Process")
    [Environment]::SetEnvironmentVariable("PGDATABASE", "", "Process")
    [Environment]::SetEnvironmentVariable("PGUSER", "", "Process")
    [Environment]::SetEnvironmentVariable("PGPASSWORD", "", "Process")
    [Environment]::SetEnvironmentVariable("DB_SCHEMA", "", "Process")
    [Environment]::SetEnvironmentVariable("PGSCHEMA", "", "Process")
    [Environment]::SetEnvironmentVariable("DB_HOST", $localDbHost, "Process")
    [Environment]::SetEnvironmentVariable("DB_PORT", $localDbPort, "Process")
    [Environment]::SetEnvironmentVariable("DB_NAME", $localDbName, "Process")
    [Environment]::SetEnvironmentVariable("DB_USER", $localDbUser, "Process")
    [Environment]::SetEnvironmentVariable("DB_PASS", $localDbPass, "Process")
}

function Clear-LocalPostgresEnvironment {
    $databaseUrl = [Environment]::GetEnvironmentVariable("DATABASE_URL", "Process")
    if (
        [string]::IsNullOrWhiteSpace($databaseUrl) -or
        (
            (Test-TextContains $databaseUrl $localDbHost) -and
            (Test-TextContains $databaseUrl $localDbPort) -and
            (Test-TextContains $databaseUrl $localDbName)
        )
    ) {
        [Environment]::SetEnvironmentVariable("DATABASE_URL", $null, "Process")
    }

    $hostValue = [Environment]::GetEnvironmentVariable("DB_HOST", "Process")
    $portValue = [Environment]::GetEnvironmentVariable("DB_PORT", "Process")
    $nameValue = [Environment]::GetEnvironmentVariable("DB_NAME", "Process")
    $userValue = [Environment]::GetEnvironmentVariable("DB_USER", "Process")
    $passValue = [Environment]::GetEnvironmentVariable("DB_PASS", "Process")
    if (Test-LocalPostgresConfig $hostValue $portValue $nameValue $userValue $passValue) {
        foreach ($name in @("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASS")) {
            [Environment]::SetEnvironmentVariable($name, $null, "Process")
        }
    }

    foreach ($name in @("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD", "DB_SCHEMA", "PGSCHEMA")) {
        if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name, "Process"))) {
            [Environment]::SetEnvironmentVariable($name, $null, "Process")
        }
    }
}

Write-Output "Preparing local application stack..."
$backendEnvValues = Get-BackendEnvValues
$useConfiguredDatabase = Test-ConfiguredDatabase $backendEnvValues
$useLocalDatabase = $UseLocalPostgres -or (-not $useConfiguredDatabase)

if ($RestartFastApi) {
    Stop-ProjectService "FastAPI" 8000 $fastApiPidFile
}

if ($RestartFrontend) {
    Stop-ProjectService "Vite" 5173 $frontendPidFile
}

if ($useLocalDatabase) {
    if ($UseLocalPostgres) {
        Write-Output "Using local Docker PostgreSQL because -UseLocalPostgres was provided."
    } else {
        Write-Output "No configured PostgreSQL settings found; using local Docker PostgreSQL."
    }
    & (Join-Path $PSScriptRoot "start-dev-stack.ps1")
    Set-LocalPostgresEnvironment
} else {
    Write-Output "Using configured PostgreSQL settings from environment/.env."
    Clear-LocalPostgresEnvironment
}

if ($null -eq (Get-ListeningProcessId 8000)) {
    Ensure-BackendDependencies
    Set-BackendDevEnvironment $backendEnvValues
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
Save-ListeningPid 8000 $fastApiPidFile
try {
    Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/api/v1/maps" -TimeoutSec 10 | Out-Null
} catch {
    $details = Get-WebExceptionDetails $_
    throw "FastAPI is reachable but cannot read demo data from /api/v1/maps. $details"
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
Save-ListeningPid 5173 $frontendPidFile
try {
    Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5173/api/v1/maps" -TimeoutSec 10 | Out-Null
} catch {
    $details = Get-WebExceptionDetails $_
    throw "Vite is reachable but the FastAPI proxy cannot load demo data. $details"
}

Write-Output "Application stack ready:"
if ($useLocalDatabase) {
    Write-Output "- PostgreSQL: 127.0.0.1:54329"
} else {
    Write-Output "- PostgreSQL: configured environment/.env"
}
Write-Output "- FastAPI: http://127.0.0.1:8000"
Write-Output "- React/Vite: http://127.0.0.1:5173"
