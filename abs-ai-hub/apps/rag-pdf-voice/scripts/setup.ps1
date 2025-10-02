# RAG PDF Voice Setup Script
Write-Host "Setting up RAG PDF Voice application..." -ForegroundColor Green

# Check if Docker is running
if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Desktop is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

Write-Host "RAG PDF Voice setup completed!" -ForegroundColor Green
