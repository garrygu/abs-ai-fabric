#!/usr/bin/env python3
import asyncio
import asyncpg

async def create_tables():
    conn = await asyncpg.connect('postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub')
    
    # Create documents table first
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS document_hub.documents (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            file_size BIGINT NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            mime_type VARCHAR(100),
            upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            analysis_timestamp TIMESTAMP WITH TIME ZONE,
            status VARCHAR(20) DEFAULT 'uploaded',
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("✅ Created documents table")
    
    # Create analysis_results table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS document_hub.analysis_results (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            document_id UUID NOT NULL REFERENCES document_hub.documents(id) ON DELETE CASCADE,
            analysis_type VARCHAR(50) NOT NULL,
            analysis_data JSONB NOT NULL,
            analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            model_used VARCHAR(100),
            processing_time_ms INTEGER,
            status VARCHAR(20) DEFAULT 'completed',
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("✅ Created analysis_results table")
    
    # Check tables
    tables = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'document_hub'
        ORDER BY table_name
    """)
    
    print('📋 Tables:')
    for table in tables:
        print(f'  - {table["table_name"]}')
    
    # Check analysis_results columns
    columns = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'document_hub' 
        AND table_name = 'analysis_results'
        ORDER BY ordinal_position
    """)
    
    print('📋 analysis_results columns:')
    for col in columns:
        print(f'  - {col["column_name"]} ({col["data_type"]})')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())
