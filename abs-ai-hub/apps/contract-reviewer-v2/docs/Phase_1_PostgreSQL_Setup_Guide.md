# Phase 1: PostgreSQL Integration Setup Guide

## Overview
This document provides a complete guide for setting up PostgreSQL service for Phase 1 of the Centralized Document Hub implementation, including Docker setup, configuration, and integration with existing applications.

## PostgreSQL Service Options

### Option 1: Docker Compose (Recommended)
**Best for**: Development, testing, and small to medium deployments

### Option 2: Managed PostgreSQL Service
**Best for**: Production deployments, enterprise environments

### Option 3: Self-Managed PostgreSQL
**Best for**: Full control, custom configurations

## Option 1: Docker Compose Setup (Recommended)

### 1. Create PostgreSQL Service

#### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    container_name: abs-document-hub-postgres
    environment:
      - POSTGRES_DB=document_hub
      - POSTGRES_USER=hub_user
      - POSTGRES_PASSWORD=secure_password_123
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
      - ./postgresql.conf:/etc/postgresql/postgresql.conf
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hub_user -d document_hub"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - abs-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: abs-document-hub-redis
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - abs-network

  # Document Hub API (New Service)
  document-hub-api:
    image: document-hub-api:latest
    container_name: abs-document-hub-api
    environment:
      - DATABASE_URL=postgresql://hub_user:secure_password_123@postgres:5432/document_hub
      - REDIS_URL=redis://redis:6379/0
      - SHARED_DATA_PATH=/abs-shared-data
      - LOG_LEVEL=INFO
    volumes:
      - shared-data:/abs-shared-data
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - abs-network

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  shared-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /abs-shared-data

networks:
  abs-network:
    driver: bridge
```

### 2. PostgreSQL Configuration

#### postgresql.conf
```conf
# PostgreSQL Configuration for Document Hub
# Location: ./postgresql.conf

# Connection Settings
listen_addresses = '*'
port = 5432
max_connections = 100

# Memory Settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# WAL Settings
wal_level = replica
max_wal_size = 1GB
min_wal_size = 80MB
checkpoint_completion_target = 0.9

# Query Performance
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Extensions
shared_preload_libraries = 'pg_stat_statements'
```

### 3. Database Initialization Scripts

#### 01-init-database.sql
```sql
-- Database initialization script
-- Location: ./init-scripts/01-init-database.sql

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create custom types
CREATE TYPE document_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE access_level AS ENUM ('private', 'shared', 'public');
CREATE TYPE confidentiality_level AS ENUM ('public', 'internal', 'confidential', 'secret');
CREATE TYPE analysis_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'partial');
```

#### 02-create-tables.sql
```sql
-- Create core tables
-- Location: ./init-scripts/02-create-tables.sql

-- Documents table
CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    mime_type VARCHAR(100),
    
    -- Document metadata
    title VARCHAR(500),
    description TEXT,
    language VARCHAR(10) DEFAULT 'en',
    page_count INTEGER,
    word_count INTEGER,
    
    -- Business context
    client_id VARCHAR(100),
    case_number VARCHAR(100),
    matter_type VARCHAR(50),
    document_category VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'normal',
    
    -- Access control
    access_level access_level DEFAULT 'private',
    confidentiality_level confidentiality_level DEFAULT 'internal',
    
    -- Audit fields
    uploaded_by VARCHAR(100) NOT NULL,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    
    -- Status tracking
    processing_status document_status DEFAULT 'pending',
    analysis_status VARCHAR(20) DEFAULT 'none',
    validation_status VARCHAR(20) DEFAULT 'pending',
    
    -- Additional metadata
    custom_metadata JSONB DEFAULT '{}',
    tags TEXT[],
    keywords TEXT[],
    
    -- Full-text search
    search_vector tsvector
);

-- Document versions
CREATE TABLE document_versions (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    change_description TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    file_size BIGINT,
    
    UNIQUE(document_id, version_number)
);

