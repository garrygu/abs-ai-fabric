# Shared Document Storage Architecture for Multi-App Ecosystem

## Overview
This document outlines the recommended storage architecture for a multi-app ecosystem where multiple applications need to access the same documents, either partially or fully.

## Current Problem
- Multiple apps (contract-reviewer, legal-assistant, onyx, etc.) need access to same documents
- Duplicate storage wastes disk space and creates sync issues
- No centralized document management
- Apps can't share analysis results or insights

## Recommended Solution: Centralized Document Hub

### 1. Shared Document Storage Structure

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

### 2. Document Registry System

#### Central Document Registry (PostgreSQL)
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
```

### 3. Shared Document Service

#### Document Service API
```python
# Shared document service
class SharedDocumentService:
    def __init__(self, base_path="/abs-shared-data"):
        self.base_path = Path(base_path)
        self.postgres_pool = asyncpg.create_pool("postgresql://user:pass@localhost/document_hub")
        self.redis = redis.from_url("redis://localhost:6379/0")
        self.raw_path = self.base_path / "documents" / "raw"
        self.processed_path = self.base_path / "documents" / "processed"
    
    def register_document(self, file_path: Path, metadata: dict) -> str:
        """Register a new document in the shared system"""
        # Generate document ID and hash
        document_id = str(uuid.uuid4())
        file_hash = self.get_file_hash(file_path)
        
        # Check for duplicates
        existing = self.find_by_hash(file_hash)
        if existing:
            return existing['document_id']
        
        # Move file to shared storage
        organized_path = self.organize_file_path(file_path, metadata)
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
        
        return document_id
    
    async def get_document_path(self, document_id: str) -> Path:
        """Get the file path for a document"""
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
        
        return analysis_id
```

### 4. App Integration Strategy

#### Contract Reviewer Integration
```python
# In contract-reviewer app.py
class ContractReviewerService:
    def __init__(self):
        self.shared_service = SharedDocumentService()
        self.analysis_path = Path("/abs-shared-data/analyses/contract-reviewer")
    
    async def upload_document(self, file: UploadFile) -> dict:
        # Save to temporary location first
        temp_path = self.save_temp_file(file)
        
        # Register with shared service
        document_id = self.shared_service.register_document(
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
        self.shared_service.grant_app_access(
            'contract-reviewer', document_id, 'analyze'
        )
        
        return {'document_id': document_id}
    
    async def analyze_document(self, document_id: str) -> dict:
        # Get document path from shared service
        doc_path = self.shared_service.get_document_path(document_id)
        
        # Perform analysis
        analysis_result = await self.run_analysis(doc_path)
        
        # Save analysis results
        analysis_path = self.analysis_path / self.get_date_path() / f"{document_id}-analysis.json"
        analysis_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(analysis_path, 'w') as f:
            json.dump(analysis_result, f)
        
        # Register analysis with shared service
        analysis_id = self.shared_service.register_analysis(
            document_id, 'contract-reviewer', 'comprehensive', str(analysis_path)
        )
        
        return {'analysis_id': analysis_id, 'result_path': str(analysis_path)}
```

#### Legal Assistant Integration
```python
# In legal-assistant app.py
class LegalAssistantService:
    def __init__(self):
        self.shared_service = SharedDocumentService()
        self.analysis_path = Path("/abs-shared-data/analyses/legal-assistant")
    
    async def get_available_documents(self, client_id: str = None) -> List[dict]:
        """Get documents available for legal assistant"""
        return self.shared_service.get_documents_for_app(
            'legal-assistant', 
            {'client_id': client_id} if client_id else None
        )
    
    async def analyze_document(self, document_id: str) -> dict:
        # Check if contract-reviewer already analyzed this document
        existing_analysis = self.shared_service.get_existing_analysis(
            document_id, 'contract-reviewer'
        )
        
        if existing_analysis:
            # Use existing analysis as base
            base_analysis = self.load_analysis(existing_analysis['result_path'])
            enhanced_analysis = await self.enhance_analysis(base_analysis)
        else:
            # Perform fresh analysis
            doc_path = self.shared_service.get_document_path(document_id)
            enhanced_analysis = await self.run_analysis(doc_path)
        
        # Save enhanced analysis
        analysis_path = self.analysis_path / self.get_date_path() / f"{document_id}-enhanced.json"
        analysis_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(analysis_path, 'w') as f:
            json.dump(enhanced_analysis, f)
        
        # Register analysis
        analysis_id = self.shared_service.register_analysis(
            document_id, 'legal-assistant', 'enhanced', str(analysis_path)
        )
        
        return {'analysis_id': analysis_id, 'result_path': str(analysis_path)}
```

### 5. Cross-App Data Sharing

#### Shared Vector Storage
```python
# Shared vector service for cross-app similarity
class SharedVectorService:
    def __init__(self):
        self.qdrant_client = QdrantClient("localhost", port=6333)
        self.vector_path = Path("/abs-shared-data/vectors")
    
    def store_document_vectors(self, document_id: str, chunks: List[dict]):
        """Store document vectors accessible by all apps"""
        points = []
        for i, chunk in enumerate(chunks):
            embedding = self.get_embedding(chunk['text'])
            points.append(PointStruct(
                id=f"{document_id}-chunk-{i}",
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "chunk_text": chunk['text'],
                    "chunk_type": chunk['type'],
                    "app_source": "shared",  # Available to all apps
                    "client_id": chunk.get('client_id'),
                    "matter_type": chunk.get('matter_type')
                }
            ))
        
        self.qdrant_client.upsert(
            collection_name="shared_document_chunks",
            points=points
        )
    
    def find_similar_documents(self, query_text: str, app_name: str = None) -> List[dict]:
        """Find similar documents across all apps"""
        query_embedding = self.get_embedding(query_text)
        
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

