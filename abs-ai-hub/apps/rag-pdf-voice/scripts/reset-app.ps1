# Reset RAG PDF Voice application
Write-Host "Resetting RAG PDF Voice..." -ForegroundColor Yellow
docker compose down -v
docker compose up -d
Write-Host "RAG PDF Voice reset completed!" -ForegroundColor Green
