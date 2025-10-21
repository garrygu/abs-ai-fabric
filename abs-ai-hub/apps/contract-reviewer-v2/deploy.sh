#!/bin/bash

# Contract Reviewer v2 - Integrated Deployment Script
# This script deploys the complete integrated application with all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="contract-reviewer-v2-integrated"
APP_PORT=8082
COMPOSE_FILE="docker-compose.yml"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    log_info "Checking Docker status..."
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log_success "Docker is running"
}

# Check if Docker Compose is available
check_docker_compose() {
    log_info "Checking Docker Compose..."
    if ! command -v docker-compose > /dev/null 2>&1; then
        log_error "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    log_success "Docker Compose is available"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    # Create data directories
    mkdir -p data/file_storage/{documents,analysis_results,reports,archives,templates,backups,temp,metadata}
    mkdir -p data/uploads
    mkdir -p data/reports
    mkdir -p data/templates
    mkdir -p data/logs
    
    # Set permissions
    chmod -R 755 data/
    
    log_success "Directories created successfully"
}

# Check if required files exist
check_files() {
    log_info "Checking required files..."
    
    local required_files=(
        "Dockerfile"
        "docker-compose.yml"
        "requirements_integrated.txt"
        "app_integrated.py"
        "postgres-init/01-init-integrated.sql"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file $file not found"
            exit 1
        fi
    done
    
    log_success "All required files found"
}

# Build the application
build_app() {
    log_info "Building Contract Reviewer v2 - Integrated..."
    
    # Build the Docker image
    docker-compose -f $COMPOSE_FILE build --no-cache
    
    if [ $? -eq 0 ]; then
        log_success "Application built successfully"
    else
        log_error "Failed to build application"
        exit 1
    fi
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start PostgreSQL first
    log_info "Starting PostgreSQL..."
    docker-compose -f $COMPOSE_FILE up -d postgresql
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Start Qdrant
    log_info "Starting Qdrant..."
    docker-compose -f $COMPOSE_FILE up -d qdrant
    
    # Start Redis
    log_info "Starting Redis..."
    docker-compose -f $COMPOSE_FILE up -d redis
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 15
    
    # Start the main application
    log_info "Starting Contract Reviewer v2 - Integrated..."
    docker-compose -f $COMPOSE_FILE up -d contract-reviewer-v2-integrated
    
    log_success "All services started successfully"
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    # Wait for application to start
    sleep 30
    
    # Check PostgreSQL
    if docker exec document-hub-postgres pg_isready -U hub_user -d document_hub > /dev/null 2>&1; then
        log_success "PostgreSQL is healthy"
    else
        log_warning "PostgreSQL health check failed"
    fi
    
    # Check Qdrant
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        log_success "Qdrant is healthy"
    else
        log_warning "Qdrant health check failed"
    fi
    
    # Check Redis
    if docker exec redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is healthy"
    else
        log_warning "Redis health check failed"
    fi
    
    # Check main application
    if curl -s http://localhost:$APP_PORT/api/health > /dev/null 2>&1; then
        log_success "Contract Reviewer v2 - Integrated is healthy"
    else
        log_warning "Contract Reviewer v2 - Integrated health check failed"
    fi
}

# Show service status
show_status() {
    log_info "Service Status:"
    echo ""
    
    # Show running containers
    docker-compose -f $COMPOSE_FILE ps
    
    echo ""
    log_info "Service URLs:"
    echo "  Contract Reviewer v2 - Integrated: http://localhost:$APP_PORT"
    echo "  API Documentation: http://localhost:$APP_PORT/docs"
    echo "  Health Check: http://localhost:$APP_PORT/api/health"
    echo "  Statistics: http://localhost:$APP_PORT/api/stats"
    echo ""
    echo "  PostgreSQL: localhost:5432"
    echo "  Qdrant: http://localhost:6333"
    echo "  Redis: localhost:6379"
    echo ""
}

# Stop services
stop_services() {
    log_info "Stopping services..."
    docker-compose -f $COMPOSE_FILE down
    log_success "Services stopped"
}

# Clean up
cleanup() {
    log_info "Cleaning up..."
    docker-compose -f $COMPOSE_FILE down -v
    docker system prune -f
    log_success "Cleanup completed"
}

# Show logs
show_logs() {
    log_info "Showing logs..."
    docker-compose -f $COMPOSE_FILE logs -f
}

# Main deployment function
deploy() {
    log_info "Starting Contract Reviewer v2 - Integrated deployment..."
    echo ""
    
    check_docker
    check_docker_compose
    create_directories
    check_files
    build_app
    start_services
    check_health
    show_status
    
    echo ""
    log_success "Deployment completed successfully!"
    echo ""
    log_info "You can now:"
    echo "  1. Access the application at http://localhost:$APP_PORT"
    echo "  2. View API documentation at http://localhost:$APP_PORT/docs"
    echo "  3. Check health status at http://localhost:$APP_PORT/api/health"
    echo "  4. View logs with: ./deploy.sh logs"
    echo "  5. Stop services with: ./deploy.sh stop"
    echo ""
}

# Main script logic
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "start")
        start_services
        check_health
        show_status
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 5
        start_services
        check_health
        show_status
        ;;
    "status")
        show_status
        ;;
    "health")
        check_health
        ;;
    "logs")
        show_logs
        ;;
    "cleanup")
        cleanup
        ;;
    "build")
        check_docker
        check_docker_compose
        check_files
        build_app
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|status|health|logs|cleanup|build}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  start    - Start services"
        echo "  stop     - Stop services"
        echo "  restart  - Restart services"
        echo "  status   - Show service status"
        echo "  health   - Check service health"
        echo "  logs     - Show service logs"
        echo "  cleanup  - Clean up everything"
        echo "  build    - Build application only"
        exit 1
        ;;
esac
