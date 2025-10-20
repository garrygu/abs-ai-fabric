# Migration Guide: Redis Document Cache to PostgreSQL

This guide explains how to migrate existing document cache data from Redis to PostgreSQL persistence in Contract Reviewer v2.

## Overview

The migration process transfers:
- **Document metadata** from Redis to PostgreSQL
- **Analysis results** from Redis to PostgreSQL  
- **File references** and metadata
- **User sessions** and audit information

## Prerequisites

### 1. System Requirements
- PostgreSQL service running and accessible
- Redis service running (source data)
- Python 3.8+ with required dependencies
- Sufficient disk space for migrated data

### 2. Dependencies
```bash
# Install required packages
pip install redis asyncpg psycopg2-binary

# Or use the requirements file
pip install -r document_requirements.txt
```

### 3. Database Setup
Ensure PostgreSQL is running and accessible:
```bash
# Check PostgreSQL status
docker exec document-hub-postgres pg_isready -U hub_user -d document_hub

# Verify database exists
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT COUNT(*) FROM document_hub.documents;"
```

## Migration Methods

### Method 1: Simple Migration Script (Recommended)

#### Step 1: Run Simple Migration
```bash
cd abs-ai-hub/apps/contract-reviewer-v2
python simple_migration.py
```

#### Step 2: Follow Interactive Prompts
```
🚀 Contract Reviewer v2 - Redis to PostgreSQL Migration
============================================================

Migration Settings:
Migrate files? (y/n): y
Source directory (default: /tmp/contract-reviewer-v2/uploads): 
Target directory (default: /var/lib/postgresql/data/migrated_files): 
Perform dry run first? (y/n): y
```

#### Step 3: Review Dry Run Results
```
🔍 Running dry run...
Discovery results:
  Total Redis Keys: 25
  Document Keys: 10
  Analysis Keys: 10
  Session Keys: 5

Dry run results: {...}
```

#### Step 4: Run Actual Migration
```
🚀 Running actual migration...
Migration completed!
Results: {...}
```

### Method 2: Advanced Migration Tool

#### Step 1: Configure Migration
```bash
# Edit migration configuration
nano migration_config.yml
```

#### Step 2: Run Advanced Migration
```bash
python migrate_redis_to_postgres.py \
  --redis-url "redis://localhost:6379" \
  --postgres-url "postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub" \
  --migrate-files \
  --source-dir "/tmp/contract-reviewer-v2/uploads" \
  --target-dir "/var/lib/postgresql/data/migrated_files"
```

#### Step 3: Validate Migration
```bash
python migrate_redis_to_postgres.py --validate
```

#### Step 4: Cleanup Redis (Optional)
```bash
python migrate_redis_to_postgres.py --cleanup
```

### Method 3: FastAPI Integration

#### Step 1: Add Migration Endpoints
```python
from simple_migration import create_migration_endpoints

# Add to your FastAPI app
create_migration_endpoints(app)
```

