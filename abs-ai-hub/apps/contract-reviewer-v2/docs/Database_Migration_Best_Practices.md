# Database Migration Best Practices for Dockerized PostgreSQL

## Overview
This document outlines best practices for running database migrations in a containerized PostgreSQL environment.

## Migration Strategies

### Option 1: Automatic Migration on Startup (Recommended for Development)
Run migrations automatically when the application starts.

**Pros:**
- Simple and automated
- Ensures database is always up-to-date
- Good for development environments

**Cons:**
- Requires running app to migrate
- Can slow down startup time

### Option 2: Separate Migration Container (Recommended for Production)
Create a dedicated container/job that runs migrations independently.

**Pros:**
- Separation of concerns
- Can run migrations independently of application
- Better for CI/CD pipelines
- Explicit control over when migrations run

**Cons:**
- Requires orchestration (docker-compose, K8s jobs)
- More complex setup

### Option 3: Manual Migration (Flexible)
Run migrations manually using scripts or tools.

**Pros:**
- Full control over timing
- Can review migrations before applying

**Cons:**
- Manual process
- Easy to forget

## Recommended Approach

For the Contract Reviewer v2 application, we recommend a **hybrid approach**:

1. **Include migration logic in app startup** (with safety checks)
2. **Provide standalone migration script** for manual/scheduled execution
3. **Create idempotent migrations** that can be run multiple times safely

## Implementation

### 1. Update app_integrated.py to run migrations on startup

Add this to the `initialize_services()` function:

```python
async def initialize_services():
    """Initialize all services"""
    global doc_service, vector_service, processing_service, storage_service, report_service, history_service, redis_client, watch_directory_service, library_files_service
    
    try:
        logger.info("🚀 Initializing Contract Reviewer v2 - Integrated Services")
        
        # Run database migrations first
        await run_migrations()
        
        # Initialize PostgreSQL document service
        logger.info("🔧 Initializing PostgreSQL document service...")
        # ... rest of initialization
```

### 2. Create migration runner function

```python
async def run_migrations():
    """Run database migrations"""
    try:
        logger.info("🔄 Running database migrations...")
        import subprocess
        result = subprocess.run(
            ["python", "migrate_add_source_type.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logger.info("✅ Database migrations completed")
        else:
            logger.warning(f"⚠️ Migration warnings: {result.stderr}")
    except Exception as e:
        logger.warning(f"⚠️ Migration check failed: {e}")
        # Don't fail startup - migrations should be idempotent
```

### 3. Docker Compose Entrypoint Setup

Create a wrapper script that runs migrations before starting the app:

**File:** `entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "🚀 Starting Contract Reviewer v2"

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until pg_isready -h document-hub-postgres -p 5432 -U hub_user; do
  sleep 1
done

echo "✅ PostgreSQL is ready"

# Run migrations
echo "🔄 Running database migrations..."
python migrate_add_source_type.py

# Start the application
echo "🚀 Starting application..."
exec "$@"
```

**Update Dockerfile:**

```dockerfile
# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use entrypoint
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app_integrated:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 4. Docker Compose Configuration

**docker-compose.yml:**

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: document_hub
      POSTGRES_USER: hub_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres-init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hub_user -d document_hub"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      POSTGRES_URL: postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub
      QDRANT_HOST: qdrant
      QDRANT_PORT: 6333
    volumes:
      - ./:/app
      - file_storage:/data/file_storage
```

## Migration Best Practices

### 1. Make Migrations Idempotent

All migrations should be safe to run multiple times:

```sql
-- Good: Checks before adding
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'documents' AND column_name = 'source_type'
    ) THEN
        ALTER TABLE documents ADD COLUMN source_type VARCHAR(20) DEFAULT 'upload';
    END IF;
END $$;
```

### 2. Use Transactions

Wrap migrations in transactions for rollback capability:

```python
async with conn.transaction():
    await conn.execute("ALTER TABLE ...")
    await conn.execute("CREATE TABLE ...")
```

### 3. Version Tracking

Track migration versions:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. Logging

Always log what migrations are running:

```python
logger.info("🔄 Running migration: add_source_type_column")
logger.info("✅ Migration completed successfully")
logger.warning("⚠️ Column already exists, skipping")
```

### 5. Error Handling

Handle errors gracefully:

```python
try:
    await run_migration()
except Exception as e:
    logger.error(f"❌ Migration failed: {e}")
    # Decide whether to fail startup or continue
    raise  # or continue depending on severity
```

## Production Considerations

### 1. Separate Migration Job (Kubernetes)

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
spec:
  template:
    spec:
      containers:
      - name: migration
        image: contract-reviewer:latest
        command: ["python", "migrate_add_source_type.py"]
        env:
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: url
      restartPolicy: Never
```

### 2. Migration in CI/CD

Add to your pipeline:

```yaml
# .github/workflows/deploy.yml
- name: Run Database Migrations
  run: |
    docker-compose run --rm app python migrate_add_source_type.py
```

### 3. Backup Before Migration

```bash
# Create backup before migration
pg_dump -h document-hub-postgres -U hub_user -d document_hub > backup.sql

# Run migration
python migrate_add_source_type.py

# Verify migration
python verify_migration.py
```

### 4. Rollback Strategy

Keep rollback scripts:

```python
# rollback_add_source_type.py
async def rollback():
    """Rollback source_type column addition"""
    await conn.execute("ALTER TABLE documents DROP COLUMN IF EXISTS source_type")
    await conn.execute("DROP TABLE IF EXISTS library_files")
```

## Testing Migrations

### Test Script

```python
# test_migrations.py
import asyncio
import asyncpg

async def test_migrations():
    """Test migrations in a test database"""
    conn = await asyncpg.connect("postgresql://user:pass@localhost/test_db")
    try:
        await conn.execute("CREATE TABLE ...")
        await run_migration()
        # Verify
        result = await conn.fetchval("SELECT column_name FROM ...")
        assert result is not None
    finally:
        await conn.close()
```

## Monitoring

### 1. Add Migration Status Endpoint

```python
@app.get("/api/admin/migration-status")
async def get_migration_status():
    """Get current migration status"""
    async with doc_service.pool.acquire() as conn:
        columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents'
        """)
        has_source_type = any(c['column_name'] == 'source_type' for c in columns)
        return {
            "source_type_column_exists": has_source_type,
            "migration_version": "1.0.0"
        }
```

### 2. Logging

```python
logger.info("Migration started: add_source_type")
logger.info("Migration completed: add_source_type")
logger.warning("Migration skipped (already applied): add_source_type")
logger.error("Migration failed: add_source_type - Error: ...")
```

## Quick Start

For development, the current implementation:

1. **Run migration manually:**
   ```bash
   docker-compose exec app python migrate_add_source_type.py
   ```

2. **Or restart the app** (with auto-migration on startup)

3. **Check migration status:**
   ```bash
   docker-compose exec postgres psql -U hub_user -d document_hub -c "\d documents"
   ```

## Recommended Next Steps

1. **Update `app_integrated.py`** to include `run_migrations()` on startup
2. **Create `entrypoint.sh`** for Docker migration orchestration
3. **Update `docker-compose.yml`** to use entrypoint script
4. **Add migration version tracking** for production deployments
5. **Create rollback scripts** for each migration

## Summary

**Development:**
- Run migrations automatically on app startup
- Keep migrations idempotent
- Log everything

**Production:**
- Run migrations as separate job/step
- Always backup before migrations
- Test migrations in staging first
- Have rollback plans ready




