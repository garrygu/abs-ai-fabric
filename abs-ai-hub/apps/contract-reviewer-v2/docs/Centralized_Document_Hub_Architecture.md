# Centralized Document Hub Architecture

## Overview
The Centralized Document Hub Architecture is a comprehensive document management system designed for multi-app ecosystems where multiple applications need to access, analyze, and share the same documents. This architecture provides a single source of truth for all document-related operations across the entire ABS ecosystem.

## Architecture Principles

### 1. Single Source of Truth
- **One Document, Multiple Access Points**: Each document is stored once but accessible by multiple applications
- **Centralized Metadata**: All document information stored in a central registry
- **Unified Search**: Search across all documents regardless of which app created them
- **Consistent Data Model**: Standardized document structure across all applications

### 2. App-Agnostic Design
- **No App Ownership**: Documents belong to the hub, not individual applications
- **Cross-App Analysis**: Applications can build upon each other's analysis results
- **Shared Intelligence**: Vector embeddings and insights shared across all apps
- **Unified User Experience**: Consistent document access regardless of the app

### 3. Scalable and Extensible
- **Horizontal Scaling**: Add new applications without changing existing ones
- **Data Growth**: Handle increasing document volumes efficiently
- **Feature Extensibility**: Add new analysis types and capabilities
- **Performance Optimization**: Efficient storage and retrieval mechanisms

## Core Components

### 1. Document Registry Service

#### Central Document Database
```sql
-- Core document registry
CREATE TABLE documents (
    document_id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),      -- Original name when uploaded
    file_hash VARCHAR(64) UNIQUE,      -- SHA-256 for deduplication
    file_path TEXT NOT NULL,           -- Path to raw file in shared storage
    file_size BIGINT NOT NULL,
    file_type VARCHAR(10) NOT NULL,    -- PDF, DOCX, TXT, etc.
    mime_type VARCHAR(100),            -- application/pdf, etc.
    
    -- Document metadata
    title VARCHAR(500),                -- Extracted or user-provided title
    description TEXT,                  -- Document description
    language VARCHAR(10) DEFAULT 'en', -- Document language
    page_count INTEGER,                -- Number of pages (for PDFs)
    word_count INTEGER,                -- Approximate word count
    
    -- Business context
    client_id VARCHAR(100),            -- Client/customer identifier
    case_number VARCHAR(100),          -- Legal case reference
    matter_type VARCHAR(50),           -- Contract, NDA, Agreement, etc.
    document_category VARCHAR(50),     -- Legal, Financial, Technical, etc.
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    
    -- Access control
    access_level VARCHAR(20) DEFAULT 'private', -- private, shared, public
    confidentiality_level VARCHAR(20) DEFAULT 'internal', -- public, internal, confidential, secret
    
    -- Audit fields
    uploaded_by VARCHAR(100) NOT NULL,
    upload_date TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP,
    last_modified TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    
    -- Status tracking
    processing_status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    analysis_status VARCHAR(20) DEFAULT 'none',     -- none, partial, complete
    validation_status VARCHAR(20) DEFAULT 'pending', -- pending, valid, invalid
    
    -- Additional metadata (JSON)
    custom_metadata JSONB,             -- App-specific metadata
    tags TEXT[],                      -- Searchable tags
    keywords TEXT[]                   -- Extracted keywords
);

-- Document versions and history
CREATE TABLE document_versions (
    version_id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(document_id),
    version_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    change_description TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    file_size BIGINT,
    
    UNIQUE(document_id, version_number)
);

-- Document relationships
CREATE TABLE document_relationships (
    relationship_id UUID PRIMARY KEY,
    source_document_id UUID REFERENCES documents(document_id),
    target_document_id UUID REFERENCES documents(document_id),
    relationship_type VARCHAR(50) NOT NULL, -- parent, child, related, supersedes, amends
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    
    UNIQUE(source_document_id, target_document_id, relationship_type)
);
```

