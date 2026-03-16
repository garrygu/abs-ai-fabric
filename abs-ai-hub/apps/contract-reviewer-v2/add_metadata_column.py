import asyncio
import asyncpg
import os

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://hub_user:secure_password@localhost:5432/document_hub")

async def add_metadata_columns():
    print(f"Connecting to database at {POSTGRES_URL}...")
    try:
        conn = await asyncpg.connect(POSTGRES_URL)
        print("Connected!")

        tables = ['documents', 'analysis_results']
        for table in tables:
            column_exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_schema = 'document_hub'
                    AND table_name = '{table}' 
                    AND column_name = 'metadata'
                )
            """)
            
            if column_exists:
                print(f"✅ 'metadata' column already exists in {table} table")
            else:
                print(f"🔧 Adding 'metadata' column to {table} table...")
                await conn.execute(f"""
                    ALTER TABLE document_hub.{table} 
                    ADD COLUMN metadata JSONB
                """)
                print(f"✅ Added 'metadata' column to {table} table")

        # Also check library_files and watch_directories and processed_watch_files if needed, but error mainly about metadata which was added to documents.
        # Wait, the error could be in 'library_files'. Let's check public schema too.
        public_tables = ['library_files', 'watch_directories', 'processed_watch_files']
        for table in public_tables:
            table_exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name = '{table}'
                )
            """)
            if table_exists:
                column_exists = await conn.fetchval(f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public'
                        AND table_name = '{table}' 
                        AND column_name = 'metadata'
                    )
                """)
                if column_exists:
                    print(f"✅ 'metadata' column already exists in public.{table} table")
                else:
                    print(f"🔧 Adding 'metadata' column to public.{table} table...")
                    await conn.execute(f"""
                        ALTER TABLE public.{table} 
                        ADD COLUMN metadata JSONB
                    """)
                    print(f"✅ Added 'metadata' column to public.{table} table")

        await conn.close()
        print("🎉 Successfully executed migration.")
    except Exception as e:
        print(f"❌ Error during migration: {e}")

if __name__ == "__main__":
    asyncio.run(add_metadata_columns())
