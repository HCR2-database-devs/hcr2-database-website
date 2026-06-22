$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$composeFile = Join-Path $repoRoot "infra\dev\docker-compose.yml"

docker compose -f $composeFile down -v --remove-orphans
if ($LASTEXITCODE -ne 0) {
    throw "Failed to stop the development Docker stack. Is Docker Desktop running?"
}

docker compose -f $composeFile up -d --build postgres
if ($LASTEXITCODE -ne 0) {
    throw "Failed to start the development PostgreSQL service."
}

Write-Output "Waiting for PostgreSQL health check..."
$ready = $false
for ($i = 1; $i -le 30; $i++) {
    docker compose -f $composeFile exec -T postgres pg_isready -U hcr2_dev -d hcr2_dev
    if ($LASTEXITCODE -eq 0) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}
if (-not $ready) {
    throw "PostgreSQL health check failed after waiting."
}

Write-Output "Development database reset and seeded."
