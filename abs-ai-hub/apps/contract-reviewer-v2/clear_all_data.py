#!/usr/bin/env python3
"""
Clear All Data Script for Contract Reviewer v2
This script clears all data from PostgreSQL, Redis, Qdrant, and file storage
"""

import asyncio
import asyncpg
import redis
import json
import os
import shutil
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuration
POSTGRES_URL = "postgresql://hub_user:secure_password@localhost:5432/document_hub"
REDIS_URL = "redis://localhost:6379/0"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
FILE_STORAGE_PATH = "/data/file_storage"

async def clear_postgresql():
    """Clear all data from PostgreSQL"""
    print("🗑️  Clearing PostgreSQL data...")
    try:
        conn = await asyncpg.connect(POSTGRES_URL)
        
        # Get all table names
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'document_hub'
        """)
        
        # Clear all tables
        for table in tables:
            table_name = table['tablename']
            await conn.execute(f"TRUNCATE TABLE document_hub.{table_name} RESTART IDENTITY CASCADE")
            print(f"  ✓ Cleared table: {table_name}")
        
        await conn.close()
        print("✅ PostgreSQL data cleared successfully")
        
    except Exception as e:
        print(f"❌ Error clearing PostgreSQL: {e}")

def clear_redis():
    """Clear all data from Redis"""
    print("🗑️  Clearing Redis data...")
    try:
        r = redis.from_url(REDIS_URL)
        
        # Get all keys
        keys = r.keys("*")
        if keys:
            r.delete(*keys)
            print(f"  ✓ Deleted {len(keys)} keys from Redis")
        else:
            print("  ✓ No keys found in Redis")
        
        print("✅ Redis data cleared successfully")
        
    except Exception as e:
        print(f"❌ Error clearing Redis: {e}")

def clear_qdrant():
    """Clear all data from Qdrant"""
    print("🗑️  Clearing Qdrant data...")
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Get all collections
        collections = client.get_collections()
        
        for collection in collections.collections:
            collection_name = collection.name
            client.delete_collection(collection_name)
            print(f"  ✓ Deleted collection: {collection_name}")
        
        print("✅ Qdrant data cleared successfully")
        
    except Exception as e:
        print(f"❌ Error clearing Qdrant: {e}")

def clear_file_storage():
    """Clear all data from file storage"""
    print("🗑️  Clearing file storage...")
    try:
        storage_path = Path(FILE_STORAGE_PATH)
        
        if storage_path.exists():
            # Remove all files and directories except the structure
            for item in storage_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"  ✓ Removed directory: {item.name}")
                else:
                    item.unlink()
                    print(f"  ✓ Removed file: {item.name}")
            
            # Recreate the directory structure
            subdirs = [
                "documents", "analysis_results", "reports", 
                "archives", "templates", "backups", "temp", "metadata"
            ]
            
            for subdir in subdirs:
                (storage_path / subdir).mkdir(parents=True, exist_ok=True)
                print(f"  ✓ Created directory: {subdir}")
            
            print("✅ File storage cleared successfully")
        else:
            print("  ✓ File storage path doesn't exist")
            
    except Exception as e:
        print(f"❌ Error clearing file storage: {e}")

async def main():
    """Main function to clear all data"""
    print("🧹 Starting data cleanup...")
    print("=" * 50)
    
    # Clear all storage systems
    await clear_postgresql()
    print()
    
    clear_redis()
    print()
    
    clear_qdrant()
    print()
    
    clear_file_storage()
    print()
    
    print("=" * 50)
    print("🎉 All data cleared successfully!")
    print("You can now start fresh with the Contract Reviewer v2 application.")

if __name__ == "__main__":
    asyncio.run(main())
