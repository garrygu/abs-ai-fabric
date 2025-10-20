# Practical Example: Redis + PostgreSQL Integration

## Current Implementation (Redis-Only)

Let me show you how the current Contract Reviewer v2 uses Redis and how it will work with PostgreSQL:

### **Current Redis Usage in app.py**

```python
# Current Redis-only implementation
import redis as redislib

# Redis client for caching
redis_client = None
try:
    redis_client = redislib.from_url(REDIS_URL)
    redis_client.ping()
except:
    redis_client = None

# Current analysis result saving (Redis-only)
def save_analysis_result(document_id: str, analysis_data: Dict[str, Any]) -> str:
    """Save analysis result to Redis and local cache"""
    analysis_id = str(uuid.uuid4())
    analysis_data["analysis_id"] = analysis_id
    analysis_data["document_id"] = document_id
    analysis_data["saved_at"] = datetime.now().isoformat()
    
    # Save to Redis if available
    if redis_client:
        try:
            redis_client.setex(
                f"analysis:{analysis_id}", 
                86400 * 30,  # 30 days expiry
                json.dumps(analysis_data)
            )
            redis_client.setex(
                f"document_analysis:{document_id}", 
                86400 * 30,  # 30 days expiry
                analysis_id
            )
        except Exception as e:
            print(f"Error saving to Redis: {e}")
    
    # Also save to local memory cache
    analysis_results_cache[analysis_id] = analysis_data
    return analysis_id

# Current analysis result loading (Redis-only)
def load_analysis_result(document_id: str) -> Optional[Dict[str, Any]]:
    """Load analysis result from Redis or local cache"""
    # Try Redis first
    if redis_client:
        try:
            analysis_id = redis_client.get(f"document_analysis:{document_id}")
            if analysis_id:
                analysis_data = redis_client.get(f"analysis:{analysis_id.decode()}")
                if analysis_data:
                    return json.loads(analysis_data)
        except Exception as e:
            print(f"Error loading from Redis: {e}")
    
    # Fallback to local cache
    for analysis_id, analysis_data in analysis_results_cache.items():
        if analysis_data.get("document_id") == document_id:
            return analysis_data
    
    return None
```

## New Implementation (Redis + PostgreSQL)

### **Enhanced Implementation with Dual Storage**

