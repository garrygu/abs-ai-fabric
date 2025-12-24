cd C:\ABS\core
Write-Host "Starting ABS Minimal Core..."
docker compose -f docker-compose.yml --env-file .env up -d
Write-Host "Core services:"
docker compose -f docker-compose.yml ps

# Start GPU Metrics Server (runs on host, not Docker)
Write-Host "`nStarting GPU Metrics Server on port 8083..."
$gpuMetricsJob = Start-Job -Name "GPUMetricsServer" -ScriptBlock {
    cd C:\ABS\core\gateway
    python gpu_metrics_server.py
}
Write-Host "GPU Metrics Server started (Job ID: $($gpuMetricsJob.Id))"
Write-Host "  - Endpoint: http://127.0.0.1:8083/gpu-metrics"
Write-Host "  - To stop: Stop-Job -Name GPUMetricsServer"
