@echo off
REM Contract Reviewer v2 - Integrated Deployment Script for Windows
REM This script deploys the complete integrated application with all services

setlocal enabledelayedexpansion

REM Configuration
set APP_NAME=contract-reviewer-v2-integrated
set APP_PORT=8082
set COMPOSE_FILE=docker-compose.yml

REM Functions
:log_info
echo [INFO] %~1
goto :eof

:log_success
echo [SUCCESS] %~1
goto :eof

:log_warning
echo [WARNING] %~1
goto :eof

:log_error
echo [ERROR] %~1
goto :eof

REM Check if Docker is running
:check_docker
call :log_info "Checking Docker status..."
docker info >nul 2>&1
if %errorlevel% neq 0 (
    call :log_error "Docker is not running. Please start Docker and try again."
    exit /b 1
)
call :log_success "Docker is running"
goto :eof

REM Check if Docker Compose is available
:check_docker_compose
call :log_info "Checking Docker Compose..."
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    call :log_error "Docker Compose is not installed. Please install Docker Compose and try again."
    exit /b 1
)
call :log_success "Docker Compose is available"
goto :eof

REM Create necessary directories
:create_directories
call :log_info "Creating necessary directories..."

REM Create data directories
if not exist "data\file_storage\documents" mkdir "data\file_storage\documents"
if not exist "data\file_storage\analysis_results" mkdir "data\file_storage\analysis_results"
if not exist "data\file_storage\reports" mkdir "data\file_storage\reports"
if not exist "data\file_storage\archives" mkdir "data\file_storage\archives"
if not exist "data\file_storage\templates" mkdir "data\file_storage\templates"
if not exist "data\file_storage\backups" mkdir "data\file_storage\backups"
if not exist "data\file_storage\temp" mkdir "data\file_storage\temp"
if not exist "data\file_storage\metadata" mkdir "data\file_storage\metadata"
if not exist "data\uploads" mkdir "data\uploads"
if not exist "data\reports" mkdir "data\reports"
if not exist "data\templates" mkdir "data\templates"
if not exist "data\logs" mkdir "data\logs"

call :log_success "Directories created successfully"
goto :eof

REM Check if required files exist
:check_files
call :log_info "Checking required files..."

if not exist "Dockerfile" (
    call :log_error "Required file Dockerfile not found"
    exit /b 1
)
if not exist "docker-compose.yml" (
    call :log_error "Required file docker-compose.yml not found"
    exit /b 1
)
if not exist "requirements_integrated.txt" (
    call :log_error "Required file requirements_integrated.txt not found"
    exit /b 1
)
if not exist "app_integrated.py" (
    call :log_error "Required file app_integrated.py not found"
    exit /b 1
)
if not exist "postgres-init\01-init-integrated.sql" (
    call :log_error "Required file postgres-init\01-init-integrated.sql not found"
    exit /b 1
)

call :log_success "All required files found"
goto :eof

REM Build the application
:build_app
call :log_info "Building Contract Reviewer v2 - Integrated..."

REM Build the Docker image
docker-compose -f %COMPOSE_FILE% build --no-cache
if %errorlevel% neq 0 (
    call :log_error "Failed to build application"
    exit /b 1
)

call :log_success "Application built successfully"
goto :eof

REM Start services
:start_services
call :log_info "Starting services..."

REM Start PostgreSQL first
call :log_info "Starting PostgreSQL..."
docker-compose -f %COMPOSE_FILE% up -d postgresql

REM Wait for PostgreSQL to be ready
call :log_info "Waiting for PostgreSQL to be ready..."
timeout /t 10 /nobreak >nul

REM Start Qdrant
call :log_info "Starting Qdrant..."
docker-compose -f %COMPOSE_FILE% up -d qdrant

REM Start Redis
call :log_info "Starting Redis..."
docker-compose -f %COMPOSE_FILE% up -d redis

REM Wait for services to be ready
call :log_info "Waiting for services to be ready..."
timeout /t 15 /nobreak >nul

REM Start the main application
call :log_info "Starting Contract Reviewer v2 - Integrated..."
docker-compose -f %COMPOSE_FILE% up -d contract-reviewer-v2-integrated

call :log_success "All services started successfully"
goto :eof

