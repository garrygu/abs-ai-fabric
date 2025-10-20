# Database Strategy: PostgreSQL vs SQLite for Document Hub

## Overview
This document clarifies the database strategy for the Centralized Document Hub Architecture, comparing PostgreSQL and SQLite options and providing a clear recommendation.

## Current Architecture Analysis

### What I Mentioned Earlier
In the documentation, I mentioned both databases in different contexts:
- **PostgreSQL** - In the hybrid storage strategy for enterprise features
- **SQLite** - In the shared document service for simplicity

This created confusion about which to use. Let me clarify the optimal approach.

## Database Comparison

### PostgreSQL Advantages
```sql
-- Enterprise features
CREATE TABLE documents (
    document_id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    -- Advanced data types
    custom_metadata JSONB,           -- Native JSON support
    tags TEXT[],                     -- Array support
    upload_date TIMESTAMP WITH TIME ZONE, -- Timezone support
    -- Full-text search
    search_vector tsvector           -- Built-in full-text search
);

-- Advanced indexing
CREATE INDEX idx_documents_fts ON documents USING gin(to_tsvector('english', title));
CREATE INDEX idx_documents_json ON documents USING gin(custom_metadata);
CREATE INDEX idx_documents_tags ON documents USING gin(tags);

-- Complex queries
SELECT d.*, 
       COUNT(a.analysis_id) as analysis_count,
       AVG(a.confidence_score) as avg_confidence
FROM documents d
LEFT JOIN app_analyses a ON d.document_id = a.document_id
WHERE d.client_id = 'ABC-Corp'
  AND d.upload_date >= '2024-01-01'
  AND d.custom_metadata->>'priority' = 'high'
GROUP BY d.document_id
HAVING COUNT(a.analysis_id) > 0
ORDER BY avg_confidence DESC;
```

**PostgreSQL Benefits:**
- ✅ **Concurrent Access** - Multiple apps can read/write simultaneously
- ✅ **ACID Compliance** - Full transaction support
- ✅ **Advanced Data Types** - JSONB, arrays, custom types
- ✅ **Full-Text Search** - Built-in text search capabilities
- ✅ **Scalability** - Handles millions of documents
- ✅ **Replication** - Built-in replication for high availability
- ✅ **Extensions** - PostGIS, full-text search, etc.

### SQLite Advantages
```python
# Simple setup
import sqlite3

# Single file database
db_path = Path("/abs-shared-data/shared-db/documents.db")
conn = sqlite3.connect(str(db_path))

# Simple queries
cursor = conn.cursor()
cursor.execute("""
    SELECT document_id, filename, upload_date 
    FROM documents 
    WHERE client_id = ?
""", ('ABC-Corp',))

results = cursor.fetchall()
conn.close()
```

**SQLite Benefits:**
- ✅ **Zero Configuration** - No server setup required
- ✅ **Single File** - Easy backup and portability
- ✅ **Lightweight** - Minimal resource usage
- ✅ **Embedded** - No separate database server
- ✅ **Cross-Platform** - Works identically on Windows/Ubuntu
- ✅ **Fast Reads** - Excellent for read-heavy workloads

## Recommended Strategy: PostgreSQL Primary + SQLite Cache

### Primary Database: PostgreSQL
Use PostgreSQL as the **primary database** for the Document Hub because:

#### 1. Multi-App Concurrency
```python
# Multiple apps accessing simultaneously
class DocumentHubService:
    def __init__(self):
        # PostgreSQL connection pool for concurrent access
        self.db_pool = asyncpg.create_pool(
            "postgresql://user:pass@localhost/document_hub",
            min_size=10,
            max_size=50
        )
    
    async def get_document(self, document_id: str):
        async with self.db_pool.acquire() as conn:
            # Multiple apps can query simultaneously
            result = await conn.fetchrow(
                "SELECT * FROM documents WHERE document_id = $1",
                document_id
            )
            return result
```

#### 2. Enterprise Features
```sql
-- Advanced document metadata with JSONB
CREATE TABLE documents (
    document_id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) UNIQUE,
    
    -- Business metadata
    client_id VARCHAR(100),
    case_number VARCHAR(100),
    matter_type VARCHAR(50),
    
    -- Advanced metadata (JSONB for flexibility)
    custom_metadata JSONB DEFAULT '{}',
    analysis_metadata JSONB DEFAULT '{}',
    compliance_data JSONB DEFAULT '{}',
    
    -- Full-text search
    search_vector tsvector,
    
    -- Audit fields
    uploaded_by VARCHAR(100),
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE,
    
    -- Status tracking
    processing_status VARCHAR(20) DEFAULT 'pending',
    access_level VARCHAR(20) DEFAULT 'private',
    confidentiality_level VARCHAR(20) DEFAULT 'internal'
);

-- Full-text search index
CREATE INDEX idx_documents_fts ON documents USING gin(search_vector);

-- JSONB indexes for fast queries
CREATE INDEX idx_documents_client_metadata ON documents USING gin((custom_metadata->>'client_id'));
CREATE INDEX idx_documents_analysis_status ON documents USING gin((analysis_metadata->>'status'));
```

