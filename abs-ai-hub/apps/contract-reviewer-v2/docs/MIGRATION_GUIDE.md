# Database Migration Guide

## Quick Start

### Option 1: Automatic Migration (Development - Recommended)

The application will automatically run migrations on startup:

```bash
docker-compose up
```

### Option 2: Manual Migration

If you prefer to run migrations manually:

```bash
# Using Docker
docker-compose exec app python migrate_add_source_type.py

# Or directly
python migrate_add_source_type.py
```

### Option 3: Standalone Migration Container (Production)

```bash
docker-compose run --rm migration python migrate_add_source_type.py
```

## Migration Scripts

### migrate_add_source_type.py

Adds the Document Library feature to the database:
- Adds `source_type` column to `documents` table
- Creates `library_files` table
- Creates necessary indexes

**Usage:**
```bash
python migrate_add_source_type.py
```

**Features:**
- Idempotent (safe to run multiple times)
- Creates tables/columns if they don't exist
- Logs all operations

## Migration Status

Check if migrations have been applied:

```bash
# Using docker-compose
docker-compose exec postgres psql -U hub_user -d document_hub -c "\d documents"

# Should show source_type column in the output
```

Or check programmatically:

```bash
python -c "
import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://hub_user:secure_password@localhost:5432/document_hub')
    col = await conn.fetchval(\"\"\"
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'documents' AND column_name = 'source_type'
    \"\"\")
    print('✅ source_type column exists' if col else '❌ source_type column missing')
    await conn.close()

asyncio.run(check())
"
```

## Rollback

To rollback the Document Library migration:

```sql
-- Connect to database
docker-compose exec postgres psql -U hub_user -d document_hub

-- Run rollback SQL
ALTER TABLE documents DROP COLUMN IF EXISTS source_type;
DROP TABLE IF EXISTS library_files;
DROP TABLE IF EXISTS processed_watch_files;

-- Verify
\dt  -- Should not show library_files
\d documents  -- Should not show source_type column
```

## Best Practices

1. **Always backup before migrations:**
   ```bash
   docker-compose exec postgres pg_dump -U hub_user document_hub > backup.sql
   ```

2. **Test in development first**

3. **Check migration status before deployment**

4. **Monitor logs during migration**

5. **Verify after migration**

## Troubleshooting

### Migration Fails with "Column Already Exists"

This is normal - the migration is idempotent and checks before creating.

### "Connection Refused"

Ensure PostgreSQL is running:
```bash
docker-compose ps postgres
```

Wait for it to be ready:
```bash
docker-compose exec postgres pg_isready
```

### "Permission Denied"

Check PostgreSQL user permissions:
```bash
docker-compose exec postgres psql -U hub_user -d document_hub -c "\du"
```

## Production Deployment

For production environments:

1. **Create a backup:**
   ```bash
   pg_dump -h production-db -U hub_user document_hub > pre-migration-backup.sql
   ```

2. **Run migration during deployment:**
   ```bash
   # In CI/CD pipeline
   python migrate_add_source_type.py
   ```

3. **Verify migration:**
   ```bash
   # Check logs
   # Verify schema
   # Run smoke tests
   ```

4. **Monitor application logs**

## Migration Sequence

When the application starts:

1. Wait for PostgreSQL to be ready
2. Run migrations (migrate_add_source_type.py)
3. Initialize services
4. Start application

You can see this in the logs:
```
🚀 Initializing Contract Reviewer v2 - Integrated Services
🔄 Running database migrations on startup...
✅ Database migrations completed successfully
🔧 Initializing PostgreSQL document service...
...
✅ All services initialized successfully!
```

## Manual Migration Execution

If automatic migration fails, run manually:

```bash
# Get into the container
docker-compose exec app bash

# Run migration
python migrate_add_source_type.py

# Check status
python -c "
import asyncio
import asyncpg
from pathlib import Path

async def check():
    conn = await asyncpg.connect('postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub')
    
    # Check source_type column
    col = await conn.fetchval(\"\"\"
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'documents' AND column_name = 'source_type'
    \"\"\")
    print('source_type column:', '✅ exists' if col else '❌ missing')
    
    # Check library_files table
    table = await conn.fetchval(\"\"\"
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'library_files'
    \"\"\")
    print('library_files table:', '✅ exists' if table else '❌ missing')
    
    await conn.close()

asyncio.run(check())
"
```

## Next Steps

After migration:
1. Verify the schema is updated
2. Restart the application
3. Check the Document Library tab in the UI
4. Test adding a watch directory


