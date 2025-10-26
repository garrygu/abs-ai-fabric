# Database Schema Design Guidelines for ABS AI Hub

## Overview

This document establishes the **database schema design guidelines** for all applications in the ABS AI Hub ecosystem. These guidelines ensure proper data isolation, security, and maintainability across multiple apps sharing the same PostgreSQL instance.

---

## 1. Core Principle: One Schema Per Application

### ✅ **Requirement: Each app gets its own PostgreSQL schema**

**Why?**
- **Data Isolation**: Each app's data is completely separate from others
- **Security**: Apps can only access their own data (with proper permissions)
- **Maintenance**: Easy to backup, restore, or delete app data independently
- **Scalability**: Add new apps without affecting existing ones
- **Team Collaboration**: Multiple teams can work independently
- **Compliance**: Easier to audit and control data access

### ❌ **Anti-Pattern: All apps sharing the `public` schema**

**Why not?**
- Risk of naming conflicts across apps
- Harder to isolate app data
- Difficult to manage permissions
- Harder to clean up or migrate a single app
- Poor separation of concerns

---

## 2. Naming Convention

### Schema Name Format

```
app_id = snake_case version of the app's unique ID
database_schema = app_id
```

### Examples

| App ID | Schema Name | Example |
|--------|-------------|---------|
| `contract-reviewer-v2` | `document_hub` | `document_hub.documents` |
| `legal-assistant` | `legal_assistant` | `legal_assistant.cases` |
| `rag-pdf-voice` | `rag_pdf_voice` | `rag_pdf_voice.sessions` |
| `whisper-server` | `whisper_server` | `whisper_server.transcriptions` |

### Naming Rules
- ✅ Use `snake_case` (lowercase with underscores)
- ✅ Match app's registry `id` but replace hyphens with underscores
- ✅ Keep it short and descriptive
- ❌ Avoid special characters or spaces
- ❌ No uppercase letters

---

## 3. Schema Configuration

### Apps Registry Configuration

Every app in `apps-registry.json` **MUST** specify its `database_schema`:

```json
{
  "name": "Contract Reviewer v2",
  "id": "contract-reviewer-v2",
  "category": "Legal Apps",
  "description": "Professional AI-powered contract analysis platform.",
  "database_schema": "document_hub",  // ⬅️ REQUIRED
  "port": 8082,
  "path": "apps/contract-reviewer-v2"
}
```

### Environment Variable Configuration

Apps **MUST** connect to their assigned schema:

```yaml
# docker-compose.yml
environment:
  POSTGRES_URL=postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub
  # Schema is specified in connection string OR via search_path
```

---

## 4. Schema Creation

### Automatic Schema Creation (Recommended)

Apps should create their own schema during initialization:

```python
# app_integrated.py
async def create_app_schema():
    """Create app-specific schema if it doesn't exist"""
    async with pool.acquire() as conn:
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {APP_SCHEMA}")
        await conn.execute(f"SET search_path TO {APP_SCHEMA}, public")
        logger.info(f"✅ Created schema: {APP_SCHEMA}")
```

### Manual Schema Creation (Alternative)

```sql
-- Connect to shared PostgreSQL
psql -U hub_user -d document_hub

-- Create schema for new app
CREATE SCHEMA IF NOT EXISTS legal_assistant;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA legal_assistant TO hub_user;
```

---

## 5. Query Patterns

### Always Use Schema Qualification (Explicit)

```python
# ✅ CORRECT: Explicit schema
async with pool.acquire() as conn:
    result = await conn.fetch("""
        SELECT * FROM document_hub.documents 
        WHERE status = $1
    """, 'analyzed')
```

### Set Search Path (Implicit - Alternative)

```python
# ✅ CORRECT: Set search path
async with pool.acquire() as conn:
    await conn.execute("SET search_path TO document_hub, public")
    result = await conn.fetch("""
        SELECT * FROM documents 
        WHERE status = $1
    """, 'analyzed')
```

### ❌ Anti-Pattern: No Schema Qualification

```python
# ❌ WRONG: Assumes default schema
async with pool.acquire() as conn:
    result = await conn.fetch("""
        SELECT * FROM documents  # Which schema?!
        WHERE status = $1
    """, 'analyzed')
```

---

## 6. Cross-Schema Access

### When Apps Need Shared Data

If apps need to share data, create a **shared schema**:

```sql
-- Create shared schema for cross-app data
CREATE SCHEMA IF NOT EXISTS shared;

-- App A writes to shared
INSERT INTO shared.documents (app_source, document_id, metadata)
VALUES ('contract-reviewer', 'abc123', '{"type": "contract"}');

-- App B reads from shared
SELECT * FROM shared.documents WHERE app_source = 'contract-reviewer';
```

### Cross-App Communication Pattern

```python
# App A writes to shared schema
await pool.execute("""
    INSERT INTO shared.document_registry 
    (app_id, document_id, document_type, metadata)
    VALUES ($1, $2, $3, $4)
""", 'contract-reviewer', doc_id, 'contract', metadata_json)

# App B reads from shared schema
result = await pool.fetch("""
    SELECT * FROM shared.document_registry 
    WHERE app_id = $1
""", 'legal-assistant')
```

