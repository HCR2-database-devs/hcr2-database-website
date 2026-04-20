$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$composeFile = Join-Path $repoRoot "infra\dev\docker-compose.yml"

docker compose -f $composeFile up -d --build
if ($LASTEXITCODE -ne 0) {
    throw "Failed to start the development Docker stack. Is Docker Desktop running?"
}

Write-Output "PostgreSQL: 127.0.0.1:54329"
Write-Output "Legacy PHP: http://127.0.0.1:18080"
