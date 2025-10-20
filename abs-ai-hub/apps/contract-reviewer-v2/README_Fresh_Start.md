# Fresh PostgreSQL Implementation

## Overview

Since there's almost no data in Redis yet, we're taking a **clean slate approach**:
1. **Clear all Redis data** 
2. **Implement fresh PostgreSQL-first architecture**
3. **Use Redis only for caching** (not primary storage)

## Quick Start

### 1. Clear Redis Data
```bash
cd abs-ai-hub/apps/contract-reviewer-v2

# Simple Redis cleanup
python clear_redis.py

# Or comprehensive cleanup with verification
python redis_cleanup_and_fresh_start.py
```

### 2. Verify PostgreSQL is Running
```bash
# Check PostgreSQL container
docker exec document-hub-postgres pg_isready -U hub_user -d document_hub

# Check database tables
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT COUNT(*) FROM document_hub.documents;"
```

### 3. Run Fresh Implementation
```bash
# Use the new PostgreSQL-first app
python app_postgresql_first.py
```

## Architecture

### **PostgreSQL (Primary Storage)**
- ✅ Document metadata and file information
- ✅ Complete analysis results
- ✅ User accounts and permissions
- ✅ Audit logs and compliance data
- ✅ Document relationships

### **Redis (Caching Only)**
- ✅ Cached API responses (5 minutes)
- ✅ Cached document info (1 hour)
- ✅ Cached analysis results (7 days)
- ✅ Session data (1 hour)
- ✅ Rate limiting counters

### **Qdrant (Vector Search)**
- ✅ Document text chunks as vectors
- ✅ Semantic search and similarity
- ✅ Cross-document analysis

## Key Benefits

1. **Clean Architecture**: No migration complexity
2. **PostgreSQL First**: All data persisted properly
3. **Redis Caching**: Fast access for frequently used data
4. **No Data Loss**: Everything stored in PostgreSQL
5. **Easy Debugging**: Clear separation of concerns

## Implementation Details

### **Document Upload**
```python
# 1. Save file to disk
# 2. Create document record in PostgreSQL
# 3. Cache document info in Redis
```

### **Document Analysis**
```python
# 1. Check if analysis exists in PostgreSQL
# 2. If not, perform analysis
# 3. Save analysis result to PostgreSQL
# 4. Cache analysis result in Redis
```

### **Document Retrieval**
```python
# 1. Check Redis cache first (fast)
# 2. If cache miss, query PostgreSQL
# 3. Cache result in Redis
# 4. Return to user
```

## Testing

### **Test Redis Cleanup**
```bash
python clear_redis.py
```

### **Test Fresh Implementation**
```bash
python quick_cleanup_and_start.py
```

### **Test Full App**
```bash
python app_postgresql_first.py
```

## Migration from Old App

### **Replace Old App**
```bash
# Backup old app.py
mv app.py app_old.py

# Use new PostgreSQL-first app
mv app_postgresql_first.py app.py
```

### **Update Dependencies**
```bash
# Add PostgreSQL dependencies
pip install asyncpg psycopg2-binary

# Or use requirements file
pip install -r document_requirements.txt
```

## Monitoring

### **Check Service Status**
```bash
# Health check
curl http://localhost:8080/api/health

# Statistics
curl http://localhost:8080/api/stats
```

### **Check Redis Usage**
```bash
# Redis info
docker exec redis redis-cli info

# Redis keys
docker exec redis redis-cli keys "*"
```

### **Check PostgreSQL Usage**
```bash
# Database size
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT pg_size_pretty(pg_database_size('document_hub'));"

# Table counts
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT COUNT(*) FROM document_hub.documents; SELECT COUNT(*) FROM document_hub.analysis_results;"
```

## Troubleshooting

### **Redis Connection Issues**
```bash
# Check Redis container
docker ps | grep redis

# Test Redis connection
docker exec redis redis-cli ping
```

### **PostgreSQL Connection Issues**
```bash
# Check PostgreSQL container
docker ps | grep postgres

# Test PostgreSQL connection
docker exec document-hub-postgres pg_isready -U hub_user -d document_hub
```

### **App Startup Issues**
```bash
# Check logs
python app_postgresql_first.py

# Test individual components
python -c "from document_service import DocumentService; print('Document service import OK')"
```

## Next Steps

1. **Clear Redis data** using the cleanup scripts
2. **Test PostgreSQL connection** and verify tables exist
3. **Run fresh implementation** with `app_postgresql_first.py`
4. **Verify functionality** by uploading and analyzing documents
5. **Monitor performance** and cache hit rates
6. **Replace old app** when satisfied with new implementation

This approach gives you a clean, PostgreSQL-first architecture with Redis caching for optimal performance!