---

## 7. Schema Management

### Current Schema Map

```
PostgreSQL Instance: document-hub-postgres
├── public (Legacy - to be removed)
├── document_hub (Contract Reviewer v2) ✅ Active
└── Future:
    ├── legal_assistant (Legal Assistant app)
    ├── rag_pdf_voice (RAG PDF Voice app)
    ├── whisper_server (Whisper Server app)
    └── shared (Cross-app shared data)
```

### Listing All Schemas

```sql
SELECT schema_name, schema_owner 
FROM information_schema.schemata 
WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY schema_name;
```

### Removing an App's Schema

```sql
-- ⚠️ DANGER: This deletes ALL data for the app!
DROP SCHEMA legal_assistant CASCADE;
```

---

## 8. Best Practices

### ✅ DO:

1. **Always specify schema in queries**: `SELECT * FROM my_schema.table`
2. **Create schema on app startup**: Initialize schema in app code
3. **Use schema name in environment variables**: Make it explicit
4. **Document schema in apps-registry.json**: Keep it consistent
5. **Use shared schema for cross-app data**: Don't access other apps' schemas directly
6. **Grant minimal permissions**: Only grant what each app needs

### ❌ DON'T:

1. **Don't use `public` schema**: It's a legacy holdover, not for your data
2. **Don't access other apps' schemas directly**: Use shared schema instead
3. **Don't create schemas manually without documentation**: Always update registry
4. **Don't hardcode schema names in queries**: Use environment variables
5. **Don't share credentials across apps**: Each app should have its own user

---

## 9. Migration Guide

### Migrating from `public` to App Schema

```sql
-- Step 1: Create new schema
CREATE SCHEMA IF NOT EXISTS document_hub;

-- Step 2: Copy tables
CREATE TABLE document_hub.documents AS TABLE public.documents;

-- Step 3: Migrate data
INSERT INTO document_hub.documents 
SELECT * FROM public.documents;

-- Step 4: Update app code to use new schema

-- Step 5: Drop old schema (after verification)
DROP SCHEMA public CASCADE;
```

### Adding Schema to Existing App

```python
# Add to apps-registry.json
{
  "database_schema": "my_app_schema"
}

# Update environment variable
POSTGRES_URL=postgresql://hub_user:password@host:5432/document_hub

# Update queries in app code
# Change: FROM documents
# To: FROM my_app_schema.documents
```

---

## 10. Troubleshooting

### Problem: "Schema does not exist"

```sql
-- Check if schema exists
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'document_hub';

-- Create schema
CREATE SCHEMA IF NOT EXISTS document_hub;
```

### Problem: "Permission denied for schema"

```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA document_hub TO hub_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA document_hub TO hub_user;
```

### Problem: "Table does not exist in schema"

```sql
-- Check tables in schema
SELECT table_name FROM information_schema.tables WHERE table_schema = 'document_hub';

-- Create missing table
CREATE TABLE document_hub.documents (...);
```

---

## 11. Reference

### Quick Reference Card

```sql
-- Create schema
CREATE SCHEMA IF NOT EXISTS my_app_schema;

-- Set search path
SET search_path TO my_app_schema, public;

-- List schemas
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name NOT IN ('pg_catalog', 'information_schema');

-- List tables in schema
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'my_app_schema';

-- Drop schema (DANGER: deletes all data)
DROP SCHEMA my_app_schema CASCADE;
```

### Code Example

```python
# app_integrated.py
import os
from asyncpg import create_pool

APP_SCHEMA = os.getenv('DATABASE_SCHEMA', 'my_app_schema')
POSTGRES_URL = os.getenv('POSTGRES_URL')

async def initialize_database():
    """Initialize app-specific schema"""
    pool = await create_pool(POSTGRES_URL)
    
    async with pool.acquire() as conn:
        # Create schema
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {APP_SCHEMA}")
        
        # Set search path
        await conn.execute(f"SET search_path TO {APP_SCHEMA}, public")
        
        # Create tables
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {APP_SCHEMA}.documents (
                id UUID PRIMARY KEY,
                filename VARCHAR(255),
                ...
            )
        """)
    
    return pool
```

---

## 12. Summary

### Key Points

✅ **Each app = one schema**  
✅ **Schema name = snake_case app_id**  
✅ **Always qualify tables with schema**  
✅ **Document schema in apps-registry.json**  
✅ **Create shared schema for cross-app data**  
✅ **Grant minimal permissions**

### Checklist for New App

- [ ] Add `database_schema` to `apps-registry.json`
- [ ] Create schema in initialization code
- [ ] Update queries to use qualified names
- [ ] Set up environment variables
- [ ] Update connection string
- [ ] Document in README

---

**Last Updated**: October 25, 2025  
**Version**: 1.0.0  
**Status**: Active