### 6. Docker Compose Integration

#### Shared Storage Volume
```yaml
# docker-compose.yml
version: '3.8'
services:
  contract-reviewer:
    image: contract-reviewer-v2
    volumes:
      - shared-data:/abs-shared-data
      - shared-data:/app/shared-data  # Mount as /app/shared-data in container
    environment:
      - SHARED_DATA_PATH=/app/shared-data
      - SHARED_DB_PATH=/app/shared-data/shared-db
  
  legal-assistant:
    image: legal-assistant
    volumes:
      - shared-data:/abs-shared-data
      - shared-data:/app/shared-data
    environment:
      - SHARED_DATA_PATH=/app/shared-data
      - SHARED_DB_PATH=/app/shared-data/shared-db
  
  onyx:
    image: onyx
    volumes:
      - shared-data:/abs-shared-data
      - shared-data:/app/shared-data
    environment:
      - SHARED_DATA_PATH=/app/shared-data
      - SHARED_DB_PATH=/app/shared-data/shared-db

volumes:
  shared-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /abs-shared-data  # Host path
```

### 7. Benefits of Shared Storage

#### For Individual Apps
- **No Duplication**: Each document stored once
- **Cross-App Access**: Access documents from other apps
- **Shared Analysis**: Build upon other apps' analysis results
- **Unified Search**: Search across all app documents

#### For the Ecosystem
- **Centralized Management**: Single source of truth for documents
- **Efficient Storage**: No duplicate files
- **Cross-App Insights**: Discover patterns across all apps
- **Unified User Experience**: Consistent document access

#### For Legal Organizations
- **Portfolio View**: See all documents across all tools
- **Cross-Tool Analysis**: Compare insights from different apps
- **Efficient Workflows**: Seamless handoff between tools
- **Comprehensive Reporting**: Reports across entire document portfolio

### 8. Migration Strategy

#### Phase 1: Setup Shared Storage
1. Create `/abs-shared-data` directory structure
2. Implement `SharedDocumentService`
3. Create shared database schema

#### Phase 2: Migrate Existing Documents
1. Move existing documents to shared storage
2. Update app configurations to use shared paths
3. Register existing documents in shared database

#### Phase 3: Enable Cross-App Access
1. Implement app permission system
2. Enable cross-app document discovery
3. Add shared vector storage

#### Phase 4: Advanced Features
1. Cross-app analysis building
2. Unified search across all apps
3. Portfolio-wide reporting and analytics

This shared storage architecture ensures efficient document management across the entire ABS ecosystem while maintaining app-specific functionality and analysis capabilities.