REM Check service health
:check_health
call :log_info "Checking service health..."

REM Wait for application to start
timeout /t 30 /nobreak >nul

REM Check PostgreSQL
docker exec document-hub-postgres pg_isready -U hub_user -d document_hub >nul 2>&1
if %errorlevel% equ 0 (
    call :log_success "PostgreSQL is healthy"
) else (
    call :log_warning "PostgreSQL health check failed"
)

REM Check Qdrant
curl -s http://localhost:6333/health >nul 2>&1
if %errorlevel% equ 0 (
    call :log_success "Qdrant is healthy"
) else (
    call :log_warning "Qdrant health check failed"
)

REM Check Redis
docker exec redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    call :log_success "Redis is healthy"
) else (
    call :log_warning "Redis health check failed"
)

REM Check main application
curl -s http://localhost:%APP_PORT%/api/health >nul 2>&1
if %errorlevel% equ 0 (
    call :log_success "Contract Reviewer v2 - Integrated is healthy"
) else (
    call :log_warning "Contract Reviewer v2 - Integrated health check failed"
)
goto :eof

REM Show service status
:show_status
call :log_info "Service Status:"
echo.

REM Show running containers
docker-compose -f %COMPOSE_FILE% ps

echo.
call :log_info "Service URLs:"
echo   Contract Reviewer v2 - Integrated: http://localhost:%APP_PORT%
echo   API Documentation: http://localhost:%APP_PORT%/docs
echo   Health Check: http://localhost:%APP_PORT%/api/health
echo   Statistics: http://localhost:%APP_PORT%/api/stats
echo.
echo   PostgreSQL: localhost:5432
echo   Qdrant: http://localhost:6333
echo   Redis: localhost:6379
echo.
goto :eof

REM Stop services
:stop_services
call :log_info "Stopping services..."
docker-compose -f %COMPOSE_FILE% down
call :log_success "Services stopped"
goto :eof

REM Clean up
:cleanup
call :log_info "Cleaning up..."
docker-compose -f %COMPOSE_FILE% down -v
docker system prune -f
call :log_success "Cleanup completed"
goto :eof

REM Show logs
:show_logs
call :log_info "Showing logs..."
docker-compose -f %COMPOSE_FILE% logs -f
goto :eof

REM Main deployment function
:deploy
call :log_info "Starting Contract Reviewer v2 - Integrated deployment..."
echo.

call :check_docker
call :check_docker_compose
call :create_directories
call :check_files
call :build_app
call :start_services
call :check_health
call :show_status

echo.
call :log_success "Deployment completed successfully!"
echo.
call :log_info "You can now:"
echo   1. Access the application at http://localhost:%APP_PORT%
echo   2. View API documentation at http://localhost:%APP_PORT%/docs
echo   3. Check health status at http://localhost:%APP_PORT%/api/health
echo   4. View logs with: deploy.bat logs
echo   5. Stop services with: deploy.bat stop
echo.
goto :eof

REM Main script logic
if "%1"=="" goto :deploy
if "%1"=="deploy" goto :deploy
if "%1"=="start" (
    call :start_services
    call :check_health
    call :show_status
    goto :eof
)
if "%1"=="stop" (
    call :stop_services
    goto :eof
)
if "%1"=="restart" (
    call :stop_services
    timeout /t 5 /nobreak >nul
    call :start_services
    call :check_health
    call :show_status
    goto :eof
)
if "%1"=="status" (
    call :show_status
    goto :eof
)
if "%1"=="health" (
    call :check_health
    goto :eof
)
if "%1"=="logs" (
    call :show_logs
    goto :eof
)
if "%1"=="cleanup" (
    call :cleanup
    goto :eof
)
if "%1"=="build" (
    call :check_docker
    call :check_docker_compose
    call :check_files
    call :build_app
    goto :eof
)

echo Usage: %0 {deploy^|start^|stop^|restart^|status^|health^|logs^|cleanup^|build}
echo.
echo Commands:
echo   deploy   - Full deployment (default)
echo   start    - Start services
echo   stop     - Stop services
echo   restart  - Restart services
echo   status   - Show service status
echo   health   - Check service health
echo   logs     - Show service logs
echo   cleanup  - Clean up everything
echo   build    - Build application only
exit /b 1