#### Document Processing Pipeline
```sql
-- Document processing stages
CREATE TABLE document_processing_stages (
    stage_id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(document_id),
    stage_name VARCHAR(50) NOT NULL,  -- upload, extract_text, chunk, embed, analyze
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    processing_time_seconds INTEGER,
    metadata JSONB                     -- Stage-specific data
);

-- Text extraction results
CREATE TABLE document_text (
    text_id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(document_id),
    text_content TEXT NOT NULL,
    extraction_method VARCHAR(50),    -- ocr, native, hybrid
    confidence_score FLOAT,           -- OCR confidence if applicable
    language_detected VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document chunks for vector storage
CREATE TABLE document_chunks (
    chunk_id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(document_id),
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_type VARCHAR(50),           -- paragraph, section, clause, page
    start_position INTEGER,           -- Character position in original text
    end_position INTEGER,
    word_count INTEGER,
    page_number INTEGER,              -- For PDFs
    section_title VARCHAR(200),       -- Extracted section heading
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(document_id, chunk_index)
);
```

### 2. Application Integration Layer

#### App Registration and Permissions
```sql
-- Registered applications
CREATE TABLE applications (
    app_id UUID PRIMARY KEY,
    app_name VARCHAR(50) UNIQUE NOT NULL, -- contract-reviewer, legal-assistant, onyx
    app_version VARCHAR(20),
    description TEXT,
    capabilities TEXT[],              -- Array of capabilities
    api_endpoint VARCHAR(255),        -- Internal API endpoint
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, deprecated
    registered_at TIMESTAMP DEFAULT NOW(),
    last_heartbeat TIMESTAMP,
    configuration JSONB               -- App-specific configuration
);

-- App permissions for documents
CREATE TABLE app_document_permissions (
    permission_id UUID PRIMARY KEY,
    app_id UUID REFERENCES applications(app_id),
    document_id UUID REFERENCES documents(document_id),
    permission_type VARCHAR(20) NOT NULL, -- read, analyze, modify, delete
    granted_at TIMESTAMP DEFAULT NOW(),
    granted_by VARCHAR(100),
    expires_at TIMESTAMP,            -- Optional expiration
    conditions JSONB,                -- Additional conditions
    
    UNIQUE(app_id, document_id, permission_type)
);

-- App-specific analysis results
CREATE TABLE app_analyses (
    analysis_id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(document_id),
    app_id UUID REFERENCES applications(app_id),
    analysis_type VARCHAR(50) NOT NULL, -- comprehensive, quick, risk-focused, etc.
    analysis_version VARCHAR(20),     -- Version of analysis algorithm
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    
    -- Analysis metadata
    model_used VARCHAR(100),         -- AI model used
    confidence_score FLOAT,           -- Overall confidence
    processing_time_seconds INTEGER,
    tokens_used INTEGER,             -- AI tokens consumed
    cost_usd DECIMAL(10,4),          -- Analysis cost
    
    -- Results storage
    result_path TEXT,                -- Path to analysis results file
    summary_path TEXT,               -- Path to summary file
    report_path TEXT,                -- Path to generated report
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Analysis metadata
    analysis_metadata JSONB,         -- Analysis-specific metadata
    quality_metrics JSONB            -- Quality assessment metrics
);
```

### 3. Shared Vector Storage System