-- Document relationships
CREATE TABLE document_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    target_document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    
    UNIQUE(source_document_id, target_document_id, relationship_type)
);

-- Document processing stages
CREATE TABLE document_processing_stages (
    stage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    stage_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    processing_time_seconds INTEGER,
    metadata JSONB
);

-- Document text
CREATE TABLE document_text (
    text_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    text_content TEXT NOT NULL,
    extraction_method VARCHAR(50),
    confidence_score FLOAT,
    language_detected VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document chunks
CREATE TABLE document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_type VARCHAR(50),
    start_position INTEGER,
    end_position INTEGER,
    word_count INTEGER,
    page_number INTEGER,
    section_title VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(document_id, chunk_index)
);

-- Applications
CREATE TABLE applications (
    app_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    app_name VARCHAR(50) UNIQUE NOT NULL,
    app_version VARCHAR(20),
    description TEXT,
    capabilities TEXT[],
    api_endpoint VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    configuration JSONB
);

-- App document permissions
CREATE TABLE app_document_permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    app_id UUID REFERENCES applications(app_id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    permission_type VARCHAR(20) NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by VARCHAR(100),
    expires_at TIMESTAMP WITH TIME ZONE,
    conditions JSONB,
    
    UNIQUE(app_id, document_id, permission_type)
);

-- App analyses
CREATE TABLE app_analyses (
    analysis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    app_id UUID REFERENCES applications(app_id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    analysis_version VARCHAR(20),
    status analysis_status DEFAULT 'pending',
    
    -- Analysis metadata
    model_used VARCHAR(100),
    confidence_score FLOAT,
    processing_time_seconds INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10,4),
    
    -- Results storage
    result_path TEXT,
    summary_path TEXT,
    report_path TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Analysis metadata
    analysis_metadata JSONB,
    quality_metrics JSONB
);

-- Users
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    role VARCHAR(50),
    client_access TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- User sessions
CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(document_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Audit logs
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(100),
    document_id UUID REFERENCES documents(document_id),
    analysis_id UUID REFERENCES app_analyses(analysis_id),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    details JSONB
);
```

#### 03-create-indexes.sql
```sql
-- Create indexes for optimal performance
-- Location: ./init-scripts/03-create-indexes.sql

-- Documents table indexes
CREATE INDEX idx_documents_client_id ON documents(client_id);
CREATE INDEX idx_documents_matter_type ON documents(matter_type);
CREATE INDEX idx_documents_upload_date ON documents(upload_date);
CREATE INDEX idx_documents_access_level ON documents(access_level);
CREATE INDEX idx_documents_processing_status ON documents(processing_status);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);

-- Composite indexes for common queries
CREATE INDEX idx_documents_client_matter ON documents(client_id, matter_type);
CREATE INDEX idx_documents_status_date ON documents(processing_status, upload_date);
CREATE INDEX idx_documents_access_client ON documents(access_level, client_id);

-- Full-text search indexes
CREATE INDEX idx_documents_title_fts ON documents USING gin(to_tsvector('english', title));
CREATE INDEX idx_documents_description_fts ON documents USING gin(to_tsvector('english', description));
CREATE INDEX idx_documents_tags_fts ON documents USING gin(tags);

-- JSONB indexes
CREATE INDEX idx_documents_custom_metadata ON documents USING gin(custom_metadata);
CREATE INDEX idx_documents_analysis_metadata ON documents USING gin(analysis_metadata);

-- Document chunks indexes
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_type ON document_chunks(chunk_type);
CREATE INDEX idx_document_chunks_text_fts ON document_chunks USING gin(to_tsvector('english', chunk_text));

-- App analyses indexes
CREATE INDEX idx_app_analyses_document_id ON app_analyses(document_id);
CREATE INDEX idx_app_analyses_app_id ON app_analyses(app_id);
CREATE INDEX idx_app_analyses_status ON app_analyses(status);
CREATE INDEX idx_app_analyses_created_at ON app_analyses(created_at);

