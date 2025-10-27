#!/usr/bin/env python3
"""
Migration script to add source_type column to documents table
Supports the Document Library feature by tracking document origins
"""

import asyncio
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_add_source_type():
    """Add source_type column to documents table"""
    database_url = "postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub"
    
    try:
        conn = await asyncpg.connect(database_url)
        
        logger.info("🔧 Adding source_type column to documents table...")
        
        # Check if column already exists in document_hub schema
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_schema = 'document_hub'
                AND table_name = 'documents' 
                AND column_name = 'source_type'
            )
        """)
        
        if column_exists:
            logger.info("✅ source_type column already exists")
        else:
            # Add the column
            await conn.execute("""
                ALTER TABLE document_hub.documents 
                ADD COLUMN source_type VARCHAR(20) DEFAULT 'upload'
            """)
            
            # Add index for better query performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_source_type 
                ON document_hub.documents(source_type)
            """)
            
            logger.info("✅ Added source_type column and index to documents table")
        
        # Check if watch_directories table needs to be created
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'watch_directories'
            )
        """)
        
        if not table_exists:
            logger.info("🔧 Creating watch_directories table...")
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS watch_directories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    path TEXT NOT NULL,
                    path_type VARCHAR(50) NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    recursive BOOLEAN DEFAULT TRUE,
                    file_patterns TEXT[],
                    processed_files JSONB DEFAULT '[]'::jsonb,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    last_scan_at TIMESTAMP WITH TIME ZONE,
                    last_error TEXT
                )
            """)
            
            logger.info("✅ Created watch_directories table")
            
            # Create processed_watch_files table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_watch_files (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    watch_directory_id UUID NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash VARCHAR(64) NOT NULL,
                    document_id UUID,
                    processing_status VARCHAR(50) NOT NULL,
                    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT,
                    metadata JSONB,
                    UNIQUE(watch_directory_id, file_path)
                )
            """)
            
            logger.info("✅ Created processed_watch_files table")
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_watch_directories_enabled 
                ON watch_directories(enabled)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_watch_files_watch_directory_id 
                ON processed_watch_files(watch_directory_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_watch_files_document_id 
                ON processed_watch_files(document_id)
            """)
            
            logger.info("✅ Created indexes for watch directories tables")
        
        # Check if library_files table needs to be created
        library_table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = 'library_files'
            )
        """)
        
        if not library_table_exists:
            logger.info("🔧 Creating library_files table...")
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS library_files (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    watch_directory_id UUID,
                    file_path TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_size BIGINT,
                    file_type VARCHAR(50),
                    mime_type VARCHAR(100),
                    file_hash VARCHAR(64),
                    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    indexed_status VARCHAR(50) DEFAULT 'indexed',
                    analyzed BOOLEAN DEFAULT FALSE,
                    document_id UUID REFERENCES document_hub.documents(id),
                    metadata JSONB,
                    UNIQUE(watch_directory_id, file_path)
                )
            """)
            
            logger.info("✅ Created library_files table")
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_library_files_watch_directory_id 
                ON library_files(watch_directory_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_library_files_document_id 
                ON library_files(document_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_library_files_analyzed 
                ON library_files(analyzed)
            """)
            
            logger.info("✅ Created indexes for library_files table")
        
        logger.info("🎉 Migration completed successfully!")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate_add_source_type())