```python
# New Redis + PostgreSQL implementation
import redis as redislib
from document_service import DocumentService

# Initialize both Redis and PostgreSQL
redis_client = None
doc_service = None

try:
    # Redis client for caching
    redis_client = redislib.from_url(REDIS_URL)
    redis_client.ping()
    
    # PostgreSQL service for persistence
    doc_service = DocumentService()
    await doc_service.initialize()
    
    print("✅ Both Redis and PostgreSQL initialized")
except Exception as e:
    print(f"❌ Error initializing storage: {e}")

# Enhanced analysis result saving (Redis + PostgreSQL)
async def save_analysis_result(document_id: str, analysis_data: Dict[str, Any]) -> str:
    """Save analysis result to both Redis (cache) and PostgreSQL (persistent)"""
    analysis_id = str(uuid.uuid4())
    analysis_data["analysis_id"] = analysis_id
    analysis_data["document_id"] = document_id
    analysis_data["saved_at"] = datetime.now().isoformat()
    
    try:
        # 1. Save to PostgreSQL (persistent storage)
        if doc_service:
            postgres_result = await doc_service.create_analysis_result(
                document_id=document_id,
                analysis_type="contract_review",
                analysis_data=analysis_data,
                model_used=analysis_data.get("model_used", "llama3.2:3b"),
                processing_time_ms=analysis_data.get("processing_time_ms", 0)
            )
            analysis_id = postgres_result["id"]  # Use PostgreSQL-generated ID
        
        # 2. Save to Redis (fast cache)
        if redis_client:
            redis_client.setex(
                f"analysis:{analysis_id}", 
                86400 * 7,  # 7 days cache
                json.dumps(analysis_data)
            )
            redis_client.setex(
                f"document_analysis:{document_id}", 
                86400 * 7,  # 7 days cache
                analysis_id
            )
        
        # 3. Save to local memory cache (fallback)
        analysis_results_cache[analysis_id] = analysis_data
        
        print(f"✅ Analysis saved to PostgreSQL and cached in Redis: {analysis_id}")
        return analysis_id
        
    except Exception as e:
        print(f"❌ Error saving analysis: {e}")
        raise

# Enhanced analysis result loading (Redis + PostgreSQL)
async def load_analysis_result(document_id: str) -> Optional[Dict[str, Any]]:
    """Load analysis result from Redis cache, fallback to PostgreSQL"""
    
    # 1. Try Redis cache first (fastest)
    if redis_client:
        try:
            analysis_id = redis_client.get(f"document_analysis:{document_id}")
            if analysis_id:
                analysis_data = redis_client.get(f"analysis:{analysis_id.decode()}")
                if analysis_data:
                    print(f"✅ Analysis loaded from Redis cache: {analysis_id.decode()}")
                    return json.loads(analysis_data)
        except Exception as e:
            print(f"⚠️ Error loading from Redis: {e}")
    
    # 2. Try PostgreSQL (authoritative source)
    if doc_service:
        try:
            analyses = await doc_service.get_analysis_results_by_document(
                document_id=document_id,
                analysis_type="contract_review"
            )
            if analyses:
                analysis = analyses[0]  # Get most recent analysis
                
                # Cache in Redis for next time
                if redis_client:
                    redis_client.setex(
                        f"analysis:{analysis['id']}", 
                        86400 * 7,  # 7 days cache
                        json.dumps(analysis)
                    )
                    redis_client.setex(
                        f"document_analysis:{document_id}", 
                        86400 * 7,  # 7 days cache
                        analysis['id']
                    )
                
                print(f"✅ Analysis loaded from PostgreSQL and cached: {analysis['id']}")
                return analysis
        except Exception as e:
            print(f"⚠️ Error loading from PostgreSQL: {e}")
    
    # 3. Fallback to local memory cache
    for analysis_id, analysis_data in analysis_results_cache.items():
        if analysis_data.get("document_id") == document_id:
            print(f"✅ Analysis loaded from local cache: {analysis_id}")
            return analysis_data
    
    print(f"⚠️ No analysis found for document: {document_id}")
    return None
```

## Data Flow Examples

### **Example 1: Document Upload and Analysis**

```python
# 1. User uploads document
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    # Save file to disk
    file_path = UPLOADS_DIR / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create document record in PostgreSQL
    document = await doc_service.create_document(
        file_path=str(file_path),
        original_filename=file.filename,
        metadata={"upload_source": "contract-reviewer-v2"}
    )
    
    # Cache document info in Redis
    if redis_client:
        redis_client.setex(
            f"document:{document['id']}", 
            3600,  # 1 hour cache
            json.dumps(document)
        )
    
    return {"document_id": document["id"], "status": "uploaded"}

# 2. Analyze document
@app.post("/api/analyze/{document_id}")
async def analyze_document(document_id: str):
    # Get document from cache or database
    document = await get_document(document_id)
    
    # Perform analysis
    analysis_result = await perform_analysis(document)
    
    # Save analysis to both PostgreSQL and Redis
    analysis_id = await save_analysis_result(document_id, analysis_result)
    
    return {"analysis_id": analysis_id, "status": "completed"}
```

### **Example 2: Document List with Caching**

```python
@app.get("/api/documents")
async def list_documents(limit: int = 10, offset: int = 0):
    # Check Redis cache first
    cache_key = f"documents:list:{limit}:{offset}"
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            print("✅ Document list loaded from Redis cache")
            return json.loads(cached)
    
    # Load from PostgreSQL
    documents, total_count = await doc_service.get_documents(
        limit=limit, 
        offset=offset
    )
    
    response = {
        "documents": documents,
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }
    
    # Cache in Redis
    if redis_client:
        redis_client.setex(cache_key, 300, json.dumps(response))  # 5 min cache
    
    print("✅ Document list loaded from PostgreSQL and cached")
    return response
```

### **Example 3: Session Management**