#### Vector Collections Management
```python
# Qdrant collections for shared document intelligence
class SharedVectorCollections:
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        
        # Collection configurations
        self.collections = {
            "document_chunks": {
                "vector_size": 768,  # Embedding dimension
                "distance": Distance.COSINE,
                "description": "Document text chunks for semantic search"
            },
            "analysis_insights": {
                "vector_size": 768,
                "distance": Distance.COSINE,
                "description": "Analysis insights and recommendations"
            },
            "document_similarities": {
                "vector_size": 768,
                "distance": Distance.COSINE,
                "description": "Overall document similarity vectors"
            },
            "cross_app_patterns": {
                "vector_size": 768,
                "distance": Distance.COSINE,
                "description": "Patterns discovered across applications"
            }
        }
    
    def initialize_collections(self):
        """Initialize all vector collections"""
        for collection_name, config in self.collections.items():
            try:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=config["vector_size"],
                        distance=config["distance"]
                    )
                )
                print(f"✓ Created collection: {collection_name}")
            except Exception as e:
                print(f"Collection {collection_name} may already exist: {e}")
    
    def store_document_chunks(self, document_id: str, chunks: List[dict]):
        """Store document chunks with cross-app accessibility"""
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
                    "chunk_index": i,
                    "app_source": "shared",  # Available to all apps
                    "client_id": chunk.get('client_id'),
                    "matter_type": chunk.get('matter_type'),
                    "document_category": chunk.get('document_category'),
                    "created_at": datetime.now().isoformat(),
                    "access_level": "shared"
                }
            ))
        
        self.client.upsert(
            collection_name="document_chunks",
            points=points
        )
    
    def store_analysis_insights(self, analysis_id: str, insights: List[dict]):
        """Store analysis insights for cross-app discovery"""
        points = []
        for i, insight in enumerate(insights):
            embedding = self.get_embedding(insight['text'])
            points.append(PointStruct(
                id=f"{analysis_id}-insight-{i}",
                vector=embedding,
                payload={
                    "analysis_id": analysis_id,
                    "insight_text": insight['text'],
                    "insight_type": insight['type'],
                    "severity": insight.get('severity'),
                    "category": insight.get('category'),
                    "app_source": insight.get('app_name'),
                    "document_id": insight.get('document_id'),
                    "confidence": insight.get('confidence'),
                    "created_at": datetime.now().isoformat()
                }
            ))
        
        self.client.upsert(
            collection_name="analysis_insights",
            points=points
        )
```

### 4. Cross-App Analysis Engine

#### Analysis Orchestration Service
```python
class CrossAppAnalysisEngine:
    def __init__(self, document_service, vector_service):
        self.document_service = document_service
        self.vector_service = vector_service
        self.analysis_pipeline = AnalysisPipeline()
    
    async def orchestrate_analysis(self, document_id: str, analysis_type: str = "comprehensive"):
        """Orchestrate analysis across multiple applications"""
        
        # Get document information
        document = await self.document_service.get_document(document_id)
        
        # Check for existing analyses
        existing_analyses = await self.get_existing_analyses(document_id)
        
        # Determine analysis strategy
        analysis_plan = self.create_analysis_plan(document, existing_analyses, analysis_type)
        
        # Execute analysis plan
        results = []
        for step in analysis_plan:
            result = await self.execute_analysis_step(step)
            results.append(result)
            
            # Store intermediate results
            await self.store_analysis_result(result)
        
        # Generate cross-app insights
        cross_app_insights = await self.generate_cross_app_insights(results)
        
        # Store final results
        final_result = await self.consolidate_results(results, cross_app_insights)
        
        return final_result
    
    def create_analysis_plan(self, document: dict, existing_analyses: List[dict], analysis_type: str) -> List[dict]:
        """Create analysis plan based on document and existing analyses"""
        plan = []
        
        # Base analysis steps
        if not existing_analyses:
            plan.extend([
                {"app": "contract-reviewer", "type": "comprehensive", "priority": 1},
                {"app": "legal-assistant", "type": "enhanced", "priority": 2},
                {"app": "onyx", "type": "additional_insights", "priority": 3}
            ])
        else:
            # Build upon existing analyses
            for analysis in existing_analyses:
                if analysis['app_name'] == 'contract-reviewer':
                    plan.append({"app": "legal-assistant", "type": "enhancement", "priority": 1})
                elif analysis['app_name'] == 'legal-assistant':
                    plan.append({"app": "onyx", "type": "supplement", "priority": 2})
        
        return plan
    
    async def generate_cross_app_insights(self, analysis_results: List[dict]) -> List[dict]:
        """Generate insights by comparing analyses across apps"""
        insights = []
        
        # Compare risk assessments
        risk_insights = await self.compare_risk_assessments(analysis_results)
        insights.extend(risk_insights)
        
        # Identify consensus patterns
        consensus_insights = await self.identify_consensus_patterns(analysis_results)
        insights.extend(consensus_insights)
        
        # Find conflicting assessments
        conflict_insights = await self.identify_conflicts(analysis_results)
        insights.extend(conflict_insights)
        
        return insights
```

