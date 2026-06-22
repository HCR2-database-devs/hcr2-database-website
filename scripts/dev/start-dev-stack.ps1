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

function Invoke-ExternalWithTimeout(
    [string]$FilePath,
    [string[]]$ArgumentList,
    [int]$TimeoutSeconds,
    [string]$Description
) {
    Write-Output "$Description..."
    $process = $null
    try {
        $command = Get-Command $FilePath -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $command) {
            throw "$FilePath was not found on PATH."
        }

        $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $command.Source
        $startInfo.Arguments = Join-ProcessArguments $ArgumentList
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true

        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $startInfo
        if (-not $process.Start()) {
            throw "$Description could not start $($command.Source)."
        }

        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            $process.Kill()
            throw "$Description timed out after ${TimeoutSeconds}s. Docker Desktop may be stopped or unresponsive."
        }

        $output = $process.StandardOutput.ReadToEnd().Trim()
        $errorOutput = $process.StandardError.ReadToEnd().Trim()
        if ($output) {
            Write-Output $output
        }
        if ($errorOutput) {
            Write-Output $errorOutput
        }
        $exitCode = $process.ExitCode
        if ($exitCode -ne 0) {
            throw "$Description failed with exit code $exitCode. Is Docker Desktop running?"
        }
    } finally {
        if ($null -ne $process) {
            $process.Dispose()
        }
    }
}

Invoke-ExternalWithTimeout `
    "docker" `
    @("compose", "-f", $composeFile, "up", "-d", "--build", "postgres") `
    (Get-DockerTimeoutSeconds) `
    "Starting development PostgreSQL container"

Write-Output "PostgreSQL: 127.0.0.1:54329"
