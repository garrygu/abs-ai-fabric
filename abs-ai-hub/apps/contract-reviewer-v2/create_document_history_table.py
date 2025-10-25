#!/usr/bin/env python3
"""
Create document_history table for tracking all document handling events
"""
import asyncio
import asyncpg

async def create_document_history_table():
    """Create document_history table for audit trail"""
    conn = await asyncpg.connect('postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub')
    
    try:
        # Create document_history table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS document_hub.document_history (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                document_id UUID NOT NULL REFERENCES document_hub.documents(id) ON DELETE CASCADE,
                event_type VARCHAR(50) NOT NULL,
                event_status VARCHAR(20) NOT NULL DEFAULT 'success',
                event_description TEXT,
                event_data JSONB,
                user_id VARCHAR(100),
                session_id VARCHAR(100),
                processing_time_ms INTEGER,
                error_message TEXT,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ Created document_history table")
        
        # Create indexes for better performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_history_document_id 
            ON document_hub.document_history(document_id)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_history_event_type 
            ON document_hub.document_history(event_type)
        """)
        
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_history_created_at 
            ON document_hub.document_history(created_at)
        """)
        
        print("✅ Created indexes for document_history table")
        
        # Check table structure
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'document_hub' 
            AND table_name = 'document_history'
            ORDER BY ordinal_position
        """)
        
        print('\n📋 document_history table columns:')
        for col in columns:
            print(f'  - {col["column_name"]} ({col["data_type"]}) - nullable: {col["is_nullable"]} - default: {col["column_default"]}')
        
    except Exception as e:
        print(f"❌ Error creating document_history table: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_document_history_table())

