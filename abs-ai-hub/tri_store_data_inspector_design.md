# Tri-Store Data Inspector - Gateway Hub Integration

## 🎯 **Design Decision: Gateway Hub Integration**

**Decision**: Implement the Tri-Store Data Inspector as a **standalone feature within the Gateway Hub** rather than a separate application.

### **Why Gateway Hub is Perfect:**

1. **✅ Already Has All Connections**: 
   - Redis: `REDIS_URL = "redis://redis:6379/0"`
   - PostgreSQL: `document-hub-postgres:5432`
   - Qdrant: `http://qdrant:6333`

2. **✅ Service Management**: 
   - Service registry with health monitoring
   - Auto-wake functionality
   - Container management via Docker API

3. **✅ Admin Interface**: 
   - Existing `/admin/services/status` endpoint
   - Service lifecycle management
   - Health checks for all stores

4. **✅ Unified Access**: 
   - Single entry point for all ABS services
   - Consistent authentication/authorization
   - Centralized logging and monitoring

## 🏗️ **Architecture Design**

```
┌─────────────────────────────────────────────────────────────┐
│                    Gateway Hub (Port 8081)                 │
├─────────────────────────────────────────────────────────────┤
│  Existing Features:                                         │
│  • Service Management                                       │
│  • Model Registry                                           │
│  • Chat API                                                 │
│  • Catalog API                                              │
├─────────────────────────────────────────────────────────────┤
│  NEW: Tri-Store Data Inspector                              │
│  • /admin/inspector/{doc_id}                               │
│  • /admin/inspector/diff/{doc_id}                          │
│  • /admin/inspector/batch                                  │
│  • /admin/inspector/health                                 │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Stores                              │
├─────────────────────────────────────────────────────────────┤
│  Redis          PostgreSQL        Qdrant                   │
│  ┌─────────┐    ┌─────────────┐   ┌─────────────┐          │
│  │doc:{id} │    │documents    │   │collections  │          │
│  │HASH     │    │table        │   │points       │          │
│  │TTL      │    │metadata     │   │vectors      │          │
│  └─────────┘    └─────────────┘   └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## 📋 **Implementation Plan**

### **Phase 1: Core Inspector API**

#### **1.1 Data Models**
```python
# Add to gateway/app.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class StoreSnapshot(BaseModel):
    found: bool
    store_type: str  # 'postgres' | 'redis' | 'qdrant'
    key: str
    payload: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None
    updated_at: Optional[str] = None
    ttl_seconds: Optional[int] = None  # Redis only

class TriStoreSnapshot(BaseModel):
    doc_id: str
    requested_at: str
    env: str = 'prod'
    postgres: Optional[StoreSnapshot] = None
    redis: Optional[StoreSnapshot] = None
    qdrant: Optional[StoreSnapshot] = None
    consistency: Dict[str, Any]

class ConsistencyReport(BaseModel):
    status: str  # 'OK' | 'WARNING' | 'ERROR'
    problems: List[Dict[str, str]]
    field_diff: List[Dict[str, Any]]
    embeddings_diff: List[Dict[str, Any]]
```

#### **1.2 Store Connectors**
```python
# Add connector functions to gateway/app.py

