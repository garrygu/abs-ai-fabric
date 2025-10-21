# Contract Reviewer v2 - Integrated Setup and Deployment Guide

## Overview

This guide covers the complete setup and deployment of Contract Reviewer v2 - Integrated, a comprehensive legal document analysis platform that combines PostgreSQL persistence, Qdrant vector search, Redis caching, and file-based storage.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│  Contract Reviewer v2 - Integrated Application                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                                │
│  Document Service | Vector Service | Processing | Storage       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │     REDIS        │    │   POSTGRESQL    │    │   QDRANT    │ │
│  │   (Caching)      │    │  (Persistence)  │    │ (Vectors)   │ │
│  │                 │    │                 │    │             │ │
│  │ • API Cache      │    │ • Document      │    │ • Text      │ │
│  │ • Doc Cache      │    │   Metadata      │    │   Chunks    │ │
│  │ • Analysis Cache │    │ • Analysis      │    │ • Embeddings│ │
│  │ • Session Data   │    │   Results       │    │ • Similarity│ │
│  │ • Rate Limiting  │    │ • User Data     │    │   Search    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│                                │                                │
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                FILE-BASED STORAGE                           │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │ │
│  │  │ Documents   │  │ Analysis    │  │ Reports     │         │ │
│  │  │             │  │ Results     │  │             │         │ │
│  │  │ • PDFs      │  │ • JSON      │  │ • PDF       │         │ │
│  │  │ • DOCX      │  │ • XML       │  │ • Word      │         │ │
│  │  │ • TXT       │  │ • YAML      │  │ • HTML      │         │ │
│  │  │ • Images    │  │ • Binary    │  │ • JSON      │         │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │ │
│  │  │ Archives    │  │ Templates   │  │ Backups     │         │ │
│  │  │             │  │             │  │             │         │ │
│  │  │ • ZIP       │  │ • Report    │  │ • Automated │         │ │
│  │  │ • TAR       │  │   Templates │  │ • Manual    │         │ │
│  │  │ • Compressed│  │ • Custom    │  │ • Scheduled │         │ │
│  │  │ • Encrypted │  │   Formats   │  │ • Versioned │         │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### System Requirements
- **OS**: Windows 10/11 or Ubuntu 20.04+
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: Minimum 50GB free space
- **CPU**: Multi-core processor recommended

### Software Requirements
- **Docker**: 20.10+ with Docker Compose
- **Python**: 3.9+ (if running without Docker)
- **Git**: For cloning the repository

### Services Required
- **PostgreSQL**: 15+ (via Docker)
- **Qdrant**: Latest (via Docker)
- **Redis**: 7+ (via Docker)
- **Hub Gateway**: For service management

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd ABS/abs-ai-hub/apps/contract-reviewer-v2
```

### 2. Environment Setup
```bash
# Create environment file
cat > .env << EOF
# Application Configuration
APP_PORT=8080
HUB_GATEWAY_URL=http://hub-gateway:8081

# Database Configuration
POSTGRES_URL=postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub

# Vector Database Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Cache Configuration
REDIS_URL=redis://redis:6379/0

# File Storage Configuration
FILE_STORAGE_PATH=/data/file_storage
MAX_FILE_SIZE=100

# Optional Configuration
ENABLE_COMPRESSION=true
LOG_LEVEL=INFO
EOF
```

### 3. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements_integrated.txt

# Or use Docker (recommended)
docker build -t contract-reviewer-v2-integrated .
```

### 4. Start Services
```bash
# Start core services (PostgreSQL, Qdrant, Redis)
cd ../../core
docker-compose -f core.yml up -d

# Start Hub Gateway
docker-compose -f core.yml up -d hub-gateway

# Start Contract Reviewer v2
cd ../abs-ai-hub/apps/contract-reviewer-v2
python app_integrated.py
```

### 5. Verify Installation
```bash
# Check application health
curl http://localhost:8080/api/health

# Check service status
curl http://localhost:8080/api/stats
```

## Detailed Setup

### 1. Core Services Setup

#### PostgreSQL Setup
```bash
# Start PostgreSQL container
cd ../../core
docker-compose -f core.yml up -d postgresql

# Verify PostgreSQL is running
docker exec document-hub-postgres pg_isready -U hub_user -d document_hub

# Check database tables
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "\dt"
```

#### Qdrant Setup
```bash
# Start Qdrant container
docker-compose -f core.yml up -d qdrant

# Verify Qdrant is running
curl http://localhost:6333/collections

# Check collections
curl http://localhost:6333/collections/legal_documents
```

#### Redis Setup
```bash
# Start Redis container
docker-compose -f core.yml up -d redis

# Verify Redis is running
docker exec redis redis-cli ping

# Check Redis info
docker exec redis redis-cli info
```

### 2. Application Configuration