-- Audit logs indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_document_id ON audit_logs(document_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
```

#### 04-create-functions.sql
```sql
-- Create utility functions
-- Location: ./init-scripts/04-create-functions.sql

-- Function to update search vector
CREATE OR REPLACE FUNCTION update_document_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update search vector
CREATE TRIGGER update_documents_search_vector
    BEFORE INSERT OR UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_document_search_vector();

-- Function to get document statistics
CREATE OR REPLACE FUNCTION get_document_stats(client_id_param VARCHAR DEFAULT NULL)
RETURNS TABLE (
    total_documents BIGINT,
    processed_documents BIGINT,
    pending_documents BIGINT,
    failed_documents BIGINT,
    avg_confidence FLOAT,
    total_size BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_documents,
        COUNT(CASE WHEN d.processing_status = 'completed' THEN 1 END) as processed_documents,
        COUNT(CASE WHEN d.processing_status = 'pending' THEN 1 END) as pending_documents,
        COUNT(CASE WHEN d.processing_status = 'failed' THEN 1 END) as failed_documents,
        AVG(a.confidence_score) as avg_confidence,
        SUM(d.file_size) as total_size
    FROM documents d
    LEFT JOIN app_analyses a ON d.document_id = a.document_id
    WHERE (client_id_param IS NULL OR d.client_id = client_id_param);
END;
$$ LANGUAGE plpgsql;
```

### 4. Environment Configuration

#### .env file
```bash
# Environment variables for Document Hub
# Location: .env

# PostgreSQL Configuration
POSTGRES_DB=document_hub
POSTGRES_USER=hub_user
POSTGRES_PASSWORD=secure_password_123
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DATABASE_URL=postgresql://hub_user:secure_password_123@postgres:5432/document_hub

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Application Configuration
SHARED_DATA_PATH=/abs-shared-data
LOG_LEVEL=INFO
API_PORT=8080

# Security
JWT_SECRET_KEY=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# Qdrant Configuration (for future phases)
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your_qdrant_api_key
```

### 5. Setup Scripts

#### setup-postgres.sh
```bash
#!/bin/bash
# PostgreSQL setup script
# Location: scripts/setup-postgres.sh

set -e

echo "🚀 Setting up PostgreSQL for Document Hub..."

# Create shared data directory
echo "📁 Creating shared data directory..."
sudo mkdir -p /abs-shared-data
sudo chown -R $USER:$USER /abs-shared-data

# Create init scripts directory
echo "📝 Creating initialization scripts..."
mkdir -p init-scripts

# Start PostgreSQL service
echo "🐘 Starting PostgreSQL service..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker-compose exec postgres pg_isready -U hub_user -d document_hub; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run database migrations
echo "🔄 Running database migrations..."
docker-compose exec postgres psql -U hub_user -d document_hub -f /docker-entrypoint-initdb.d/01-init-database.sql
docker-compose exec postgres psql -U hub_user -d document_hub -f /docker-entrypoint-initdb.d/02-create-tables.sql
docker-compose exec postgres psql -U hub_user -d document_hub -f /docker-entrypoint-initdb.d/03-create-indexes.sql
docker-compose exec postgres psql -U hub_user -d document_hub -f /docker-entrypoint-initdb.d/04-create-functions.sql

echo "✅ Database setup complete!"

# Test connection
echo "🧪 Testing database connection..."
docker-compose exec postgres psql -U hub_user -d document_hub -c "SELECT version();"

echo "🎉 PostgreSQL setup completed successfully!"
```

#### setup-postgres.ps1 (Windows)
```powershell
# PostgreSQL setup script for Windows
# Location: scripts/setup-postgres.ps1

Write-Host "🚀 Setting up PostgreSQL for Document Hub..." -ForegroundColor Green

# Create shared data directory
Write-Host "📁 Creating shared data directory..." -ForegroundColor Yellow
if (-not (Test-Path "C:\abs-shared-data")) {
    New-Item -ItemType Directory -Path "C:\abs-shared-data" -Force
}

# Create init scripts directory
Write-Host "📝 Creating initialization scripts..." -ForegroundColor Yellow
if (-not (Test-Path "init-scripts")) {
    New-Item -ItemType Directory -Path "init-scripts" -Force
}

# Start PostgreSQL service
Write-Host "🐘 Starting PostgreSQL service..." -ForegroundColor Yellow
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
Write-Host "⏳ Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
do {
    Start-Sleep -Seconds 2
    $ready = docker-compose exec postgres pg_isready -U hub_user -d document_hub 2>$null
} while ($LASTEXITCODE -ne 0)

Write-Host "✅ PostgreSQL is ready!" -ForegroundColor Green

# Run database migrations
Write-Host "🔄 Running database migrations..." -ForegroundColor Yellow
docker-compose exec postgres psql -U hub_user -d document_hub -f /docker-entrypoint-initdb.d/01-init-database.sql
docker-compose exec postgres psql -U hub_user -d document_hub -f /docker-entrypoint-initdb.d/02-create-tables.sql
docker-compose exec postgres psql -U hub_user -d document_hub -f /docker-entrypoint-initdb.d/03-create-indexes.sql
docker-compose exec postgres psql -U hub_user -d document_hub -f /docker-entrypoint-initdb.d/04-create-functions.sql

Write-Host "✅ Database setup complete!" -ForegroundColor Green

# Test connection
Write-Host "🧪 Testing database connection..." -ForegroundColor Yellow
docker-compose exec postgres psql -U hub_user -d document_hub -c "SELECT version();"

Write-Host "🎉 PostgreSQL setup completed successfully!" -ForegroundColor Green
```

### 6. Integration with Existing Apps

#### Update Contract Reviewer App
```python
# Update contract-reviewer-v2/app.py
import asyncpg
import redis
from pathlib import Path

class DocumentHubService:
    def __init__(self):
        self.postgres_pool = None
        self.redis_client = None
        self.shared_data_path = Path(os.getenv("SHARED_DATA_PATH", "/abs-shared-data"))
    
    async def initialize(self):
        """Initialize connections to Document Hub services"""
        # PostgreSQL connection pool
        self.postgres_pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL", "postgresql://hub_user:secure_password_123@postgres:5432/document_hub"),
            min_size=5,
            max_size=20
        )
        
        # Redis connection
        self.redis_client = redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379/0")
        )
    
    async def register_document(self, file_path: Path, metadata: dict) -> str:
        """Register document with Document Hub"""
        # Generate document ID and hash
        document_id = str(uuid.uuid4())
        file_hash = self.get_file_hash(file_path)
        
        # Check for duplicates
        async with self.postgres_pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT document_id FROM documents WHERE file_hash = $1",
                file_hash
            )
            if existing:
                return existing['document_id']
        
        # Move file to shared storage
        organized_path = self.organize_file_path(file_path, metadata)
        shutil.move(str(file_path), str(organized_path))
        
        # Register in PostgreSQL
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO documents 
                (document_id, filename, file_hash, file_path, file_size, file_type, 
                 client_id, matter_type, uploaded_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, document_id, metadata['filename'], file_hash, str(organized_path),
                metadata['file_size'], metadata['file_type'], metadata.get('client_id'),
                metadata.get('matter_type'), metadata['uploaded_by'])
        
        # Cache in Redis
        await self.redis_client.setex(
            f"document:{document_id}",
            3600,  # 1 hour TTL
            json.dumps({
                'document_id': document_id,
                'filename': metadata['filename'],
                'client_id': metadata.get('client_id'),
                'status': 'registered'
            })
        )
        
        return document_id

