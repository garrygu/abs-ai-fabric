# Redis and PostgreSQL Integration Architecture

## Overview

In our new hybrid architecture, **Redis and PostgreSQL work together as complementary storage layers**, each optimized for different use cases and data access patterns. This is NOT a replacement relationship - it's a **collaborative partnership**.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                     │
│  Contract Reviewer v2 | Legal Assistant | Other Apps                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SERVICE LAYER                                         │
│  Document Service | Analysis Service | Cache Service                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE LAYER                                         │
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │     REDIS        │    │   POSTGRESQL    │    │     QDRANT      │            │
│  │   (Caching)      │    │  (Persistence)   │    │  (Vectors)      │            │
│  │                 │    │                 │    │                 │            │
│  │ • Session Data   │    │ • Document      │    │ • Text Chunks   │            │
│  │ • Temp Results   │    │   Metadata      │    │ • Embeddings    │            │
│  │ • API Cache      │    │ • Analysis      │    │ • Similarity    │            │
│  │ • Rate Limiting  │    │   Results       │    │   Search        │            │
│  │ • Real-time      │    │ • User Data     │    │ • Cross-doc     │            │
│  │   Updates        │    │ • Audit Logs    │    │   Analysis      │            │
│  │ • Queue Data     │    │ • Relationships │    │                 │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FILE SYSTEM                                           │
│  • Original Documents (.pdf, .docx)                                            │
│  • Analysis Reports (.json, .pdf)                                               │
│  • Generated Reports                                                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## How Redis and PostgreSQL Work Together

### 1. **Redis as Primary Caching Layer**

Redis serves as the **fast access layer** for frequently accessed data:

#### **Session Management**
```python
# User sessions stored in Redis for fast access
redis_client.setex(
    f"session:{session_id}", 
    3600,  # 1 hour TTL
    json.dumps({
        "user_id": "user123",
        "document_id": "doc456",
        "permissions": ["read", "analyze"],
        "last_activity": "2024-01-01T10:00:00"
    })
)
```

#### **Analysis Result Caching**
```python
# Cache analysis results for quick access
redis_client.setex(
    f"analysis:{analysis_id}", 
    86400 * 7,  # 7 days TTL
    json.dumps({
        "summary": "Contract analysis complete",
        "risks": [...],
        "recommendations": [...],
        "cached_at": "2024-01-01T10:00:00"
    })
)
```

#### **API Response Caching**
```python
# Cache API responses to reduce database load
redis_client.setex(
    f"api:documents:list:{user_id}:{page}", 
    300,  # 5 minutes TTL
    json.dumps(document_list_response)
)
```

### 2. **PostgreSQL as Persistent Storage**

PostgreSQL serves as the **authoritative data store** for all persistent data:

#### **Document Metadata**
```sql
-- All document information stored permanently
INSERT INTO documents (
    id, filename, original_filename, file_path, 
    file_size, file_type, upload_timestamp, 
    status, metadata
) VALUES (
    'doc-uuid', 'contract.pdf', 'contract.pdf', 
    '/files/contract.pdf', 1024000, '.pdf', 
    '2024-01-01T10:00:00', 'uploaded', 
    '{"client": "ACME Corp", "contract_type": "NDA"}'
);
```

#### **Analysis Results**
```sql
-- Complete analysis results stored permanently
INSERT INTO analysis_results (
    id, document_id, analysis_type, analysis_data,
    model_used, processing_time_ms, status
) VALUES (
    'analysis-uuid', 'doc-uuid', 'contract_review',
    '{"summary": "...", "risks": [...], "recommendations": [...]}',
    'llama3.2:3b', 1500, 'completed'
);
```

## Data Flow Patterns

### **Pattern 1: Document Upload and Analysis**

```
1. User uploads document
   ↓
2. Document metadata → PostgreSQL (persistent)
   ↓
3. Analysis request → Redis queue (temporary)
   ↓
4. Analysis processing → Redis cache (temporary)
   ↓
5. Analysis results → PostgreSQL (persistent)
   ↓
6. Analysis results → Redis cache (for quick access)
```

### **Pattern 2: Document Retrieval**

```
1. User requests document list
   ↓
2. Check Redis cache first
   ↓
3. If cache miss → Query PostgreSQL
   ↓
4. Store result in Redis cache
   ↓
5. Return to user
```

### **Pattern 3: Analysis Result Access**

```
1. User requests analysis results
   ↓
2. Check Redis cache (fast)
   ↓
3. If cache miss → Query PostgreSQL (authoritative)
   ↓
4. Cache result in Redis
   ↓
5. Return to user
```

## Specific Use Cases

### **1. Session Management**
- **Redis**: Active user sessions, login tokens, temporary permissions
- **PostgreSQL**: User accounts, permanent permissions, audit logs

### **2. Document Analysis**
- **Redis**: Analysis queue, temporary processing state, cached results
- **PostgreSQL**: Document metadata, final analysis results, relationships

### **3. API Performance**
- **Redis**: Cached API responses, rate limiting counters, temporary data
- **PostgreSQL**: User data, document metadata, permanent configurations

### **4. Real-time Features**
- **Redis**: Live updates, notifications, temporary state
- **PostgreSQL**: Historical data, permanent records, audit trails

