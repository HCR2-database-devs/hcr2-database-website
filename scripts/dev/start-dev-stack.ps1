$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$composeFile = Join-Path $repoRoot "infra\dev\docker-compose.yml"

function Get-DockerTimeoutSeconds {
    $timeout = 45
    if ([int]::TryParse($env:DEV_DOCKER_TIMEOUT_SECONDS, [ref]$timeout) -and $timeout -gt 0) {
        return $timeout
    }
    return 45
}

function Invoke-ExternalWithTimeout(
    [string]$FilePath,
    [string[]]$ArgumentList,
    [int]$TimeoutSeconds,
    [string]$Description
) {
    Write-Output "$Description..."
    $stdout = [System.IO.Path]::GetTempFileName()
    $stderr = [System.IO.Path]::GetTempFileName()
    try {
        $process = Start-Process `
            -FilePath $FilePath `
            -ArgumentList $ArgumentList `
            -RedirectStandardOutput $stdout `
            -RedirectStandardError $stderr `
            -WindowStyle Hidden `
            -PassThru

        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            throw "$Description timed out after ${TimeoutSeconds}s. Docker Desktop may be stopped or unresponsive."
        }

        $output = (Get-Content -LiteralPath $stdout -Raw -ErrorAction SilentlyContinue).Trim()
        $errorOutput = (Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue).Trim()
        if ($output) {
            Write-Output $output
        }
        if ($errorOutput) {
            Write-Output $errorOutput
        }
        if ($process.ExitCode -ne 0) {
            throw "$Description failed with exit code $($process.ExitCode). Is Docker Desktop running?"
        }
    } finally {
        Remove-Item -LiteralPath $stdout, $stderr -ErrorAction SilentlyContinue
    }
}

Invoke-ExternalWithTimeout `
    "docker" `
    @("compose", "-f", $composeFile, "up", "-d", "--build", "postgres") `
    (Get-DockerTimeoutSeconds) `
    "Starting development PostgreSQL container"

Write-Output "PostgreSQL: 127.0.0.1:54329"
