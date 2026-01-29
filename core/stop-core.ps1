# Run from repo root (.\core\stop-core.ps1) or from core (.\stop-core.ps1)
$CoreDir = $PSScriptRoot
Set-Location $CoreDir

# Stop GPU Metrics Server if running
Write-Host "Stopping GPU Metrics Server..."
$gpuJob = Get-Job -Name "GPUMetricsServer" -ErrorAction SilentlyContinue
if ($gpuJob) {
    Stop-Job -Name "GPUMetricsServer" -ErrorAction SilentlyContinue
    Remove-Job -Name "GPUMetricsServer" -ErrorAction SilentlyContinue
    Write-Host "GPU Metrics Server stopped."
} else {
    Write-Host "GPU Metrics Server not running as a job."
}

# Also kill any orphaned python processes running the metrics server
#$gpuProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue | 
#   Where-Object { $_.CommandLine -like "*gpu_metrics_server*" }
#if ($gpuProcess) {
#    $gpuProcess | Stop-Process -Force
#    Write-Host "Killed orphaned GPU metrics server process."
#}

# If you started GPU metrics manually in another terminal, close that window or run:
#   Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq '' } | Stop-Process -Force

Write-Host "`nStopping Docker services..."
$envFile = Join-Path $CoreDir ".env"
if (Test-Path $envFile) {
    docker compose -f docker-compose.yml --env-file .env down
} else {
    docker compose -f docker-compose.yml down
}
Write-Host "ABS Core stopped."
