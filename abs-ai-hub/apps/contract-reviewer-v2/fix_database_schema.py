#!/usr/bin/env python3
"""
Fix Database Schema Script
This script drops and recreates the database with the correct schema
"""

import asyncio
import asyncpg
import os
from pathlib import Path

# Database connection details
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://hub_user:secure_password@localhost:5432/document_hub")

async def fix_database_schema():
    """Drop and recreate the database schema"""
    print("🔧 Fixing database schema...")
    
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(POSTGRES_URL)
        print("✅ Connected to PostgreSQL")
        
        # Drop existing tables (in correct order due to foreign keys)
        print("🗑️ Dropping existing tables...")
        await conn.execute("DROP TABLE IF EXISTS document_hub.audit_logs CASCADE")
        await conn.execute("DROP TABLE IF EXISTS document_hub.user_sessions CASCADE")
        await conn.execute("DROP TABLE IF EXISTS document_hub.document_chunks CASCADE")
        await conn.execute("DROP TABLE IF EXISTS document_hub.analysis_results CASCADE")
        await conn.execute("DROP TABLE IF EXISTS document_hub.documents CASCADE")
        await conn.execute("DROP TABLE IF EXISTS document_hub.users CASCADE")
        
        # Drop schema if it exists
        await conn.execute("DROP SCHEMA IF EXISTS document_hub CASCADE")
        print("✅ Dropped existing schema and tables")
        
        # Create schema
        await conn.execute("CREATE SCHEMA IF NOT EXISTS document_hub")
        print("✅ Created document_hub schema")
        
        # Read and execute the SQL initialization script
        sql_file = Path(__file__).parent / "postgres-init" / "01-init-integrated.sql"
        if sql_file.exists():
            print(f"📄 Reading SQL script: {sql_file}")
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            print(f"📄 SQL content length: {len(sql_content)} characters")
            print(f"📄 First 200 characters: {sql_content[:200]}")
            
            # Split SQL into individual statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            print(f"📄 Found {len(statements)} SQL statements")
            
            # Execute each statement
            for i, statement in enumerate(statements):
                if statement:
                    print(f"📄 Executing statement {i+1}: {statement[:50]}...")
                    try:
                        await conn.execute(statement)
                        print(f"✅ Statement {i+1} executed successfully")
                    except Exception as e:
                        print(f"❌ Error executing statement {i+1}: {e}")
                        print(f"Statement: {statement}")
            
            print("✅ Executed SQL initialization script")
        else:
            print(f"❌ SQL file not found: {sql_file}")
            return False
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'document_hub'
            ORDER BY table_name
        """)
        
        print("📋 Created tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Verify analysis_results table has all required columns
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'document_hub' 
            AND table_name = 'analysis_results'
            ORDER BY ordinal_position
        """)
        
        print("📋 analysis_results table columns:")
        for col in columns:
            print(f"  - {col['column_name']} ({col['data_type']})")
        
        # Check for required columns
        required_columns = ['id', 'document_id', 'analysis_type', 'analysis_data', 
                          'analysis_timestamp', 'model_used', 'processing_time_ms', 
                          'status', 'metadata', 'created_at', 'updated_at']
        
        existing_columns = [col['column_name'] for col in columns]
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        else:
            print("✅ All required columns present")
        
        await conn.close()
        print("✅ Database schema fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_database_schema())
    if success:
        print("\n🎉 Database schema has been fixed!")
        print("You can now restart the application.")
    else:
        print("\n💥 Failed to fix database schema!")
        exit(1)