#### Environment Variables
```bash
# Required Environment Variables
export APP_PORT=8080
export POSTGRES_URL="postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub"
export QDRANT_HOST=qdrant
export QDRANT_PORT=6333
export REDIS_URL="redis://redis:6379/0"
export FILE_STORAGE_PATH="/data/file_storage"
export MAX_FILE_SIZE=100

# Optional Environment Variables
export HUB_GATEWAY_URL="http://hub-gateway:8081"
export ENABLE_COMPRESSION=true
export LOG_LEVEL=INFO
```

#### File Storage Setup
```bash
# Create file storage directories
mkdir -p /data/file_storage/{documents,analysis_results,reports,archives,templates,backups,temp,metadata}

# Set permissions
chmod 755 /data/file_storage
chmod -R 755 /data/file_storage/*

# Verify directory structure
tree /data/file_storage
```

### 3. Application Deployment

#### Development Mode
```bash
# Run in development mode with auto-reload
python app_integrated.py

# Or with uvicorn directly
uvicorn app_integrated:app --host 0.0.0.0 --port 8080 --reload
```

#### Production Mode
```bash
# Run in production mode
uvicorn app_integrated:app --host 0.0.0.0 --port 8080 --workers 4

# Or with Docker
docker run -d \
  --name contract-reviewer-v2 \
  --network abs-net \
  -p 8080:8080 \
  -v /data/file_storage:/data/file_storage \
  -e POSTGRES_URL="postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub" \
  -e QDRANT_HOST=qdrant \
  -e REDIS_URL="redis://redis:6379/0" \
  contract-reviewer-v2-integrated
```

## API Usage

### 1. Document Upload
```bash
# Upload a document
curl -X POST "http://localhost:8080/api/documents/upload" \
  -F "file=@contract.pdf" \
  -F "client_id=ACME_Corp" \
  -F "document_type=contract" \
  -F "process_for_search=true" \
  -F "generate_report=false"
```

### 2. Document Analysis
```bash
# Analyze a document
curl -X POST "http://localhost:8080/api/analyze/doc-001" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "comprehensive",
    "include_risks": true,
    "include_recommendations": true,
    "include_citations": true,
    "process_for_search": true,
    "generate_report": true,
    "report_format": "pdf"
  }'
```

### 3. Semantic Search
```bash
# Search documents
curl -X POST "http://localhost:8080/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "confidentiality agreement",
    "limit": 10,
    "score_threshold": 0.7,
    "include_analysis": true,
    "include_reports": true
  }'
```

### 4. Document Management
```bash
# List documents
curl "http://localhost:8080/api/documents?limit=10&offset=0&include_vectors=true&include_reports=true"

# Get document info
curl "http://localhost:8080/api/documents/info/doc-001"

# Download document
curl "http://localhost:8080/api/documents/download/doc-001" -o contract.pdf
```

### 5. File Management
```bash
# Upload file to file storage
curl -X POST "http://localhost:8080/api/files/upload" \
  -F "file=@document.pdf" \
  -F "file_type=document" \
  -F "client_id=ACME_Corp"

# Create file version
curl -X POST "http://localhost:8080/api/files/version/file-001" \
  -H "Content-Type: application/json" \
  -d '{"version_comment": "Updated content"}'

# Create archive
curl -X POST "http://localhost:8080/api/files/archive" \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": ["file-001", "file-002"],
    "archive_name": "client_documents",
    "compression_level": 6
  }'
```

### 6. Report Generation
```bash
# Generate report
curl -X POST "http://localhost:8080/api/files/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": "report-001",
    "report_type": "analysis_summary",
    "format": "pdf",
    "document_ids": ["doc-001"],
    "analysis_ids": ["analysis-001"],
    "client_id": "ACME_Corp"
  }'

# List report templates
curl "http://localhost:8080/api/files/reports/templates"
```

## Monitoring and Maintenance

### 1. Health Monitoring
```bash
# Check application health
curl http://localhost:8080/api/health

# Get detailed statistics
curl http://localhost:8080/api/stats

# Check service status via Hub Gateway
curl http://localhost:8081/api/services/status
```

### 2. Log Monitoring
```bash
# View application logs
tail -f /var/log/contract-reviewer-v2/app.log

# View Docker logs
docker logs contract-reviewer-v2-integrated -f

# View service logs
docker logs document-hub-postgres -f
docker logs qdrant -f
docker logs redis -f
```

### 3. Storage Management
```bash
# Check storage statistics
curl "http://localhost:8080/api/files/storage/stats"

# Cleanup old files
curl -X POST "http://localhost:8080/api/files/storage/cleanup?days_old=30"

# Check disk usage
df -h /data/file_storage
du -sh /data/file_storage/*
```

### 4. Database Maintenance
```bash
# Check PostgreSQL status
docker exec document-hub-postgres pg_isready -U hub_user -d document_hub

# Check database size
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT pg_size_pretty(pg_database_size('document_hub'));"

# Check table sizes
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Troubleshooting

### Common Issues

#### 1. Service Connection Issues
```bash
# Check if services are running
docker ps | grep -E "(postgres|qdrant|redis)"