#### Step 2: Use REST API
```bash
# Run migration via API
curl -X POST "http://localhost:8000/api/migration/run" \
  -H "Content-Type: application/json" \
  -d '{
    "migrate_files": true,
    "source_dir": "/tmp/contract-reviewer-v2/uploads",
    "target_dir": "/var/lib/postgresql/data/migrated_files",
    "dry_run": false
  }'

# Validate migration
curl -X POST "http://localhost:8000/api/migration/validate"

# Cleanup Redis
curl -X POST "http://localhost:8000/api/migration/cleanup" \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

## Migration Process Details

### Phase 1: Discovery
The migration tool discovers all Redis data:
- **Document keys**: `document:*`
- **Analysis keys**: `analysis:*`
- **Session keys**: `session:*`
- **Other keys**: Miscellaneous data

### Phase 2: Document Migration
For each document in Redis:
1. **Extract metadata**: filename, file_path, file_size, upload_timestamp
2. **Create PostgreSQL record**: Insert into `documents` table
3. **Preserve relationships**: Maintain document ID relationships
4. **Add migration metadata**: Track Redis key and migration timestamp

### Phase 3: Analysis Migration
For each analysis in Redis:
1. **Extract analysis data**: summary, risks, recommendations, key_points
2. **Find corresponding document**: Match by Redis document ID
3. **Create PostgreSQL record**: Insert into `analysis_results` table
4. **Preserve analysis metadata**: model_used, processing_time_ms

### Phase 4: File Migration (Optional)
If file migration is enabled:
1. **Copy files**: From source directory to target directory
2. **Preserve structure**: Maintain directory hierarchy
3. **Update paths**: Update file_path references in PostgreSQL
4. **Validate files**: Ensure file integrity

### Phase 5: Validation
The migration tool validates:
- **Data integrity**: All Redis data migrated to PostgreSQL
- **File existence**: All referenced files exist
- **Relationships**: Analysis results linked to correct documents
- **Counts match**: Document and analysis counts are consistent

## Data Mapping

### Redis to PostgreSQL Field Mapping

#### Documents
| Redis Field | PostgreSQL Field | Notes |
|-------------|------------------|-------|
| `filename` | `original_filename` | Original filename from upload |
| `file_path` | `file_path` | Path to file on disk |
| `file_size` | `file_size` | File size in bytes |
| `upload_timestamp` | `upload_timestamp` | When file was uploaded |
| `metadata` | `metadata` | Additional metadata (JSONB) |

#### Analysis Results
| Redis Field | PostgreSQL Field | Notes |
|-------------|------------------|-------|
| `document_id` | `document_id` | Reference to documents table |
| `analysis` | `analysis_data` | Analysis results (JSONB) |
| `model_used` | `model_used` | AI model used for analysis |
| `processing_time_ms` | `processing_time_ms` | Time taken for analysis |

### Migration Metadata
Each migrated record includes:
```json
{
  "migrated_from_redis": true,
  "redis_key": "document:uuid",
  "redis_document_id": "uuid",
  "migration_timestamp": "2024-01-01T00:00:00"
}
```

## Error Handling

### Common Issues and Solutions

#### 1. File Not Found
```
⚠️ File not found: /tmp/contract-reviewer-v2/uploads/contract.pdf
```
**Solution**: Check file paths and ensure files exist before migration

#### 2. Invalid JSON Data
```
⚠️ Invalid JSON for key: document:uuid
```
**Solution**: Check Redis data integrity, may need to clean corrupted data

#### 3. Database Connection Issues
```
❌ Failed to connect to PostgreSQL: connection refused
```
**Solution**: Ensure PostgreSQL service is running and accessible

#### 4. Missing Document References
```
⚠️ Could not find migrated document for analysis: analysis:uuid
```
**Solution**: Ensure documents are migrated before analyses

### Error Recovery
The migration tool provides:
- **Detailed error logging**: All errors are logged with context
- **Partial migration support**: Continue migration despite errors
- **Rollback capability**: Can undo partial migrations
- **Validation reports**: Identify what was successfully migrated

## Performance Considerations

### Large Dataset Migration
For large datasets (>1000 documents):
1. **Use batch processing**: Process documents in batches
2. **Monitor memory usage**: Large datasets may require more memory
3. **Consider downtime**: Plan for maintenance window
4. **Test performance**: Run performance tests first

### Performance Optimization
```python
# Use connection pooling
migration = DocumentCacheMigration()
await migration.initialize()

# Process in batches
batch_size = 100
for i in range(0, len(documents), batch_size):
    batch = documents[i:i + batch_size]
    await migration.migrate_documents(batch)
```

## Testing Migration

### Run Migration Tests
```bash
# Run comprehensive test suite
python test_migration.py

