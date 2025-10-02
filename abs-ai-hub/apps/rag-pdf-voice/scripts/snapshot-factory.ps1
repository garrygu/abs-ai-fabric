# Create snapshot of RAG PDF Voice factory state
Write-Host "Creating factory snapshot..." -ForegroundColor Green
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$snapshotName = "rag-pdf-voice-factory-$timestamp"
docker save -o "$snapshotName.tar" $(docker images --format "table {{.Repository}}:{{.Tag}}" | grep rag-pdf-voice)
Write-Host "Factory snapshot created: $snapshotName.tar" -ForegroundColor Green
