# Run from repo root (.\core\start-core.ps1) or from core (.\start-core.ps1)
$CoreDir = $PSScriptRoot
Set-Location $CoreDir

# Ensure .env exists for docker compose (vars: ABS_NETWORK, TZ, OLLAMA_PORT)
if (-not (Test-Path .env)) {
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "Created .env from .env.example. Edit core\.env if you need to change ports or network."
    } else {
        Write-Host "WARNING: No .env or .env.example in core. Create core\.env with ABS_NETWORK, TZ, OLLAMA_PORT."
    }
}

Write-Host "Starting ABS Minimal Core..."
docker compose -f docker-compose.yml --env-file .env up -d
Write-Host "Core services:"
docker compose -f docker-compose.yml ps

# Start GPU Metrics Server on host (needs nvidia-smi; Docker cannot see GPU here)
# Uses Node.js; no Python required. Install Node from https://nodejs.org if missing.
Write-Host "`nStarting GPU Metrics Server on port 8083..."
$gatewayPath = Join-Path $CoreDir "gateway"
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
    $gpuMetricsJob = Start-Job -Name "GPUMetricsServer" -ScriptBlock {
        param($p)
        Set-Location $p
        node gpu_metrics_server.js
    } -ArgumentList $gatewayPath
    Write-Host "GPU Metrics Server started (Job ID: $($gpuMetricsJob.Id))"
    Write-Host "  - Endpoint: http://127.0.0.1:8083/gpu-metrics"
    Write-Host "  - To stop: Stop-Job -Name GPUMetricsServer"
} else {
    Write-Host "Node.js not found. Install from https://nodejs.org to run GPU metrics on port 8083."
    Write-Host "  - Gateway (8081) and other services are running; only GPU metrics is skipped."
}