# Centralized Document Hub Architecture & Docker Implementation Guide

## Overview

This comprehensive guide covers the complete implementation of a centralized document hub architecture for the ABS multi-app ecosystem, including both the architectural design and Docker-based deployment strategy. This enables multiple applications (contract-reviewer, legal-assistant, onyx, etc.) to share documents, analysis results, and insights efficiently.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Docker Volume Sharing](#docker-volume-sharing)
3. [Shared Storage Structure](#shared-storage-structure)
4. [Document Registry System](#document-registry-system)
5. [Shared Document Service](#shared-document-service)
6. [App Integration Strategy](#app-integration-strategy)
7. [Docker Implementation](#docker-implementation)
8. [Deployment Guide](#deployment-guide)
9. [Cross-App Data Sharing](#cross-app-data-sharing)
10. [Security & Access Control](#security--access-control)
11. [Monitoring & Maintenance](#monitoring--maintenance)
12. [Migration Strategy](#migration-strategy)

---

## Architecture Overview

### Current Problem
- Multiple apps (contract-reviewer, legal-assistant, onyx, etc.) need access to same documents
- Duplicate storage wastes disk space and creates sync issues
- No centralized document management
- Apps can't share analysis results or insights

### Solution: Centralized Document Hub with Docker Volume Sharing

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│  Contract Reviewer | Legal Assistant | Onyx | Other Apps        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                                │
│  Shared Document Service | Vector Service | Analysis Service    │
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
│  │ • Doc Cache      │    │   Registry      │    │   Chunks    │ │
│  │ • Analysis Cache │    │ • Analysis      │    │ • Embeddings│ │
│  │ • Session Data   │    │   Results       │    │ • Similarity│ │
│  │ • Rate Limiting  │    │ • User Data     │    │   Search    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│                                │                                │
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                SHARED FILE STORAGE                          │ │
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

---

## Docker Volume Sharing

### Volume Sharing Methods

#### 1. **Named Volume Sharing (Recommended)**

Multiple apps can access the same Docker volume by using identical volume names:

```yaml
# App 1: Contract Reviewer v2
volumes:
  - shared-document-hub:/abs-shared-data

# App 2: Legal Assistant  
volumes:
  - shared-document-hub:/abs-shared-data

# App 3: Onyx
volumes:
  - shared-document-hub:/abs-shared-data
```

#### 2. **External Volume References**

Create volumes outside docker-compose and reference them:

```bash
# Create shared volume
docker volume create shared-document-hub

# Use in multiple docker-compose files
```

#### 3. **Host Directory Mounting**

Mount the same host directory to multiple containers:

```yaml
# All apps mount the same host directory
volumes:
  - /host/path/abs-shared-data:/abs-shared-data
```

### Volume Management Commands

```bash
# Create shared volume
docker volume create shared-document-hub

# List all volumes
docker volume ls

# Inspect specific volume
docker volume inspect shared-document-hub

# Backup shared volume
docker run --rm \
  -v shared-document-hub:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/shared-documents-backup.tar.gz -C /data .

# Restore shared volume
docker run --rm \
  -v shared-document-hub:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/shared-documents-backup.tar.gz -C /data
```

---

## Shared Storage Structure

### Centralized Document Storage Structure

```
/abs-shared-data/
├── documents/                          # Centralized document storage
│   ├── raw/                           # Original uploaded files
│   │   ├── 2024/
│   │   │   ├── 01/
│   │   │   │   ├── 15/
│   │   │   │   │   ├── ABC-Corp-NDA-a1b2c3d4.pdf
│   │   │   │   │   └── XYZ-Inc-Contract-e5f6g7h8.docx
│   │   │   │   └── 16/
│   │   │   └── 02/
│   │   └── 2023/
│   ├── processed/                      # Extracted text and metadata
│   │   ├── text/
│   │   │   ├── ABC-Corp-NDA-a1b2c3d4.txt
│   │   │   └── XYZ-Inc-Contract-e5f6g7h8.txt
│   │   └── metadata/
│   │       ├── ABC-Corp-NDA-a1b2c3d4.json
│   │       └── XYZ-Inc-Contract-e5f6g7h8.json
│   └── chunks/                        # Text chunks for vector storage
│       ├── ABC-Corp-NDA-a1b2c3d4-chunks.json
│       └── XYZ-Inc-Contract-e5f6g7h8-chunks.json
├── analyses/                          # App-specific analysis results
│   ├── contract-reviewer/
│   │   ├── 2024/01/15/
│   │   │   ├── ABC-Corp-NDA-analysis-a1b2c3d4.json
│   │   │   └── XYZ-Inc-Contract-analysis-e5f6g7h8.json
│   │   └── 2024/01/16/
│   ├── legal-assistant/
│   │   ├── 2024/01/15/
│   │   └── 2024/01/16/
│   └── onyx/
│       ├── 2024/01/15/
│       └── 2024/01/16/
├── vectors/                           # Shared vector storage
│   ├── document-chunks/               # Document chunk embeddings
│   ├── analysis-insights/             # Analysis insight embeddings
│   └── cross-app-similarities/        # Cross-app similarity data
├── shared-db/                         # Shared database files
│   ├── documents.db                   # PostgreSQL for document metadata
│   ├── users.db                       # Shared user management
│   └── app-permissions.db             # App access permissions
└── cache/                            # Shared cache directory
    ├── redis/                        # Redis data directory (primary cache)
    └── temp/                         # Temporary processing files
```

### App-Specific Storage

Each app maintains its own private storage:

```
/data/app-specific/
├── logs/                        # Application logs
├── cache/                       # App-specific cache
├── config/                      # App configuration
└── temp/                        # App temporary files
```

---

## Document Registry System

### Central Document Registry (PostgreSQL)

```sql
-- Central document registry
CREATE TABLE shared_documents (
    document_id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) UNIQUE,      -- SHA-256 for deduplication
    file_path TEXT NOT NULL,           -- Path to raw file
    file_size BIGINT,
    file_type VARCHAR(10),
    upload_date TIMESTAMP DEFAULT NOW(),
    uploaded_by VARCHAR(100),
    client_id VARCHAR(100),
    case_number VARCHAR(100),
    matter_type VARCHAR(50),
    access_level VARCHAR(20) DEFAULT 'private', -- private, shared, public
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- App-specific analysis tracking
CREATE TABLE app_analyses (
    analysis_id UUID PRIMARY KEY,
    document_id UUID REFERENCES shared_documents(document_id),
    app_name VARCHAR(50) NOT NULL,     -- contract-reviewer, legal-assistant, etc.
    analysis_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    result_path TEXT,                  -- Path to analysis results
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Cross-app document access
CREATE TABLE app_document_access (
    app_name VARCHAR(50),
    document_id UUID REFERENCES shared_documents(document_id),
    access_type VARCHAR(20),           -- read, analyze, modify
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by VARCHAR(100),
    PRIMARY KEY (app_name, document_id)
);

-- Performance indexes
CREATE INDEX idx_shared_documents_hash ON shared_documents(file_hash);
CREATE INDEX idx_shared_documents_client ON shared_documents(client_id);
CREATE INDEX idx_shared_documents_matter_type ON shared_documents(matter_type);
CREATE INDEX idx_app_analyses_document_id ON app_analyses(document_id);
CREATE INDEX idx_app_analyses_app_name ON app_analyses(app_name);
CREATE INDEX idx_app_document_access_app ON app_document_access(app_name);
```

---

## Shared Document Service

### Document Service API Implementation

```python
import asyncio
import asyncpg
import redis
import json
import uuid
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class SharedDocumentService:
    def __init__(self, base_path="/abs-shared-data"):
        self.base_path = Path(base_path)
        self.postgres_pool = None
        self.redis = redis.from_url("redis://redis:6379/0")
        self.raw_path = self.base_path / "documents" / "raw"
        self.processed_path = self.base_path / "documents" / "processed"
        self.analyses_path = self.base_path / "analyses"
    
    async def initialize(self):
        """Initialize PostgreSQL connection pool"""
        self.postgres_pool = await asyncpg.create_pool(
            "postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub"
        )
    
    async def register_document(self, file_path: Path, metadata: dict) -> str:
        """Register a new document in the shared system"""
        # Generate document ID and hash
        document_id = str(uuid.uuid4())
        file_hash = self.get_file_hash(file_path)
        
        # Check for duplicates
        existing = await self.find_by_hash(file_hash)
        if existing:
            return existing['document_id']
        
        # Move file to shared storage
        organized_path = self.organize_file_path(file_path, metadata)
        organized_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(organized_path))
        
        # Register in PostgreSQL database
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO shared_documents 
                (document_id, filename, file_hash, file_path, file_size, file_type, 
                 client_id, case_number, matter_type, uploaded_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, document_id, metadata['filename'], file_hash, str(organized_path),
                metadata['file_size'], metadata['file_type'], metadata.get('client_id'),
                metadata.get('case_number'), metadata.get('matter_type'), metadata['uploaded_by'])
        
        # Cache in Redis
        self.redis.setex(f"document:{document_id}", 3600, json.dumps({
            'document_id': document_id,
            'filename': metadata['filename'],
            'file_path': str(organized_path),
            'client_id': metadata.get('client_id')
        }))
        
        return document_id
    
    async def get_document_path(self, document_id: str) -> Optional[Path]:
        """Get the file path for a document"""
        # Check Redis cache first
        cached = self.redis.get(f"document:{document_id}")
        if cached:
            data = json.loads(cached)
            return Path(data['file_path'])
        
        # Query PostgreSQL
        async with self.postgres_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT file_path FROM shared_documents WHERE document_id = $1",
                document_id
            )
            
            if result:
                return Path(result['file_path'])
            return None
    
    async def get_documents_for_app(self, app_name: str, filters: dict = None) -> List[dict]:
        """Get documents accessible by a specific app"""
        query = """
            SELECT d.*, a.access_type 
            FROM shared_documents d
            JOIN app_document_access a ON d.document_id = a.document_id
            WHERE a.app_name = $1
        """
        params = [app_name]
        
        if filters:
            if 'client_id' in filters:
                query += " AND d.client_id = $2"
                params.append(filters['client_id'])
            if 'matter_type' in filters:
                param_num = len(params) + 1
                query += f" AND d.matter_type = ${param_num}"
                params.append(filters['matter_type'])
        
        async with self.postgres_pool.acquire() as conn:
            results = await conn.fetch(query, *params)
            return [dict(row) for row in results]
    
    async def register_analysis(self, document_id: str, app_name: str, 
                               analysis_type: str, result_path: str) -> str:
        """Register analysis results for a document"""
        analysis_id = str(uuid.uuid4())
        
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO app_analyses 
                (analysis_id, document_id, app_name, analysis_type, result_path, status)
                VALUES ($1, $2, $3, $4, $5, 'completed')
            """, analysis_id, document_id, app_name, analysis_type, result_path)
        
        # Cache analysis result
        self.redis.setex(f"analysis:{analysis_id}", 86400, json.dumps({
            'analysis_id': analysis_id,
            'document_id': document_id,
            'app_name': app_name,
            'analysis_type': analysis_type,
            'result_path': result_path
        }))
        
        return analysis_id
    
    async def grant_app_access(self, app_name: str, document_id: str, access_type: str):
        """Grant access to a document for a specific app"""
        async with self.postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO app_document_access (app_name, document_id, access_type)
                VALUES ($1, $2, $3)
                ON CONFLICT (app_name, document_id) 
                DO UPDATE SET access_type = $3, granted_at = NOW()
            """, app_name, document_id, access_type)
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        import hashlib
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def organize_file_path(self, file_path: Path, metadata: dict) -> Path:
        """Organize file path based on date and metadata"""
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        
        # Create organized path
        organized_path = self.raw_path / year / month / day / file_path.name
        return organized_path
    
    async def find_by_hash(self, file_hash: str) -> Optional[dict]:
        """Find existing document by hash"""
        async with self.postgres_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM shared_documents WHERE file_hash = $1",
                file_hash
            )
            return dict(result) if result else None
```

---

## App Integration Strategy

### Contract Reviewer Integration

```python
# In contract-reviewer app_integrated.py
class ContractReviewerService:
    def __init__(self):
        self.shared_service = SharedDocumentService()
        self.analysis_path = Path("/abs-shared-data/analyses/contract-reviewer")
    
    async def upload_document(self, file: UploadFile) -> dict:
        # Save to temporary location first
        temp_path = self.save_temp_file(file)
        
        # Register with shared service
        document_id = await self.shared_service.register_document(
            temp_path, 
            {
                'filename': file.filename,
                'file_size': file.size,
                'file_type': Path(file.filename).suffix,
                'uploaded_by': self.current_user,
                'client_id': self.get_client_from_context(),
                'matter_type': self.detect_matter_type(file.filename)
            }
        )
        
        # Grant access to this app
        await self.shared_service.grant_app_access(
            'contract-reviewer', document_id, 'analyze'
        )
        
        return {'document_id': document_id}
    
    async def analyze_document(self, document_id: str) -> dict:
        # Get document path from shared service
        doc_path = await self.shared_service.get_document_path(document_id)
        
        # Perform analysis
        analysis_result = await self.run_analysis(doc_path)
        
        # Save analysis results
        analysis_path = self.analysis_path / self.get_date_path() / f"{document_id}-analysis.json"
        analysis_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(analysis_path, 'w') as f:
            json.dump(analysis_result, f)
        
        # Register analysis with shared service
        analysis_id = await self.shared_service.register_analysis(
            document_id, 'contract-reviewer', 'comprehensive', str(analysis_path)
        )
        
        return {'analysis_id': analysis_id, 'result_path': str(analysis_path)}
```

### Legal Assistant Integration

```python
# In legal-assistant app.py
class LegalAssistantService:
    def __init__(self):
        self.shared_service = SharedDocumentService()
        self.analysis_path = Path("/abs-shared-data/analyses/legal-assistant")
    
    async def get_available_documents(self, client_id: str = None) -> List[dict]:
        """Get documents available for legal assistant"""
        return await self.shared_service.get_documents_for_app(
            'legal-assistant', 
            {'client_id': client_id} if client_id else None
        )
    
    async def analyze_document(self, document_id: str) -> dict:
        # Check if contract-reviewer already analyzed this document
        existing_analysis = await self.shared_service.get_existing_analysis(
            document_id, 'contract-reviewer'
        )
        
        if existing_analysis:
            # Use existing analysis as base
            base_analysis = self.load_analysis(existing_analysis['result_path'])
            enhanced_analysis = await self.enhance_analysis(base_analysis)
        else:
            # Perform fresh analysis
            doc_path = await self.shared_service.get_document_path(document_id)
            enhanced_analysis = await self.run_analysis(doc_path)
        
        # Save enhanced analysis
        analysis_path = self.analysis_path / self.get_date_path() / f"{document_id}-enhanced.json"
        analysis_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(analysis_path, 'w') as f:
            json.dump(enhanced_analysis, f)
        
        # Register analysis
        analysis_id = await self.shared_service.register_analysis(
            document_id, 'legal-assistant', 'enhanced', str(analysis_path)
        )
        
        return {'analysis_id': analysis_id, 'result_path': str(analysis_path)}
```

---

## Docker Implementation

### Complete Docker Compose Configuration

```yaml
# docker-compose-shared.yml
version: '3.8'

services:
  # Contract Reviewer v2 - Integrated
  contract-reviewer-v2-integrated:
    build: .
    container_name: abs-contract-reviewer-v2-integrated
    ports:
      - "8082:8080"
    environment:
      # Application Configuration
      - APP_PORT=8080
      - HUB_GATEWAY_URL=http://hub-gateway:8081
      
      # Database Configuration
      - POSTGRES_URL=postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub
      
      # Vector Database Configuration
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      
      # Cache Configuration
      - REDIS_URL=redis://redis:6379/0
      
      # Shared Storage Configuration
      - SHARED_DATA_PATH=/abs-shared-data
      - FILE_STORAGE_PATH=/abs-shared-data/documents
      - ANALYSIS_PATH=/abs-shared-data/analyses/contract-reviewer
      - MAX_FILE_SIZE=100
      
      # Optional Configuration
      - ENABLE_COMPRESSION=true
      - LOG_LEVEL=INFO
    volumes:
      # Shared document storage
      - shared-document-hub:/abs-shared-data
      # App-specific storage
      - contract-reviewer-v2-logs:/data/logs
      - contract-reviewer-v2-cache:/data/cache
      # Static files (read-only)
      - ./static:/app/static:ro
    networks:
      - abs-net
    restart: unless-stopped
    depends_on:
      - postgresql
      - qdrant
      - redis
    labels:
      - "abs.service=contract-reviewer-v2-integrated"
      - "abs.shared-storage=true"
      - "abs.environment=production"

  # Legal Assistant
  legal-assistant:
    build: ../legal-assistant
    container_name: abs-legal-assistant
    ports:
      - "8083:8080"
    environment:
      - SHARED_DATA_PATH=/abs-shared-data
      - DOCUMENT_PATH=/abs-shared-data/documents
      - ANALYSIS_PATH=/abs-shared-data/analyses/legal-assistant
      - POSTGRES_URL=postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub
      - REDIS_URL=redis://redis:6379/0
    volumes:
      # Shared document storage
      - shared-document-hub:/abs-shared-data
      # App-specific storage
      - legal-assistant-logs:/data/logs
      - legal-assistant-cache:/data/cache
    networks:
      - abs-net
    restart: unless-stopped
    depends_on:
      - postgresql
      - redis
    labels:
      - "abs.service=legal-assistant"
      - "abs.shared-storage=true"
      - "abs.environment=production"

  # Onyx
  onyx:
    build: ../onyx
    container_name: abs-onyx
    ports:
      - "8084:8080"
    environment:
      - SHARED_DATA_PATH=/abs-shared-data
      - DOCUMENT_PATH=/abs-shared-data/documents
      - ANALYSIS_PATH=/abs-shared-data/analyses/onyx
      - POSTGRES_URL=postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub
      - REDIS_URL=redis://redis:6379/0
    volumes:
      # Shared document storage
      - shared-document-hub:/abs-shared-data
      # App-specific storage
      - onyx-logs:/data/logs
      - onyx-cache:/data/cache
    networks:
      - abs-net
    restart: unless-stopped
    depends_on:
      - postgresql
      - redis
    labels:
      - "abs.service=onyx"
      - "abs.shared-storage=true"
      - "abs.environment=production"

  # PostgreSQL Database (shared)
  postgresql:
    image: postgres:15
    container_name: document-hub-postgres
    restart: unless-stopped
    environment:
      - TZ=UTC
      - POSTGRES_DB=document_hub
      - POSTGRES_USER=hub_user
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./postgres-init:/docker-entrypoint-initdb.d:ro
    ports:
      - "5432:5432"
    networks:
      - abs-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hub_user -d document_hub"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    labels:
      - "abs.service=postgresql"
      - "abs.shared-storage=true"
      - "abs.environment=production"

  # Qdrant Vector Database (shared)
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant-storage:/qdrant/storage
    networks:
      - abs-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    labels:
      - "abs.service=qdrant"
      - "abs.shared-storage=true"
      - "abs.environment=production"

  # Redis Cache (shared)
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - abs-net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    labels:
      - "abs.service=redis"
      - "abs.shared-storage=true"
      - "abs.environment=production"

volumes:
  # Shared document storage for all apps
  shared-document-hub:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /abs-shared-data  # Host path for shared storage
    labels:
      - "abs.shared=true"
      - "abs.access=multi-app"
      - "abs.security=restricted"
  
  # App-specific volumes
  contract-reviewer-v2-logs:
    driver: local
  contract-reviewer-v2-cache:
    driver: local
  legal-assistant-logs:
    driver: local
  legal-assistant-cache:
    driver: local
  onyx-logs:
    driver: local
  onyx-cache:
    driver: local
  
  # Database volumes
  postgres-data:
    driver: local
  qdrant-storage:
    driver: local
  redis-data:
    driver: local

networks:
  abs-net:
    external: true
```

---

## Deployment Guide

### Quick Start Deployment

#### **Linux/macOS:**
```bash
# Clone repository
git clone <repository-url>
cd ABS/abs-ai-hub/apps/contract-reviewer-v2

# Create shared data directory
sudo mkdir -p /abs-shared-data/{documents,analyses,vectors,shared-db,cache}
sudo chown -R $USER:$USER /abs-shared-data

# Deploy all services
docker-compose -f docker-compose-shared.yml up -d

# Check health
curl http://localhost:8082/api/health
```

#### **Windows:**
```cmd
REM Clone repository
git clone <repository-url>
cd ABS\abs-ai-hub\apps\contract-reviewer-v2

REM Create shared data directory
mkdir C:\abs-shared-data\documents
mkdir C:\abs-shared-data\analyses
mkdir C:\abs-shared-data\vectors
mkdir C:\abs-shared-data\shared-db
mkdir C:\abs-shared-data\cache

REM Deploy all services
docker-compose -f docker-compose-shared.yml up -d

REM Check health
curl http://localhost:8082/api/health
```

### Environment Configuration

```bash
# Required Environment Variables
export SHARED_DATA_PATH="/abs-shared-data"
export POSTGRES_URL="postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub"
export QDRANT_HOST="qdrant"
export QDRANT_PORT="6333"
export REDIS_URL="redis://redis:6379/0"

# Optional Configuration
export ENABLE_COMPRESSION=true
export LOG_LEVEL=INFO
export MAX_FILE_SIZE=100
```

### Service URLs

- **Contract Reviewer v2**: http://localhost:8082
- **Legal Assistant**: http://localhost:8083
- **Onyx**: http://localhost:8084
- **PostgreSQL**: localhost:5432
- **Qdrant**: http://localhost:6333
- **Redis**: localhost:6379

---

## Cross-App Data Sharing

### Shared Vector Storage

```python
# Shared vector service for cross-app similarity
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

class SharedVectorService:
    def __init__(self):
        self.qdrant_client = QdrantClient("qdrant", port=6333)
        self.vector_path = Path("/abs-shared-data/vectors")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def store_document_vectors(self, document_id: str, chunks: List[dict]):
        """Store document vectors accessible by all apps"""
        points = []
        for i, chunk in enumerate(chunks):
            embedding = self.embedding_model.encode(chunk['text']).tolist()
            points.append(PointStruct(
                id=f"{document_id}-chunk-{i}",
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "chunk_text": chunk['text'],
                    "chunk_type": chunk['type'],
                    "app_source": "shared",  # Available to all apps
                    "client_id": chunk.get('client_id'),
                    "matter_type": chunk.get('matter_type'),
                    "created_at": datetime.now().isoformat()
                }
            ))
        
        self.qdrant_client.upsert(
            collection_name="shared_document_chunks",
            points=points
        )
    
    def find_similar_documents(self, query_text: str, app_name: str = None) -> List[dict]:
        """Find similar documents across all apps"""
        query_embedding = self.embedding_model.encode(query_text).tolist()
        
        filter_conditions = {"app_source": "shared"}
        if app_name:
            filter_conditions["accessible_by"] = app_name
        
        results = self.qdrant_client.search(
            collection_name="shared_document_chunks",
            query_vector=query_embedding,
            query_filter=filter_conditions,
            limit=20
        )
        
        return results
```

### Event-Driven Synchronization

```python
# Cross-app notification system
import redis
import json
from datetime import datetime

class CrossAppNotifier:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
    
    def notify_document_uploaded(self, document_id: str, app_name: str, metadata: dict):
        """Notify other apps about document upload"""
        message = {
            "event": "document_uploaded",
            "document_id": document_id,
            "app": app_name,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        # Publish to shared channel
        self.redis_client.publish("shared_documents", json.dumps(message))
    
    def notify_analysis_completed(self, document_id: str, app_name: str, analysis_type: str):
        """Notify other apps about analysis completion"""
        message = {
            "event": "analysis_completed",
            "document_id": document_id,
            "app": app_name,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat()
        }
        
        self.redis_client.publish("shared_analyses", json.dumps(message))
    
    def listen_for_events(self, app_name: str):
        """Listen for events from other apps"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe("shared_documents", "shared_analyses")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                if data['app'] != app_name:  # Don't process own events
                    self.handle_shared_event(data)
    
    def handle_shared_event(self, data: dict):
        """Handle events from other apps"""
        if data['event'] == 'document_uploaded':
            self.on_document_uploaded(data)
        elif data['event'] == 'analysis_completed':
            self.on_analysis_completed(data)
```

---

## Security & Access Control

### Volume Access Control

```yaml
# Use read-only mounts where appropriate
volumes:
  - shared-document-hub:/abs-shared-data:rw  # Read-write for main apps
  - shared-document-hub:/abs-shared-data:ro  # Read-only for reporting apps
```

### User Permissions

```dockerfile
# In Dockerfile, create shared user
RUN groupadd -r sharedgroup && useradd -r -g sharedgroup shareduser
RUN chown -R shareduser:sharedgroup /abs-shared-data
USER shareduser
```

### Volume Labels

```yaml
volumes:
  shared-document-hub:
    driver: local
    labels:
      - "abs.shared=true"
      - "abs.access=multi-app"
      - "abs.security=restricted"
```

### Database Access Control

```sql
-- Create app-specific users
CREATE USER contract_reviewer_app WITH PASSWORD 'secure_password';
CREATE USER legal_assistant_app WITH PASSWORD 'secure_password';
CREATE USER onyx_app WITH PASSWORD 'secure_password';

-- Grant appropriate permissions
GRANT SELECT, INSERT, UPDATE ON shared_documents TO contract_reviewer_app;
GRANT SELECT, INSERT, UPDATE ON app_analyses TO contract_reviewer_app;
GRANT SELECT, INSERT ON app_document_access TO contract_reviewer_app;

-- Similar grants for other apps...
```

---

## Monitoring & Maintenance

### Volume Usage Monitoring

```bash
# Check volume usage
docker system df -v

# Monitor specific shared volume
docker volume inspect shared-document-hub

# Check volume health
docker exec container_name du -sh /abs-shared-data
```

### Cross-App Data Integrity

```python
# Data integrity checker
class SharedDataIntegrityChecker:
    def __init__(self):
        self.shared_service = SharedDocumentService()
    
    async def check_data_consistency(self):
        """Check data consistency across apps"""
        issues = []
        
        # Check for orphaned files
        orphaned_files = await self.find_orphaned_files()
        if orphaned_files:
            issues.append(f"Found {len(orphaned_files)} orphaned files")
        
        # Check for duplicate documents
        duplicates = await self.find_duplicate_documents()
        if duplicates:
            issues.append(f"Found {len(duplicates)} duplicate documents")
        
        # Check metadata consistency
        metadata_issues = await self.check_metadata_consistency()
        if metadata_issues:
            issues.extend(metadata_issues)
        
        return issues
    
    async def find_orphaned_files(self):
        """Find files without database entries"""
        orphaned = []
        for file_path in Path("/abs-shared-data/documents").rglob("*"):
            if file_path.is_file():
                # Check if file exists in database
                exists = await self.shared_service.check_file_in_db(file_path)
                if not exists:
                    orphaned.append(file_path)
        return orphaned
```

### Backup Strategy

```bash
#!/bin/bash
# Regular backup of shared volumes
BACKUP_DIR="/backups/shared-volumes"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup shared document hub
docker run --rm \
  -v shared-document-hub:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/shared-documents-$DATE.tar.gz -C /data .

# Backup PostgreSQL data
docker exec document-hub-postgres pg_dump -U hub_user document_hub > $BACKUP_DIR/postgres-$DATE.sql

# Backup Redis data
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb $BACKUP_DIR/redis-$DATE.rdb
```

---

## Migration Strategy

### Phase 1: Setup Shared Storage
1. Create `/abs-shared-data` directory structure
2. Implement `SharedDocumentService`
3. Create shared database schema
4. Deploy Docker volumes

### Phase 2: Migrate Existing Documents
1. Move existing documents to shared storage
2. Update app configurations to use shared paths
3. Register existing documents in shared database
4. Test cross-app access

### Phase 3: Enable Cross-App Access
1. Implement app permission system
2. Enable cross-app document discovery
3. Add shared vector storage
4. Test cross-app analysis building

### Phase 4: Advanced Features
1. Cross-app analysis building
2. Unified search across all apps
3. Portfolio-wide reporting and analytics
4. Performance optimization

---

## Benefits Summary

### For Individual Apps
- **✅ No Duplication**: Each document stored once
- **✅ Cross-App Access**: Access documents from other apps
- **✅ Shared Analysis**: Build upon other apps' analysis results
- **✅ Unified Search**: Search across all app documents

### For the Ecosystem
- **✅ Centralized Management**: Single source of truth for documents
- **✅ Efficient Storage**: No duplicate files
- **✅ Cross-App Insights**: Discover patterns across all apps
- **✅ Unified User Experience**: Consistent document access

### For Legal Organizations
- **✅ Portfolio View**: See all documents across all tools
- **✅ Cross-Tool Analysis**: Compare insights from different apps
- **✅ Efficient Workflows**: Seamless handoff between tools
- **✅ Comprehensive Reporting**: Reports across entire document portfolio

---

This comprehensive guide provides everything needed to implement a centralized document hub architecture with Docker volume sharing, enabling efficient multi-app document management and collaboration across the entire ABS ecosystem.
