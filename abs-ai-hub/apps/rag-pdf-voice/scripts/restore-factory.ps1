# Restore RAG PDF Voice to factory settings
Write-Host "Restoring RAG PDF Voice to factory settings..." -ForegroundColor Yellow
docker compose down -v
docker system prune -f
Write-Host "Factory restore completed!" -ForegroundColor Green
