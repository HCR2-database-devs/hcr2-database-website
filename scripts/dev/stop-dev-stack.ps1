$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$composeFile = Join-Path $repoRoot "infra\dev\docker-compose.yml"

docker compose -f $composeFile down
if ($LASTEXITCODE -ne 0) {
    throw "Failed to stop the development Docker stack. Is Docker Desktop running?"
}