# Initialize Document Hub service
document_hub = DocumentHubService()

@app.on_event("startup")
async def startup_event():
    await document_hub.initialize()
```

### 7. Monitoring and Maintenance

#### Health Check Script
```python
# health-check.py
import asyncio
import asyncpg
import redis
import sys

async def check_postgres_health():
    """Check PostgreSQL health"""
    try:
        conn = await asyncpg.connect("postgresql://hub_user:secure_password_123@localhost:5432/document_hub")
        
        # Check basic connectivity
        result = await conn.fetchval("SELECT 1")
        assert result == 1
        
        # Check table existence
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        assert len(tables) > 0
        
        # Check document count
        doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
        print(f"✅ PostgreSQL: {doc_count} documents")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ PostgreSQL health check failed: {e}")
        return False

def check_redis_health():
    """Check Redis health"""
    try:
        r = redis.from_url("redis://localhost:6379/0")
        
        # Check connectivity
        r.ping()
        
        # Check memory usage
        info = r.info('memory')
        used_memory = info['used_memory']
        max_memory = info['maxmemory']
        
        if max_memory > 0:
            usage_percent = (used_memory / max_memory) * 100
            print(f"✅ Redis: {usage_percent:.1f}% memory usage")
        else:
            print(f"✅ Redis: {used_memory / 1024 / 1024:.1f} MB used")
        
        return True
    except Exception as e:
        print(f"❌ Redis health check failed: {e}")
        return False