## Code Examples

### **Document Service with Dual Storage**

```python
class DocumentService:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.postgres_service = DocumentService()
    
    async def get_document(self, document_id: str):
        # 1. Check Redis cache first (fast)
        cached_doc = await self.redis_client.get(f"document:{document_id}")
        if cached_doc:
            return json.loads(cached_doc)
        
        # 2. If cache miss, query PostgreSQL (authoritative)
        document = await self.postgres_service.get_document_by_id(document_id)
        
        # 3. Cache result in Redis for next time
        await self.redis_client.setex(
            f"document:{document_id}", 
            3600,  # 1 hour TTL
            json.dumps(document)
        )
        
        return document
    
    async def create_analysis(self, document_id: str, analysis_data: dict):
        # 1. Store in PostgreSQL (persistent)
        analysis = await self.postgres_service.create_analysis_result(
            document_id=document_id,
            analysis_data=analysis_data
        )
        
        # 2. Cache in Redis (fast access)
        await self.redis_client.setex(
            f"analysis:{analysis['id']}", 
            86400 * 7,  # 7 days TTL
            json.dumps(analysis)
        )
        
        return analysis
```

### **Session Management**

```python
class SessionManager:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.postgres_service = DocumentService()
    
    async def create_session(self, user_id: str, document_id: str):
        session_id = str(uuid.uuid4())
        
        # 1. Store session in Redis (fast access)
        await self.redis_client.setex(
            f"session:{session_id}", 
            3600,  # 1 hour TTL
            json.dumps({
                "user_id": user_id,
                "document_id": document_id,
                "created_at": datetime.now().isoformat()
            })
        )
        
        # 2. Log session creation in PostgreSQL (audit)
        await self.postgres_service.create_audit_log(
            user_id=user_id,
            action="session_created",
            document_id=document_id,
            details={"session_id": session_id}
        )
        
        return session_id
```

## Benefits of This Architecture

### **1. Performance Optimization**
- **Redis**: Sub-millisecond access for cached data
- **PostgreSQL**: Optimized queries for complex data relationships
- **Combined**: Best of both worlds - speed and functionality

### **2. Data Durability**
- **Redis**: Fast access with TTL-based expiration
- **PostgreSQL**: ACID compliance and permanent storage
- **Combined**: No data loss, with performance benefits

### **3. Scalability**
- **Redis**: Horizontal scaling for cache layer
- **PostgreSQL**: Vertical scaling for data storage
- **Combined**: Handle high loads efficiently

### **4. Cost Optimization**
- **Redis**: Reduce database load and costs
- **PostgreSQL**: Store only what needs to be persistent
- **Combined**: Optimize resource usage

## Migration Strategy

### **Phase 1: Dual Write**
```python
# Write to both Redis and PostgreSQL during transition
async def save_analysis_result(self, analysis_data):
    # Write to PostgreSQL (new persistent storage)
    postgres_result = await self.postgres_service.create_analysis_result(analysis_data)
    
    # Write to Redis (existing cache)
    redis_result = await self.redis_client.setex(
        f"analysis:{postgres_result['id']}", 
        86400, 
        json.dumps(postgres_result)
    )
    
    return postgres_result
```

### **Phase 2: Read from PostgreSQL**
```python
# Read from PostgreSQL, cache in Redis
async def get_analysis_result(self, analysis_id):
    # Check Redis cache first
    cached = await self.redis_client.get(f"analysis:{analysis_id}")
    if cached:
        return json.loads(cached)
    
    # Read from PostgreSQL (authoritative)
    result = await self.postgres_service.get_analysis_result_by_id(analysis_id)
    
    # Cache in Redis
    await self.redis_client.setex(f"analysis:{analysis_id}", 3600, json.dumps(result))
    
    return result
```

### **Phase 3: Redis Cleanup**
```python
# Gradually reduce Redis usage for persistent data
# Keep Redis for: sessions, API cache, real-time features
# Move to PostgreSQL: document metadata, analysis results, user data
```

## Monitoring and Maintenance

### **Redis Monitoring**
- Memory usage and eviction policies
- Cache hit/miss ratios
- TTL effectiveness
- Connection pool status

### **PostgreSQL Monitoring**
- Query performance and slow queries
- Connection pool utilization
- Disk usage and growth
- Backup and recovery status

### **Integration Monitoring**
- Data consistency between systems
- Cache invalidation effectiveness
- Performance impact of dual storage
- Error rates and recovery

## Conclusion

**Redis and PostgreSQL work together as complementary layers:**

- **Redis**: Fast, temporary, cached data access
- **PostgreSQL**: Persistent, authoritative, relational data storage
- **Together**: Optimal performance with data durability

This architecture provides:
- ✅ **Fast access** through Redis caching
- ✅ **Data persistence** through PostgreSQL storage
- ✅ **Scalability** through distributed caching
- ✅ **Reliability** through ACID compliance
- ✅ **Cost efficiency** through optimized resource usage

The key is understanding that **Redis doesn't replace PostgreSQL** - it **enhances** it by providing a fast access layer while PostgreSQL provides the authoritative, persistent storage layer.
