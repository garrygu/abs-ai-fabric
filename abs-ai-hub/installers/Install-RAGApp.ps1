# Install RAG App Script
param(
    [string]$AppName = "rag-pdf-voice",
    [string]$AppPath = "apps/rag-pdf-voice"
)

Write-Host "Installing $AppName..." -ForegroundColor Green

# Check if Docker is running
if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Navigate to app directory
$appDir = Join-Path $PSScriptRoot "..\$AppPath"
if (-not (Test-Path $appDir)) {
    Write-Host "App directory not found: $appDir" -ForegroundColor Red
    exit 1
}

Set-Location $appDir

# Start the application
Write-Host "Starting $AppName..." -ForegroundColor Yellow
docker compose up -d

# Wait for health check
Write-Host "Waiting for $AppName to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if app is running
$containerName = "abs-app-$AppName"
$container = docker ps --filter "name=$containerName" --format "table {{.Names}}\t{{.Status}}"
if ($container -match $containerName) {
    Write-Host "$AppName installed and running successfully!" -ForegroundColor Green
    Write-Host "Access the application at: http://localhost:8080" -ForegroundColor Cyan
} else {
    Write-Host "Failed to start $AppName. Check Docker logs." -ForegroundColor Red
    exit 1
}
