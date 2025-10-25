#!/usr/bin/env python3
import asyncio
import asyncpg

async def create_analysis_table():
    conn = await asyncpg.connect('postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub')
    
    # Create analysis_results table with correct schema
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS document_hub.analysis_results (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            document_id UUID NOT NULL REFERENCES document_hub.documents(id) ON DELETE CASCADE,
            analysis_type VARCHAR(50) NOT NULL,
            analysis_data JSONB NOT NULL,
            analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            model_used VARCHAR(100),
            processing_time_ms INTEGER,
            confidence_score FLOAT DEFAULT 0.0,
            status VARCHAR(20) DEFAULT 'completed',
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("✅ Created analysis_results table")
    
    # Check columns
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
    asyncio.run(create_analysis_table())