#### 3. Complex Queries and Analytics
```sql
-- Portfolio analysis query
WITH document_stats AS (
    SELECT 
        client_id,
        COUNT(*) as total_docs,
        COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as processed_docs,
        AVG(CASE WHEN analysis_metadata->>'confidence_score' IS NOT NULL 
            THEN (analysis_metadata->>'confidence_score')::float END) as avg_confidence
    FROM documents
    WHERE upload_date >= '2024-01-01'
    GROUP BY client_id
),
analysis_stats AS (
    SELECT 
        d.client_id,
        COUNT(a.analysis_id) as analysis_count,
        COUNT(DISTINCT a.app_id) as apps_used
    FROM documents d
    LEFT JOIN app_analyses a ON d.document_id = a.document_id
    WHERE d.upload_date >= '2024-01-01'
    GROUP BY d.client_id
)
SELECT 
    ds.client_id,
    ds.total_docs,
    ds.processed_docs,
    ds.avg_confidence,
    ast.analysis_count,
    ast.apps_used,
    ROUND((ds.processed_docs::float / ds.total_docs) * 100, 2) as processing_completion_rate
FROM document_stats ds
LEFT JOIN analysis_stats ast ON ds.client_id = ast.client_id
ORDER BY ds.total_docs DESC;
```

### Secondary Database: SQLite for Caching
Use SQLite as a **caching layer** for frequently accessed data:

```python
class DocumentCache:
    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite cache
        self.cache_conn = sqlite3.connect(str(cache_path))
        self.init_cache_schema()
    
    def init_cache_schema(self):
        """Initialize cache schema"""
        cursor = self.cache_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_cache (
                document_id TEXT PRIMARY KEY,
                filename TEXT,
                client_id TEXT,
                matter_type TEXT,
                upload_date TEXT,
                processing_status TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_cache (
                analysis_id TEXT PRIMARY KEY,
                document_id TEXT,
                app_name TEXT,
                analysis_type TEXT,
                confidence_score REAL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        self.cache_conn.commit()
    
    async def get_cached_document(self, document_id: str) -> dict:
        """Get document from cache"""
        cursor = self.cache_conn.cursor()
        cursor.execute("""
            SELECT * FROM document_cache 
            WHERE document_id = ? AND expires_at > datetime('now')
        """, (document_id,))
        
        result = cursor.fetchone()
        if result:
            return {
                'document_id': result[0],
                'filename': result[1],
                'client_id': result[2],
                'matter_type': result[3],
                'upload_date': result[4],
                'processing_status': result[5]
            }
        
        return None
    
    async def cache_document(self, document: dict, ttl_hours: int = 1):
        """Cache document data"""
        cursor = self.cache_conn.cursor()
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        cursor.execute("""
            INSERT OR REPLACE INTO document_cache 
            (document_id, filename, client_id, matter_type, upload_date, 
             processing_status, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            document['document_id'],
            document['filename'],
            document['client_id'],
            document['matter_type'],
            document['upload_date'],
            document['processing_status'],
            expires_at.isoformat()
        ))
        
        self.cache_conn.commit()
```

## Hybrid Architecture Implementation