async def fetch_postgres_doc(doc_id: str) -> Optional[StoreSnapshot]:
    """Fetch document from PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='document-hub-postgres',
            port=5432,
            database='document_hub',
            user='hub_user',
            password='secure_password',
            connect_timeout=5
        )
        cursor = conn.cursor()
        
        # Query document
        cursor.execute("""
            SELECT id, title, content, lang, version, updated_at, meta
            FROM documents 
            WHERE id = %s
        """, (doc_id,))
        
        row = cursor.fetchone()
        if not row:
            return StoreSnapshot(found=False, store_type='postgres', key=doc_id)
        
        # Build payload
        payload = {
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'lang': row[3],
            'version': row[4],
            'updated_at': row[5].isoformat() if row[5] else None,
            'meta': row[6]
        }
        
        # Compute checksum
        checksum = compute_checksum(payload)
        
        cursor.close()
        conn.close()
        
        return StoreSnapshot(
            found=True,
            store_type='postgres',
            key=doc_id,
            payload=payload,
            checksum=checksum,
            updated_at=payload['updated_at']
        )
        
    except Exception as e:
        print(f"PostgreSQL fetch error: {e}")
        return StoreSnapshot(found=False, store_type='postgres', key=doc_id)

async def fetch_redis_doc(doc_id: str) -> Optional[StoreSnapshot]:
    """Fetch document from Redis"""
    try:
        if rds is None:
            return StoreSnapshot(found=False, store_type='redis', key=f"doc:{doc_id}")
        
        key = f"doc:{doc_id}"
        
        # Check if key exists
        if not rds.exists(key):
            return StoreSnapshot(found=False, store_type='redis', key=key)
        
        # Get TTL
        ttl = rds.ttl(key)
        
        # Get all fields
        fields = rds.hgetall(key)
        if not fields:
            return StoreSnapshot(found=False, store_type='redis', key=key)
        
        # Decode bytes to strings
        payload = {k.decode(): v.decode() for k, v in fields.items()}
        
        # Compute checksum
        checksum = compute_checksum(payload)
        
        return StoreSnapshot(
            found=True,
            store_type='redis',
            key=key,
            payload=payload,
            checksum=checksum,
            ttl_seconds=ttl,
            updated_at=payload.get('updated_at')
        )
        
    except Exception as e:
        print(f"Redis fetch error: {e}")
        return StoreSnapshot(found=False, store_type='redis', key=f"doc:{doc_id}")

async def fetch_qdrant_doc(doc_id: str) -> Optional[StoreSnapshot]:
    """Fetch document from Qdrant"""
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Try to retrieve point
            response = await client.post(
                f"http://qdrant:6333/collections/documents/points/retrieve",
                json={
                    "ids": [doc_id],
                    "with_payload": True,
                    "with_vector": False
                },
                timeout=5.0
            )
            
            if response.status_code != 200:
                return StoreSnapshot(found=False, store_type='qdrant', key=doc_id)
            
            data = response.json()
            points = data.get('result', {}).get('points', [])
            
            if not points:
                return StoreSnapshot(found=False, store_type='qdrant', key=doc_id)
            
            point = points[0]
            payload = point.get('payload', {})
            
            # Compute checksum
            checksum = compute_checksum(payload)
            
            return StoreSnapshot(
                found=True,
                store_type='qdrant',
                key=doc_id,
                payload=payload,
                checksum=checksum,
                updated_at=payload.get('updated_at')
            )
            
    except Exception as e:
        print(f"Qdrant fetch error: {e}")
        return StoreSnapshot(found=False, store_type='qdrant', key=doc_id)

def compute_checksum(data: Dict[str, Any]) -> str:
    """Compute stable checksum for data comparison"""
    import hashlib
    import json
    
    # Sort keys for consistent hashing
    sorted_data = {k: data[k] for k in sorted(data.keys())}
    json_str = json.dumps(sorted_data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]
```

#### **1.3 Consistency Analysis**
```python
def analyze_consistency(postgres: StoreSnapshot, redis: StoreSnapshot, qdrant: StoreSnapshot) -> Dict[str, Any]:
    """Analyze consistency across all three stores"""
    problems = []
    field_diff = []
    
    # Check presence
    stores = {
        'postgres': postgres,
        'redis': redis, 
        'qdrant': qdrant
    }
    
    found_stores = [name for name, store in stores.items() if store and store.found]
    
    if len(found_stores) == 0:
        problems.append({
            'code': 'MISSING_ALL',
            'message': f'Document not found in any store',
            'severity': 'ERROR'
        })
    elif len(found_stores) < 3:
        missing = [name for name, store in stores.items() if not store or not store.found]
        problems.append({
            'code': 'MISSING_STORES',
            'message': f'Document missing from: {", ".join(missing)}',
            'severity': 'WARNING'
        })
    
    # Check checksums
    checksums = {}
    for name, store in stores.items():
        if store and store.found and store.checksum:
            checksums[name] = store.checksum
    
    if len(set(checksums.values())) > 1:
        problems.append({
            'code': 'CHECKSUM_MISMATCH',
            'message': f'Data checksums differ across stores',
            'severity': 'WARNING'
        })
    
    # Check field differences
    common_fields = ['title', 'lang', 'version', 'updated_at']
    for field in common_fields:
        values = {}
        for name, store in stores.items():
            if store and store.found and store.payload:
                values[name] = store.payload.get(field)
        
        # Check if values differ
        non_null_values = {k: v for k, v in values.items() if v is not None}
        if len(set(str(v) for v in non_null_values.values())) > 1:
            field_diff.append({
                'field': field,
                'postgres': values.get('postgres'),
                'redis': values.get('redis'),
                'qdrant': values.get('qdrant')
            })
    
    # Check Redis TTL
    if redis and redis.found and redis.ttl_seconds is not None:
        if redis.ttl_seconds < 3600:  # Less than 1 hour
            problems.append({
                'code': 'REDIS_TTL_LOW',
                'message': f'Redis TTL is low: {redis.ttl_seconds} seconds',
                'severity': 'WARNING'
            })
    
    # Determine overall status
    if any(p['severity'] == 'ERROR' for p in problems):
        status = 'ERROR'
    elif problems or field_diff:
        status = 'WARNING'
    else:
        status = 'OK'
    
    return {
        'status': status,
        'problems': problems,
        'field_diff': field_diff,
        'found_stores': found_stores,
        'checksums': checksums
    }
```

#### **1.4 API Endpoints**
```python
# Add to gateway/app.py

@app.get("/admin/inspector/{doc_id}", response_model=TriStoreSnapshot)
async def inspect_document(doc_id: str, env: str = Query('prod')):
    """Inspect a document across all three stores"""
    
    # Parallel fetch from all stores
    postgres, redis, qdrant = await asyncio.gather(
        fetch_postgres_doc(doc_id),
        fetch_redis_doc(doc_id),
        fetch_qdrant_doc(doc_id)
    )
    
    # Analyze consistency
    consistency = analyze_consistency(postgres, redis, qdrant)
    
    return TriStoreSnapshot(
        doc_id=doc_id,
        requested_at=datetime.utcnow().isoformat() + "Z",
        env=env,
        postgres=postgres,
        redis=redis,
        qdrant=qdrant,
        consistency=consistency
    )

@app.get("/admin/inspector/diff/{doc_id}")
async def get_document_diff(doc_id: str, env: str = Query('prod')):
    """Get only the consistency analysis for a document"""
    snapshot = await inspect_document(doc_id, env)
    return snapshot.consistency

@app.post("/admin/inspector/batch")
async def inspect_batch_documents(doc_ids: List[str], env: str = Query('prod')):
    """Inspect multiple documents in batch"""
    results = []
    
    for doc_id in doc_ids:
        try:
            snapshot = await inspect_document(doc_id, env)
            results.append(snapshot)
        except Exception as e:
            results.append({
                'doc_id': doc_id,
                'error': str(e),
                'consistency': {'status': 'ERROR', 'problems': [{'code': 'FETCH_ERROR', 'message': str(e)}]}
            })
    
    return {'results': results, 'total': len(results)}

@app.get("/admin/inspector/health")
async def inspector_health():
    """Health check for all data stores"""
    health = {}
    
    # Test PostgreSQL
    try:
        pg_snapshot = await fetch_postgres_doc("health_check_test")
        health['postgres'] = {'status': 'healthy', 'error': None}
    except Exception as e:
        health['postgres'] = {'status': 'unhealthy', 'error': str(e)}
    
    # Test Redis
    try:
        redis_snapshot = await fetch_redis_doc("health_check_test")
        health['redis'] = {'status': 'healthy', 'error': None}
    except Exception as e:
        health['redis'] = {'status': 'unhealthy', 'error': str(e)}
    
    # Test Qdrant
    try:
        qdrant_snapshot = await fetch_qdrant_doc("health_check_test")
        health['qdrant'] = {'status': 'healthy', 'error': None}
    except Exception as e:
        health['qdrant'] = {'status': 'unhealthy', 'error': str(e)}
    
    return health
```

### **Phase 2: Web UI Integration**

#### **2.1 Add to Gateway Static Files**
```html
<!-- Add to gateway static files: inspector.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tri-Store Data Inspector</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
</head>
<body class="bg-gray-100">
    <div x-data="inspectorApp()" class="min-h-screen">
        <!-- Header -->
        <header class="bg-white shadow-sm border-b">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center py-4">
                    <h1 class="text-2xl font-bold text-gray-900">
                        <i class="fas fa-search mr-2"></i>Tri-Store Data Inspector
                    </h1>
                    <div class="flex items-center space-x-4">
                        <select x-model="env" class="border rounded px-3 py-1">
                            <option value="dev">Development</option>
                            <option value="staging">Staging</option>
                            <option value="prod">Production</option>
                        </select>
                        <button @click="checkHealth()" 
                                class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                            <i class="fas fa-heartbeat mr-2"></i>Health Check
                        </button>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <!-- Search Form -->
            <div class="bg-white rounded-lg shadow p-6 mb-6">
                <div class="flex gap-4">
                    <input x-model="docId" 
                           placeholder="Enter document ID" 
                           class="flex-1 border rounded px-3 py-2"
                           @keyup.enter="inspectDocument()">
                    <button @click="inspectDocument()" 
                            :disabled="!docId || loading"
                            class="px-6 py-2 bg-black text-white rounded hover:bg-gray-800 disabled:opacity-50">
                        <i class="fas fa-search mr-2"></i>Inspect
                    </button>
                </div>
            </div>

            <!-- Results -->
            <div x-show="result" class="space-y-6">
                <!-- Consistency Status -->
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold mb-4">Consistency Analysis</h3>
                    <div class="flex items-center mb-4">
                        <span :class="getStatusColor(result.consistency.status)" 
                              class="px-3 py-1 rounded-full text-sm font-medium">
                            <i :class="getStatusIcon(result.consistency.status)" class="mr-2"></i>
                            <span x-text="result.consistency.status"></span>
                        </span>
                    </div>
                    
                    <!-- Problems -->
                    <div x-show="result.consistency.problems.length > 0" class="mb-4">
                        <h4 class="font-medium text-red-600 mb-2">Issues Found:</h4>
                        <ul class="list-disc pl-5 space-y-1">
                            <template x-for="problem in result.consistency.problems" :key="problem.code">
                                <li class="text-sm" x-text="problem.message"></li>
                            </template>
                        </ul>
                    </div>
                    
                    <!-- Field Differences -->
                    <div x-show="result.consistency.field_diff.length > 0">
                        <h4 class="font-medium text-orange-600 mb-2">Field Differences:</h4>
                        <div class="overflow-x-auto">
                            <table class="min-w-full text-sm">
                                <thead class="bg-gray-50">
                                    <tr>
                                        <th class="px-3 py-2 text-left">Field</th>
                                        <th class="px-3 py-2 text-left">PostgreSQL</th>
                                        <th class="px-3 py-2 text-left">Redis</th>
                                        <th class="px-3 py-2 text-left">Qdrant</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <template x-for="diff in result.consistency.field_diff" :key="diff.field">
                                        <tr class="border-t">
                                            <td class="px-3 py-2 font-medium" x-text="diff.field"></td>
                                            <td class="px-3 py-2" x-text="formatValue(diff.postgres)"></td>
                                            <td class="px-3 py-2" x-text="formatValue(diff.redis)"></td>
                                            <td class="px-3 py-2" x-text="formatValue(diff.qdrant)"></td>
                                        </tr>
                                    </template>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Store Details -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- PostgreSQL -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold mb-4 flex items-center">
                            <i class="fas fa-database text-blue-600 mr-2"></i>PostgreSQL
                        </h3>
                        <div x-show="result.postgres">
                            <div class="space-y-2 text-sm">
                                <div class="flex justify-between">
                                    <span>Status:</span>
                                    <span :class="result.postgres.found ? 'text-green-600' : 'text-red-600'">
                                        <i :class="result.postgres.found ? 'fas fa-check' : 'fas fa-times'" class="mr-1"></i>
                                        <span x-text="result.postgres.found ? 'Found' : 'Not Found'"></span>
                                    </span>
                                </div>
                                <div x-show="result.postgres.found" class="space-y-1">
                                    <div class="flex justify-between">
                                        <span>Key:</span>
                                        <span class="font-mono text-xs" x-text="result.postgres.key"></span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>Checksum:</span>
                                        <span class="font-mono text-xs" x-text="result.postgres.checksum"></span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>Updated:</span>
                                        <span x-text="result.postgres.updated_at"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Redis -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold mb-4 flex items-center">
                            <i class="fas fa-memory text-red-600 mr-2"></i>Redis
                        </h3>
                        <div x-show="result.redis">
                            <div class="space-y-2 text-sm">
                                <div class="flex justify-between">
                                    <span>Status:</span>
                                    <span :class="result.redis.found ? 'text-green-600' : 'text-red-600'">
                                        <i :class="result.redis.found ? 'fas fa-check' : 'fas fa-times'" class="mr-1"></i>
                                        <span x-text="result.redis.found ? 'Found' : 'Not Found'"></span>
                                    </span>
                                </div>
                                <div x-show="result.redis.found" class="space-y-1">
                                    <div class="flex justify-between">
                                        <span>Key:</span>
                                        <span class="font-mono text-xs" x-text="result.redis.key"></span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>TTL:</span>
                                        <span :class="result.redis.ttl_seconds < 3600 ? 'text-orange-600' : 'text-gray-600'">
                                            <span x-text="formatTTL(result.redis.ttl_seconds)"></span>
                                        </span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>Checksum:</span>
                                        <span class="font-mono text-xs" x-text="result.redis.checksum"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Qdrant -->
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold mb-4 flex items-center">
                            <i class="fas fa-project-diagram text-purple-600 mr-2"></i>Qdrant
                        </h3>
                        <div x-show="result.qdrant">
                            <div class="space-y-2 text-sm">
                                <div class="flex justify-between">
                                    <span>Status:</span>
                                    <span :class="result.qdrant.found ? 'text-green-600' : 'text-red-600'">
                                        <i :class="result.qdrant.found ? 'fas fa-check' : 'fas fa-times'" class="mr-1"></i>
                                        <span x-text="result.qdrant.found ? 'Found' : 'Not Found'"></span>
                                    </span>
                                </div>
                                <div x-show="result.qdrant.found" class="space-y-1">
                                    <div class="flex justify-between">
                                        <span>Key:</span>
                                        <span class="font-mono text-xs" x-text="result.qdrant.key"></span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>Checksum:</span>
                                        <span class="font-mono text-xs" x-text="result.qdrant.checksum"></span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>Updated:</span>
                                        <span x-text="result.qdrant.updated_at"></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        function inspectorApp() {
            return {
                docId: '',
                env: 'prod',
                loading: false,
                result: null,
                health: null,

                async inspectDocument() {
                    if (!this.docId.trim()) return;
                    
                    this.loading = true;
                    try {
                        const response = await fetch(`/admin/inspector/${encodeURIComponent(this.docId)}?env=${this.env}`);
                        this.result = await response.json();
                    } catch (error) {
                        console.error('Inspection failed:', error);
                        alert('Failed to inspect document');
                    } finally {
                        this.loading = false;
                    }
                },

                async checkHealth() {
                    try {
                        const response = await fetch('/admin/inspector/health');
                        this.health = await response.json();
                        console.log('Health check:', this.health);
                    } catch (error) {
                        console.error('Health check failed:', error);
                    }
                },

                getStatusColor(status) {
                    const colors = {
                        'OK': 'bg-green-100 text-green-800',
                        'WARNING': 'bg-yellow-100 text-yellow-800',
                        'ERROR': 'bg-red-100 text-red-800'
                    };
                    return colors[status] || 'bg-gray-100 text-gray-800';
                },

                getStatusIcon(status) {
                    const icons = {
                        'OK': 'fas fa-check-circle',
                        'WARNING': 'fas fa-exclamation-triangle',
                        'ERROR': 'fas fa-times-circle'
                    };
                    return icons[status] || 'fas fa-question-circle';
                },

                formatValue(value) {
                    if (value === null || value === undefined) return '-';
                    if (typeof value === 'object') return JSON.stringify(value);
                    return String(value);
                },

                formatTTL(seconds) {
                    if (seconds === null || seconds === undefined) return 'No TTL';
                    if (seconds === -1) return 'No expiration';
                    if (seconds < 60) return `${seconds}s`;
                    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
                    return `${Math.floor(seconds / 3600)}h`;
                }
            }
        }
    </script>
</body>
</html>
```

### **Phase 3: Integration with Existing Gateway**

#### **3.1 Add Route to Gateway**
```python
# Add to gateway/app.py

@app.get("/admin/inspector")
async def inspector_ui():
    """Serve the Tri-Store Inspector UI"""
    return FileResponse("inspector.html")
```

#### **3.2 Add to Gateway Navigation**
```python
# Add to gateway/app.py - extend existing admin endpoints

@app.get("/admin")
async def admin_dashboard():
    """Admin dashboard with links to all admin tools"""
    return {
        "services": "/admin/services/status",
        "inspector": "/admin/inspector",
        "catalog": "/catalog",
        "health": "/admin/inspector/health"
    }
```

## 🚀 **Benefits of Gateway Integration**

1. **✅ Single Entry Point**: All admin tools accessible from one place
2. **✅ Consistent Security**: Reuse existing auth/authorization
3. **✅ Service Management**: Leverage existing service health monitoring
4. **✅ Easy Deployment**: No additional containers or services
5. **✅ Unified Logging**: All admin actions logged consistently
6. **✅ Resource Efficiency**: Share existing connections and infrastructure

## 📋 **Next Steps**

1. **Implement Phase 1**: Add core inspector API to gateway
2. **Test with Real Data**: Use existing Contract Reviewer documents
3. **Add UI**: Implement the web interface
4. **Security**: Add proper authentication/authorization
5. **Monitoring**: Add metrics and alerting
6. **Documentation**: Create user guide and API docs

This approach leverages the existing gateway infrastructure while providing a powerful data inspection tool for the entire ABS ecosystem.