```python
# User session management
class SessionManager:
    def __init__(self):
        self.redis_client = redis_client
        self.doc_service = doc_service
    
    async def create_session(self, user_id: str, document_id: str):
        session_id = str(uuid.uuid4())
        
        # Store session in Redis (fast access)
        session_data = {
            "user_id": user_id,
            "document_id": document_id,
            "created_at": datetime.now().isoformat(),
            "permissions": ["read", "analyze"]
        }
        
        if self.redis_client:
            self.redis_client.setex(
                f"session:{session_id}", 
                3600,  # 1 hour TTL
                json.dumps(session_data)
            )
        
        # Log session creation in PostgreSQL (audit)
        if self.doc_service:
            await self.doc_service.create_audit_log(
                user_id=user_id,
                action="session_created",
                document_id=document_id,
                details={"session_id": session_id}
            )
        
        return session_id
    
    async def get_session(self, session_id: str):
        # Get from Redis (fast)
        if self.redis_client:
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                return json.loads(session_data)
        
        return None
```

## Performance Benefits

### **Cache Hit Scenarios**
```
User requests analysis result
    ↓
Check Redis cache (1ms)
    ↓
Cache HIT → Return result immediately
    ↓
Total response time: ~5ms
```

### **Cache Miss Scenarios**
```
User requests analysis result
    ↓
Check Redis cache (1ms) → MISS
    ↓
Query PostgreSQL (50ms)
    ↓
Cache result in Redis
    ↓
Return result to user
    ↓
Total response time: ~60ms
    ↓
Next request: ~5ms (cached)
```

## Migration Strategy

### **Phase 1: Dual Write (Current)**
```python
# Write to both Redis and PostgreSQL
async def save_analysis_result(document_id: str, analysis_data: dict):
    # Write to PostgreSQL (new)
    postgres_result = await doc_service.create_analysis_result(...)
    
    # Write to Redis (existing)
    redis_client.setex(f"analysis:{postgres_result['id']}", ...)
    
    return postgres_result
```

### **Phase 2: Read from PostgreSQL**
```python
# Read from PostgreSQL, cache in Redis
async def load_analysis_result(document_id: str):
    # Check Redis cache first
    cached = redis_client.get(f"document_analysis:{document_id}")
    if cached:
        return json.loads(cached)
    
    # Read from PostgreSQL (authoritative)
    result = await doc_service.get_analysis_results_by_document(document_id)
    
    # Cache in Redis
    redis_client.setex(f"analysis:{result['id']}", ...)
    
    return result
```

### **Phase 3: Redis Optimization**
```python
# Optimize Redis usage
# Keep in Redis: sessions, API cache, real-time data
# Move to PostgreSQL: document metadata, analysis results, user data
```

## Monitoring and Debugging

### **Cache Performance Monitoring**
```python
# Monitor cache hit rates
cache_hits = redis_client.info()['keyspace_hits']
cache_misses = redis_client.info()['keyspace_misses']
hit_rate = cache_hits / (cache_hits + cache_misses)

print(f"Redis cache hit rate: {hit_rate:.2%}")
```

### **Data Consistency Checks**
```python
# Verify data consistency between Redis and PostgreSQL
async def verify_consistency():
    # Get all analysis IDs from Redis
    redis_keys = redis_client.keys("analysis:*")
    
    # Get all analysis IDs from PostgreSQL
    postgres_analyses = await doc_service.get_all_analysis_results()
    
    # Compare counts
    print(f"Redis analyses: {len(redis_keys)}")
    print(f"PostgreSQL analyses: {len(postgres_analyses)}")
```

## Summary

**Redis and PostgreSQL work together as complementary layers:**

1. **Redis**: Fast cache for frequently accessed data
   - Session data
   - Cached API responses
   - Temporary analysis results
   - Real-time updates

2. **PostgreSQL**: Persistent storage for authoritative data
   - Document metadata
   - Complete analysis results
   - User accounts and permissions
   - Audit logs and compliance data

3. **Together**: Optimal performance with data durability
   - Fast access through caching
   - Data persistence and integrity
   - Scalable architecture
   - Cost-effective resource usage

This architecture ensures that your Contract Reviewer v2 gets the best of both worlds: **Redis's speed** for frequently accessed data and **PostgreSQL's reliability** for persistent storage.