### 5. Unified Search and Discovery

#### Cross-App Search Service
```python
class UnifiedSearchService:
    def __init__(self, document_service, vector_service, analysis_service):
        self.document_service = document_service
        self.vector_service = vector_service
        self.analysis_service = analysis_service
    
    async def search_documents(self, query: str, filters: dict = None, user_context: dict = None):
        """Unified search across all documents and analyses"""
        
        # Parse query for different search types
        search_types = self.parse_query(query)
        
        results = {
            "documents": [],
            "analyses": [],
            "insights": [],
            "similar_documents": []
        }
        
        # Metadata search (PostgreSQL)
        if "metadata" in search_types:
            metadata_results = await self.search_metadata(query, filters)
            results["documents"].extend(metadata_results)
        
        # Semantic search (Qdrant)
        if "semantic" in search_types:
            semantic_results = await self.search_semantic(query, filters)
            results["documents"].extend(semantic_results)
        
        # Analysis search
        if "analysis" in search_types:
            analysis_results = await self.search_analyses(query, filters)
            results["analyses"].extend(analysis_results)
        
        # Insight search
        if "insights" in search_types:
            insight_results = await self.search_insights(query, filters)
            results["insights"].extend(insight_results)
        
        # Similar document discovery
        if "similar" in search_types:
            similar_results = await self.find_similar_documents(query, filters)
            results["similar_documents"].extend(similar_results)
        
        # Rank and deduplicate results
        ranked_results = await self.rank_results(results, user_context)
        
        return ranked_results
    
    async def search_semantic(self, query: str, filters: dict = None):
        """Semantic search across document chunks"""
        query_embedding = await self.get_embedding(query)
        
        # Build filter conditions
        filter_conditions = {"access_level": "shared"}
        if filters:
            if 'client_id' in filters:
                filter_conditions["client_id"] = filters['client_id']
            if 'matter_type' in filters:
                filter_conditions["matter_type"] = filters['matter_type']
            if 'document_category' in filters:
                filter_conditions["document_category"] = filters['document_category']
        
        # Search document chunks
        chunk_results = self.vector_service.client.search(
            collection_name="document_chunks",
            query_vector=query_embedding,
            query_filter=filter_conditions,
            limit=50
        )
        
        # Group by document and get full document info
        document_results = []
        seen_documents = set()
        
        for result in chunk_results:
            doc_id = result.payload['document_id']
            if doc_id not in seen_documents:
                document_info = await self.document_service.get_document(doc_id)
                document_info['similarity_score'] = result.score
                document_info['matching_chunk'] = result.payload['chunk_text']
                document_results.append(document_info)
                seen_documents.add(doc_id)
        
        return document_results
```

### 6. Document Lifecycle Management

