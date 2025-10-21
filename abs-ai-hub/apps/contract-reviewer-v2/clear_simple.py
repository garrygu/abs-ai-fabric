import asyncio
import asyncpg
import redis
import shutil
from pathlib import Path
from qdrant_client import QdrantClient

async def clear_all():
    print('🧹 Clearing all data...')
    
    # Clear PostgreSQL
    try:
        conn = await asyncpg.connect('postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub')
        tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'document_hub'")
        for table in tables:
            await conn.execute(f"TRUNCATE TABLE document_hub.{table['tablename']} RESTART IDENTITY CASCADE")
        await conn.close()
        print('✅ PostgreSQL cleared')
    except Exception as e:
        print(f'❌ PostgreSQL error: {e}')
    
    # Clear Redis
    try:
        r = redis.from_url('redis://abs-redis:6379/0')
        keys = r.keys('*')
        if keys:
            r.delete(*keys)
        print('✅ Redis cleared')
    except Exception as e:
        print(f'❌ Redis error: {e}')
    
    # Clear Qdrant
    try:
        client = QdrantClient(host='abs-qdrant', port=6333)
        collections = client.get_collections()
        for collection in collections.collections:
            client.delete_collection(collection.name)
        print('✅ Qdrant cleared')
    except Exception as e:
        print(f'❌ Qdrant error: {e}')
    
    # Clear file storage
    try:
        storage_path = Path('/data/file_storage')
        if storage_path.exists():
            for item in storage_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            subdirs = ['documents', 'analysis_results', 'reports', 'archives', 'templates', 'backups', 'temp', 'metadata']
            for subdir in subdirs:
                (storage_path / subdir).mkdir(parents=True, exist_ok=True)
        print('✅ File storage cleared')
    except Exception as e:
        print(f'❌ File storage error: {e}')
    
    print('🎉 All data cleared!')

if __name__ == "__main__":
    asyncio.run(clear_all())
