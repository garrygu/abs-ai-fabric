@echo off
REM PostgreSQL Setup Script for Document Hub (Windows)
REM This script sets up PostgreSQL for the ABS AI Hub Document Hub

echo 🚀 Setting up PostgreSQL for Document Hub...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker first.
    exit /b 1
)

REM Create shared data directory
echo 📁 Creating shared data directory...
if not exist "C:\abs-shared-data\postgres" mkdir "C:\abs-shared-data\postgres"

REM Create ABS network if it doesn't exist
echo 🌐 Creating ABS network...
docker network create abs-network >nul 2>&1 || echo Network abs-network already exists

REM Start PostgreSQL container
echo 🐘 Starting PostgreSQL container...
cd /d "%~dp0\.."
docker-compose -f core.yml up -d postgresql

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
set timeout=60
set counter=0
:wait_loop
if %counter% geq %timeout% goto timeout_error
docker exec document-hub-postgres pg_isready -U hub_user -d document_hub >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL is ready!
    goto ready
)
timeout /t 2 /nobreak >nul
set /a counter+=2
goto wait_loop

:timeout_error
echo ❌ PostgreSQL failed to start within %timeout% seconds
echo 📋 Container logs:
docker logs document-hub-postgres
exit /b 1

:ready
REM Test database connection
echo 🔍 Testing database connection...
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT version();" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Database connection failed
    exit /b 1
)
echo ✅ Database connection successful!

REM Show container status
echo 📊 PostgreSQL container status:
docker ps --filter name=document-hub-postgres --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo 🎉 PostgreSQL setup completed successfully!
echo.
echo 📋 Connection details:
echo    Host: localhost
echo    Port: 5432
echo    Database: document_hub
echo    Username: hub_user
echo    Password: secure_password
echo.
echo 🔧 Management endpoints:
echo    Health: http://localhost:8081/api/health/postgresql
echo    Metrics: http://localhost:8081/api/metrics/postgresql
echo    Management: http://localhost:8081/api/manage/postgresql
echo.
echo 📚 Next steps:
echo    1. Update your applications to use PostgreSQL for metadata storage
echo    2. Configure backup strategies for production use
echo    3. Monitor database performance through the gateway

pause