#### Lifecycle States and Transitions
```python
class DocumentLifecycleManager:
    def __init__(self, document_service):
        self.document_service = document_service
        self.lifecycle_states = {
            "uploaded": ["processing", "failed"],
            "processing": ["processed", "failed"],
            "processed": ["analyzing", "archived"],
            "analyzing": ["analyzed", "failed"],
            "analyzed": ["active", "archived"],
            "active": ["archived", "deprecated"],
            "archived": ["active", "deleted"],
            "deprecated": ["archived", "deleted"],
            "failed": ["uploaded", "deleted"],
            "deleted": []  # Terminal state
        }
    
    async def transition_document(self, document_id: str, new_state: str, context: dict = None):
        """Transition document to new lifecycle state"""
        
        current_document = await self.document_service.get_document(document_id)
        current_state = current_document['processing_status']
        
        # Validate transition
        if new_state not in self.lifecycle_states.get(current_state, []):
            raise ValueError(f"Invalid transition from {current_state} to {new_state}")
        
        # Execute state-specific actions
        if new_state == "processing":
            await self.start_processing(document_id, context)
        elif new_state == "analyzing":
            await self.start_analysis(document_id, context)
        elif new_state == "archived":
            await self.archive_document(document_id, context)
        elif new_state == "deleted":
            await self.delete_document(document_id, context)
        
        # Update document state
        await self.document_service.update_document_status(
            document_id, 
            new_state, 
            context
        )
        
        # Log state transition
        await self.log_state_transition(document_id, current_state, new_state, context)
    
    async def archive_document(self, document_id: str, context: dict = None):
        """Archive document and move to long-term storage"""
        
        # Get document info
        document = await self.document_service.get_document(document_id)
        
        # Create archive package
        archive_package = {
            "document_id": document_id,
            "archived_at": datetime.now().isoformat(),
            "archived_by": context.get('user_id'),
            "archive_reason": context.get('reason', 'routine_archival'),
            "original_path": document['file_path'],
            "archive_path": self.get_archive_path(document),
            "metadata": document,
            "analyses": await self.get_all_analyses(document_id)
        }
        
        # Move files to archive location
        await self.move_to_archive(document, archive_package)
        
        # Update document status
        await self.document_service.update_document_status(
            document_id, 
            "archived",
            {"archive_package": archive_package}
        )
```

### 7. Security and Access Control

#### Multi-Level Security Model
```python
class SecurityManager:
    def __init__(self, document_service, user_service):
        self.document_service = document_service
        self.user_service = user_service
        self.access_control = AccessControlEngine()
    
    async def check_document_access(self, user_id: str, document_id: str, action: str) -> bool:
        """Check if user can perform action on document"""
        
        # Get user information
        user = await self.user_service.get_user(user_id)
        
        # Get document information
        document = await self.document_service.get_document(document_id)
        
        # Check access level
        if document['access_level'] == 'public':
            return True
        
        # Check user permissions
        if document['access_level'] == 'private':
            return await self.check_private_access(user, document, action)
        
        if document['access_level'] == 'shared':
            return await self.check_shared_access(user, document, action)
        
        return False
    
    async def check_private_access(self, user: dict, document: dict, action: str) -> bool:
        """Check access to private documents"""
        
        # Owner has full access
        if user['user_id'] == document['uploaded_by']:
            return True
        
        # Check explicit permissions
        permissions = await self.get_document_permissions(document['document_id'])
        for permission in permissions:
            if (permission['user_id'] == user['user_id'] and 
                action in permission['allowed_actions']):
                return True
        
        # Check role-based access
        if await self.check_role_access(user, document, action):
            return True
        
        return False
    
    async def audit_document_access(self, user_id: str, document_id: str, action: str, result: bool):
        """Log document access for audit purposes"""
        
        audit_log = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "document_id": document_id,
            "action": action,
            "result": result,
            "ip_address": self.get_client_ip(),
            "user_agent": self.get_user_agent(),
            "session_id": self.get_session_id()
        }
        
        await self.document_service.log_audit_event(audit_log)
```

## Data Flow Architecture

### Document Upload and Processing Flow
```mermaid
graph TD
    A[Document Upload] --> B[Validate File]
    B --> C[Generate Hash]
    C --> D{Duplicate Check}
    D -->|New| E[Store in Shared Storage]
    D -->|Duplicate| F[Return Existing Document ID]
    E --> G[Register in Document Registry]
    G --> H[Extract Text]
    H --> I[Create Chunks]
    I --> J[Generate Embeddings]
    J --> K[Store in Vector DB]
    K --> L[Update Processing Status]
    L --> M[Notify Applications]
```

### Cross-App Analysis Flow
```mermaid
graph TD
    A[Analysis Request] --> B[Check Existing Analyses]
    B --> C{Analysis Strategy}
    C -->|Fresh| D[Run Primary Analysis]
    C -->|Enhance| E[Build on Existing]
    D --> F[Store Results]
    E --> F
    F --> G[Generate Cross-App Insights]
    G --> H[Update Vector Storage]
    H --> I[Notify Other Apps]
    I --> J[Update Document Status]
```