# Run specific tests
python -m pytest test_migration.py::MigrationTester::test_discovery -v
python -m pytest test_migration.py::MigrationTester::test_document_migration -v
```

### Test Coverage
The test suite covers:
- **Data discovery**: Finding all Redis data
- **Document migration**: Migrating document metadata
- **Analysis migration**: Migrating analysis results
- **File migration**: Copying files to new location
- **Validation**: Ensuring migration integrity
- **Performance**: Testing with large datasets

## Post-Migration Steps

### 1. Update Application Configuration
```python
# Update app.py to use PostgreSQL instead of Redis
from document_service import DocumentService

# Replace Redis-only operations with PostgreSQL
doc_service = DocumentService()
await doc_service.initialize()
```

### 2. Verify Data Integrity
```sql
-- Check document counts
SELECT COUNT(*) FROM document_hub.documents;

-- Check analysis counts
SELECT COUNT(*) FROM document_hub.analysis_results;

-- Check migration metadata
SELECT COUNT(*) FROM document_hub.documents 
WHERE metadata->>'migrated_from_redis' = 'true';
```

### 3. Update File Paths
If files were migrated:
```python
# Update file paths in application
for document in documents:
    old_path = document['file_path']
    new_path = f"/var/lib/postgresql/data/migrated_files/{document['filename']}"
    
    # Update in PostgreSQL
    await doc_service.update_document(
        document_id=document['id'],
        updates={"file_path": new_path}
    )
```

### 4. Clean Up Redis (Optional)
After successful migration and verification:
```bash
# Clean up Redis data
python migrate_redis_to_postgres.py --cleanup
```

## Monitoring and Maintenance

### Migration Reports
Each migration generates:
- **Detailed JSON report**: Complete migration results
- **Human-readable summary**: Key metrics and status
- **Error logs**: Detailed error information
- **Performance metrics**: Timing and throughput data

### Ongoing Monitoring
```python
# Check migration status
from simple_migration import SimpleMigration

migration = SimpleMigration()
validation = await migration.validate_migration()

print(f"Migration status: {validation['validation_passed']}")
print(f"Documents: {validation['postgres_documents']}")
print(f"Analyses: {validation['postgres_analyses']}")
```

## Troubleshooting

### Common Problems

#### Migration Fails to Start
- Check PostgreSQL connection
- Verify Redis is accessible
- Ensure sufficient disk space
- Check file permissions

#### Partial Migration
- Review error logs
- Fix data issues
- Re-run migration for failed items
- Validate partial results

#### Performance Issues
- Reduce batch size
- Increase connection pool size
- Check database performance
- Monitor system resources

### Getting Help
1. **Check logs**: Review migration logs for detailed error information
2. **Run tests**: Use test suite to identify issues
3. **Validate data**: Ensure source data is clean and valid
4. **Check configuration**: Verify all settings are correct

## Best Practices

### Before Migration
1. **Backup data**: Create backups of Redis and PostgreSQL
2. **Test migration**: Run dry run and test with sample data
3. **Plan downtime**: Schedule maintenance window if needed
4. **Verify prerequisites**: Ensure all requirements are met

### During Migration
1. **Monitor progress**: Watch for errors and performance issues
2. **Validate incrementally**: Check results at each phase
3. **Maintain backups**: Keep backups until migration is verified
4. **Document issues**: Record any problems for future reference

### After Migration
1. **Verify data**: Run validation checks
2. **Update applications**: Modify code to use PostgreSQL
3. **Monitor performance**: Watch for any issues
4. **Clean up**: Remove old Redis data after verification

## Conclusion

The migration from Redis to PostgreSQL provides:
- **Persistent storage**: Data survives application restarts
- **Better performance**: Optimized queries and indexing
- **Scalability**: Handle larger datasets efficiently
- **Data integrity**: ACID compliance and relationships
- **Audit trail**: Complete history of all operations

Follow this guide to successfully migrate your document cache and enjoy the benefits of PostgreSQL persistence.