async def main():
    """Run all health checks"""
    print("🔍 Running Document Hub health checks...")
    
    postgres_ok = await check_postgres_health()
    redis_ok = check_redis_health()
    
    if postgres_ok and redis_ok:
        print("🎉 All services are healthy!")
        sys.exit(0)
    else:
        print("⚠️ Some services are unhealthy!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

## Option 2: Managed PostgreSQL Service

### AWS RDS Setup
```bash
# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier document-hub-postgres \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.4 \
    --master-username hub_user \
    --master-user-password secure_password_123 \
    --allocated-storage 20 \
    --storage-type gp2 \
    --vpc-security-group-ids sg-12345678 \
    --db-subnet-group-name document-hub-subnet-group
```

### Azure Database for PostgreSQL
```bash
# Create Azure PostgreSQL server
az postgres server create \
    --resource-group document-hub-rg \
    --name document-hub-postgres \
    --location eastus \
    --admin-user hub_user \
    --admin-password secure_password_123 \
    --sku-name GP_Gen5_2 \
    --storage-size 20480
```

## Option 3: Self-Managed PostgreSQL

### Ubuntu Installation
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Configure PostgreSQL
sudo -u postgres psql -c "CREATE USER hub_user WITH PASSWORD 'secure_password_123';"
sudo -u postgres psql -c "CREATE DATABASE document_hub OWNER hub_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE document_hub TO hub_user;"

# Configure PostgreSQL
sudo nano /etc/postgresql/15/main/postgresql.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Restart PostgreSQL
sudo systemctl restart postgresql
sudo systemctl enable postgresql
```

### Windows Installation
```powershell
# Download and install PostgreSQL from https://www.postgresql.org/download/windows/
# Or use Chocolatey
choco install postgresql

# Create database and user
psql -U postgres -c "CREATE USER hub_user WITH PASSWORD 'secure_password_123';"
psql -U postgres -c "CREATE DATABASE document_hub OWNER hub_user;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE document_hub TO hub_user;"
```

## Deployment Checklist

### Pre-Deployment
- [ ] Choose PostgreSQL service option (Docker/Managed/Self-managed)
- [ ] Set up shared data directory (`/abs-shared-data`)
- [ ] Configure environment variables
- [ ] Prepare database initialization scripts
- [ ] Set up monitoring and logging

### Deployment
- [ ] Start PostgreSQL service
- [ ] Run database initialization scripts
- [ ] Verify database connectivity
- [ ] Test basic operations
- [ ] Configure backup strategy

### Post-Deployment
- [ ] Run health checks
- [ ] Monitor performance
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Test failover procedures

## Next Steps

After PostgreSQL is set up:

1. **Phase 1.1**: Update existing apps to use Document Hub
2. **Phase 1.2**: Implement Redis caching layer
3. **Phase 1.3**: Add Qdrant vector storage
4. **Phase 1.4**: Implement file-based storage
5. **Phase 1.5**: Add batch processing capabilities

This PostgreSQL setup provides a solid foundation for the Centralized Document Hub architecture!
