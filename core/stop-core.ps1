cd C:\ABS\core

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
$gpuProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue | 
    Where-Object { $_.CommandLine -like "*gpu_metrics_server*" }
if ($gpuProcess) {
    $gpuProcess | Stop-Process -Force
    Write-Host "Killed orphaned GPU metrics server process."
}

Write-Host "`nStopping Docker services..."
docker compose -f docker-compose.yml --env-file .env down
Write-Host "ABS Core stopped."
