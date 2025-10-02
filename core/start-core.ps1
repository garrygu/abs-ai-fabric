cd C:\ABS\core
Write-Host "Starting ABS Minimal Core..."
docker compose -f core.yml --env-file .env up -d
Write-Host "Core services:"
docker compose -f core.yml ps
