#!/bin/bash
# PostgreSQL Setup Script for Document Hub
# This script sets up PostgreSQL for the ABS AI Hub Document Hub

set -e

echo "🚀 Setting up PostgreSQL for Document Hub..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create shared data directory
echo "📁 Creating shared data directory..."
mkdir -p /abs-shared-data/postgres
chmod 755 /abs-shared-data/postgres

# Create ABS network if it doesn't exist
echo "🌐 Creating ABS network..."
docker network create abs-network 2>/dev/null || echo "Network abs-network already exists"

# Start PostgreSQL container
echo "🐘 Starting PostgreSQL container..."
cd "$(dirname "$0")/.."
docker-compose -f core.yml up -d postgresql

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker exec document-hub-postgres pg_isready -U hub_user -d document_hub > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "❌ PostgreSQL failed to start within $timeout seconds"
    echo "📋 Container logs:"
    docker logs document-hub-postgres
    exit 1
fi

# Test database connection
echo "🔍 Testing database connection..."
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT version();" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Database connection successful!"
else
    echo "❌ Database connection failed"
    exit 1
fi

# Show container status
echo "📊 PostgreSQL container status:"
docker ps --filter name=document-hub-postgres --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🎉 PostgreSQL setup completed successfully!"
echo ""
echo "📋 Connection details:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: document_hub"
echo "   Username: hub_user"
echo "   Password: secure_password"
echo ""
echo "🔧 Management endpoints:"
echo "   Health: http://localhost:8081/api/health/postgresql"
echo "   Metrics: http://localhost:8081/api/metrics/postgresql"
echo "   Management: http://localhost:8081/api/manage/postgresql"
echo ""
echo "📚 Next steps:"
echo "   1. Update your applications to use PostgreSQL for metadata storage"
echo "   2. Configure backup strategies for production use"
echo "   3. Monitor database performance through the gateway"