### Search and Discovery Flow
```mermaid
graph TD
    A[Search Query] --> B[Parse Query Type]
    B --> C[Metadata Search]
    B --> D[Semantic Search]
    B --> E[Analysis Search]
    C --> F[Merge Results]
    D --> F
    E --> F
    F --> G[Rank Results]
    G --> H[Apply Filters]
    H --> I[Return Results]
```

## Performance Optimization

### Caching Strategy
```python
class DocumentHubCache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = {
            "document_metadata": 3600,      # 1 hour
            "analysis_results": 1800,        # 30 minutes
            "search_results": 600,           # 10 minutes
            "user_permissions": 1800,        # 30 minutes
            "vector_embeddings": 7200        # 2 hours
        }
    
    async def get_cached_document(self, document_id: str) -> dict:
        """Get cached document metadata"""
        cache_key = f"document:{document_id}"
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        # Cache miss - fetch from database
        document = await self.document_service.get_document(document_id)
        
        # Cache the result
        await self.redis.setex(
            cache_key,
            self.cache_ttl["document_metadata"],
            json.dumps(document)
        )
        
        return document
```

### Indexing Strategy
```sql
-- Database indexes for optimal performance
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
```

## Monitoring and Observability

### Health Monitoring
```python
class DocumentHubHealthMonitor:
    def __init__(self, document_service, vector_service, file_service):
        self.document_service = document_service
        self.vector_service = vector_service
        self.file_service = file_service
    
    async def check_health(self) -> dict:
        """Comprehensive health check"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check database connectivity
        try:
            await self.document_service.health_check()
            health_status["components"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["database"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check vector database
        try:
            await self.vector_service.health_check()
            health_status["components"]["vector_db"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["vector_db"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check file storage
        try:
            await self.file_service.health_check()
            health_status["components"]["file_storage"] = {"status": "healthy"}
        except Exception as e:
            health_status["components"]["file_storage"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        return health_status
```

## Deployment Architecture

### Microservices Deployment
```yaml
# docker-compose.yml for Document Hub
version: '3.8'
services:
  document-hub-core:
    image: document-hub-core:latest
    environment:
      - DATABASE_URL=postgresql://hub:password@postgres:5432/document_hub
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - SHARED_STORAGE_PATH=/abs-shared-data
    volumes:
      - shared-data:/abs-shared-data
    depends_on:
      - postgres
      - redis
      - qdrant
  
  document-hub-api:
    image: document-hub-api:latest
    ports:
      - "8080:8080"
    environment:
      - CORE_SERVICE_URL=http://document-hub-core:8081
    depends_on:
      - document-hub-core
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=document_hub
      - POSTGRES_USER=hub
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres-data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
  
  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant-data:/qdrant/storage

volumes:
  shared-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /abs-shared-data
  postgres-data:
  redis-data:
  qdrant-data:
```

## Benefits of Centralized Document Hub

### For Individual Applications
- **Unified Document Access**: All apps access the same document pool
- **Cross-App Intelligence**: Build upon other apps' analysis results
- **Reduced Duplication**: No need to store documents multiple times
- **Enhanced Search**: Search across all documents regardless of source app

### For the Ecosystem
- **Centralized Management**: Single point of control for all documents
- **Consistent Data Model**: Standardized document structure across apps
- **Scalable Architecture**: Add new apps without changing existing ones
- **Unified Analytics**: Portfolio-wide insights and reporting

### For Legal Organizations
- **Complete Document Portfolio**: View all documents across all tools
- **Cross-Tool Analysis**: Compare insights from different applications
- **Efficient Workflows**: Seamless handoff between tools
- **Comprehensive Reporting**: Reports spanning entire document collection
- **Compliance Management**: Centralized audit trails and access control

This Centralized Document Hub Architecture provides a robust foundation for multi-app document management while maintaining the flexibility and performance needed for enterprise legal operations.