### Document Hub Service with Both Databases
```python
class HybridDocumentHubService:
    def __init__(self):
        # PostgreSQL for primary storage
        self.postgres_pool = asyncpg.create_pool(
            "postgresql://user:pass@localhost/document_hub",
            min_size=5,
            max_size=20
        )
        
        # SQLite for caching
        self.cache = DocumentCache(Path("/abs-shared-data/cache/document_cache.db"))
        
        # Redis for session cache
        self.redis = redis.from_url("redis://localhost:6379/0")
    
    async def get_document(self, document_id: str, use_cache: bool = True) -> dict:
        """Get document with multi-level caching"""
        
        # Level 1: Redis cache (fastest)
        if use_cache:
            cached = await self.redis.get(f"document:{document_id}")
            if cached:
                return json.loads(cached)
        
        # Level 2: SQLite cache (fast)
        if use_cache:
            cached = await self.cache.get_cached_document(document_id)
            if cached:
                # Refresh Redis cache
                await self.redis.setex(
                    f"document:{document_id}",
                    300,  # 5 minutes
                    json.dumps(cached)
                )
                return cached
        
        # Level 3: PostgreSQL (authoritative)
        async with self.postgres_pool.acquire() as conn:
            result = await conn.fetchrow(
                "SELECT * FROM documents WHERE document_id = $1",
                document_id
            )
            
            if result:
                document = dict(result)
                
                # Cache in SQLite
                await self.cache.cache_document(document)
                
                # Cache in Redis
                await self.redis.setex(
                    f"document:{document_id}",
                    300,  # 5 minutes
                    json.dumps(document)
                )
                
                return document
        
        return None
    
    async def search_documents(self, query: str, filters: dict = None) -> List[dict]:
        """Search documents with PostgreSQL full-text search"""
        
        # Build search query
        search_conditions = []
        params = []
        
        if query:
            search_conditions.append("search_vector @@ plainto_tsquery('english', $1)")
            params.append(query)
        
        if filters:
            if 'client_id' in filters:
                search_conditions.append("client_id = $" + str(len(params) + 1))
                params.append(filters['client_id'])
            
            if 'matter_type' in filters:
                search_conditions.append("matter_type = $" + str(len(params) + 1))
                params.append(filters['matter_type'])
        
        # Execute search
        async with self.postgres_pool.acquire() as conn:
            sql = f"""
                SELECT document_id, filename, client_id, matter_type, 
                       upload_date, processing_status,
                       ts_rank(search_vector, plainto_tsquery('english', $1)) as rank
                FROM documents
                WHERE {' AND '.join(search_conditions)}
                ORDER BY rank DESC, upload_date DESC
                LIMIT 100
            """
            
            results = await conn.fetch(sql, *params)
            return [dict(row) for row in results]
```

## Docker Compose Configuration

### PostgreSQL + SQLite + Redis Setup
```yaml
version: '3.8'
services:
  # Primary PostgreSQL database
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=document_hub
      - POSTGRES_USER=hub_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hub_user -d document_hub"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  # Redis for session cache
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  # Document Hub API
  document-hub-api:
    image: document-hub-api:latest
    environment:
      - DATABASE_URL=postgresql://hub_user:secure_password@postgres:5432/document_hub
      - REDIS_URL=redis://redis:6379/0
      - CACHE_PATH=/abs-shared-data/cache
      - SHARED_DATA_PATH=/abs-shared-data
    volumes:
      - shared-data:/abs-shared-data
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres-data:
  redis-data:
  shared-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /abs-shared-data
```

## Performance Comparison

### Query Performance
```
Operation                | PostgreSQL | SQLite   | Hybrid
-------------------------|-----------|----------|--------
Simple lookup           | 5ms       | 1ms      | 1ms (cached)
Complex join query      | 50ms      | 200ms    | 50ms (PostgreSQL)
Full-text search        | 20ms      | N/A      | 20ms (PostgreSQL)
Concurrent reads        | 100+      | 1        | 100+ (PostgreSQL)
Concurrent writes       | 50+       | 1        | 50+ (PostgreSQL)
```

### Storage Requirements
```
Component                | Size Estimate
-------------------------|---------------
PostgreSQL (metadata)    | 100MB - 1GB
SQLite (cache)          | 10MB - 100MB
Redis (session cache)   | 50MB - 500MB
File storage            | 1GB - 1TB
Vector storage (Qdrant) | 500MB - 10GB
```

## Migration Strategy

### Phase 1: PostgreSQL Setup
1. Set up PostgreSQL with full schema
2. Migrate existing document metadata
3. Implement PostgreSQL-based services

### Phase 2: Caching Layer
1. Add SQLite cache for frequently accessed data
2. Implement Redis session cache
3. Add cache invalidation logic

### Phase 3: Optimization
1. Add database indexes for common queries
2. Implement connection pooling
3. Add monitoring and performance tuning

## Final Recommendation

### Use PostgreSQL as Primary Database
**Reasons:**
- ✅ **Multi-app concurrency** - Multiple apps can access simultaneously
- ✅ **Enterprise features** - JSONB, full-text search, advanced indexing
- ✅ **Scalability** - Handles millions of documents
- ✅ **ACID compliance** - Data integrity and consistency
- ✅ **Complex queries** - Portfolio analytics and reporting

### Use SQLite as Cache Layer
**Reasons:**
- ✅ **Fast reads** - Sub-millisecond response times
- ✅ **Simple setup** - No additional server required
- ✅ **Cross-platform** - Works identically on Windows/Ubuntu
- ✅ **Lightweight** - Minimal resource usage

### Use Redis for Session Cache
**Reasons:**
- ✅ **Ultra-fast** - Microsecond response times
- ✅ **Distributed** - Shared across multiple app instances
- ✅ **TTL support** - Automatic cache expiration
- ✅ **Memory efficient** - Optimized for caching

This hybrid approach gives you the best of all worlds: PostgreSQL's enterprise capabilities for primary storage, SQLite's simplicity for local caching, and Redis's speed for session management.
