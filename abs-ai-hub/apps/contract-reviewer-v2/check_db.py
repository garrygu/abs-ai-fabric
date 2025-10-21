#!/usr/bin/env python3
import asyncio
import asyncpg

async def check_database():
    conn = await asyncpg.connect('postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub')
    
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
    asyncio.run(check_database())
