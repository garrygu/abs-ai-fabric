Build commands:
# 1. Start core services (if not already running)
cd C:\ABS\core
.\start-core.ps1

# 2. Build and run Contract Review Assistant
cd C:\ABS\abs-ai-hub\apps\contract-reviewer
docker compose up -d --build

# 3. Check status
docker compose ps

# 4. View logs
docker compose logs -f reviewer


Clean rebuild:
# Stop and remove containers
docker compose down

# Remove images to force rebuild
docker compose down --rmi all

# Rebuild from scratch
docker compose up -d --build --force-recreate


Troubleshooting:
# Check core services
cd C:\ABS\core
docker compose -f core.yml ps

# Check networks
docker network ls | findstr abs

# Check logs
docker compose logs reviewer


Environment variables:
QDRANT_URL: http://qdrant:6333
HUB_GATEWAY_URL: http://hub-gateway:8081
APP_PORT: 7860 (default)

Dependencies:
Core services: Qdrant, Hub Gateway, Redis
Python packages: reportlab, python-docx, pymupdf, etc.
System tools: tesseract-ocr, ocrmypdf, poppler-utils

Access:
Main app: http://localhost:7860
API docs: http://localhost:7860/docs
Health check: http://localhost:7860/healthz

The app builds a Docker image with Python 3.11, installs dependencies, and runs on port 7860.