# Check network connectivity
docker exec contract-reviewer-v2-integrated ping document-hub-postgres
docker exec contract-reviewer-v2-integrated ping qdrant
docker exec contract-reviewer-v2-integrated ping redis

# Check service health
curl http://localhost:8080/api/health
```

#### 2. Database Connection Issues
```bash
# Test PostgreSQL connection
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT 1;"

# Check PostgreSQL logs
docker logs document-hub-postgres

# Restart PostgreSQL if needed
docker restart document-hub-postgres
```

#### 3. Vector Search Issues
```bash
# Check Qdrant status
curl http://localhost:6333/collections

# Check collection status
curl http://localhost:6333/collections/legal_documents

# Restart Qdrant if needed
docker restart qdrant
```

#### 4. File Storage Issues
```bash
# Check file storage permissions
ls -la /data/file_storage

# Check disk space
df -h /data/file_storage

# Check file storage health
curl "http://localhost:8080/api/files/storage/health"
```

#### 5. Memory Issues
```bash
# Check memory usage
free -h
docker stats

# Check Redis memory usage
docker exec redis redis-cli info memory

# Restart services if needed
docker restart contract-reviewer-v2-integrated
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_upload_timestamp ON documents(upload_timestamp);
CREATE INDEX IF NOT EXISTS idx_documents_client_id ON documents USING GIN ((metadata->>'client_id'));
CREATE INDEX IF NOT EXISTS idx_analysis_results_document_id ON analysis_results(document_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_analysis_type ON analysis_results(analysis_type);
```

#### 2. Redis Optimization
```bash
# Configure Redis for better performance
docker exec redis redis-cli CONFIG SET maxmemory 2gb
docker exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### 3. File Storage Optimization
```bash
# Enable compression for file storage
export ENABLE_COMPRESSION=true

# Set appropriate file size limits
export MAX_FILE_SIZE=100  # MB
```

## Security Considerations

### 1. Database Security
```bash
# Use strong passwords
export POSTGRES_PASSWORD="your_strong_password_here"

# Enable SSL for PostgreSQL
# Add to docker-compose.yml:
# environment:
#   POSTGRES_SSL_MODE: require
```

### 2. Network Security
```bash
# Use internal networks for service communication
# Ensure services are not exposed to external networks unnecessarily

# Use reverse proxy for external access
# Configure nginx or similar for SSL termination
```

### 3. File Storage Security
```bash
# Set appropriate file permissions
chmod 755 /data/file_storage
chmod -R 644 /data/file_storage/documents
chmod -R 644 /data/file_storage/analysis_results

# Enable file encryption (future feature)
# export ENABLE_ENCRYPTION=true
```

## Backup and Recovery

### 1. Database Backup
```bash
# Create database backup
docker exec document-hub-postgres pg_dump -U hub_user document_hub > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore database backup
docker exec -i document-hub-postgres psql -U hub_user document_hub < backup_20240115_120000.sql
```

### 2. File Storage Backup
```bash
# Create file storage backup
tar -czf file_storage_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data/file_storage

# Restore file storage backup
tar -xzf file_storage_backup_20240115_120000.tar.gz -C /
```

### 3. Complete System Backup
```bash
# Create complete system backup
docker-compose -f core.yml down
tar -czf complete_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  /data/file_storage \
  /var/lib/docker/volumes/core_postgres_data \
  /var/lib/docker/volumes/core_qdrant_storage \
  /var/lib/docker/volumes/core_redis_data
docker-compose -f core.yml up -d
```

## Scaling and Performance

### 1. Horizontal Scaling
```bash
# Run multiple application instances
uvicorn app_integrated:app --host 0.0.0.0 --port 8080 --workers 4

# Use load balancer for multiple instances
# Configure nginx or similar for load balancing
```

### 2. Database Scaling
```bash
# Use read replicas for PostgreSQL
# Configure connection pooling
# Consider database sharding for large datasets
```

### 3. Cache Optimization
```bash
# Increase Redis memory
docker exec redis redis-cli CONFIG SET maxmemory 4gb

# Use Redis clustering for high availability
# Configure Redis persistence
```

## Support and Maintenance

### 1. Regular Maintenance
- **Daily**: Check service health and logs
- **Weekly**: Review storage usage and cleanup old files
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and optimize database performance

### 2. Monitoring Setup
- Set up health check monitoring
- Configure log aggregation
- Set up alerting for service failures
- Monitor resource usage and performance

### 3. Documentation Updates
- Keep API documentation current
- Update setup guides as needed
- Document any custom configurations
- Maintain troubleshooting guides

This comprehensive setup guide ensures Contract Reviewer v2 - Integrated is properly deployed and maintained for production use!
