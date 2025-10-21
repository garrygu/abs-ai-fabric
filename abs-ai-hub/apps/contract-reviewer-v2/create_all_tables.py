#!/usr/bin/env python3
import asyncio
import asyncpg

async def create_all_tables():
    conn = await asyncpg.connect('postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub')
    
    # Create audit_logs table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS document_hub.audit_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID,
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id VARCHAR(255),
            details JSONB,
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("✅ Created audit_logs table")
    
    # Create users table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS document_hub.users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            role VARCHAR(50) DEFAULT 'user',
            is_active BOOLEAN DEFAULT true,
            last_login TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("✅ Created users table")
    
    # Create user_sessions table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS document_hub.user_sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES document_hub.users(id) ON DELETE CASCADE,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("✅ Created user_sessions table")
    
    # Create document_chunks table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS document_hub.document_chunks (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            document_id UUID NOT NULL REFERENCES document_hub.documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            chunk_metadata JSONB,
            vector_id VARCHAR(255),
            embedding_model VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("✅ Created document_chunks table")
    
    # Check all tables
    tables = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'document_hub'
        ORDER BY table_name
    """)
    
    print('📋 All tables:')
    for table in tables:
        print(f'  - {table["table_name"]}')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(create_all_tables())
