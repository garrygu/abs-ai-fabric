import asyncio
import asyncpg
import os

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://hub_user:secure_password@localhost:5432/document_hub")

async def comprehensive_patch():
    print(f"Connecting to database at {POSTGRES_URL}...")
    try:
        conn = await asyncpg.connect(POSTGRES_URL)
        print("Connected!")

        print("🔧 Patching analysis_results table... adding confidence_score")
        try:
            await conn.execute("""
                ALTER TABLE document_hub.analysis_results 
                ADD COLUMN confidence_score FLOAT DEFAULT 0.0
            """)
            print("✅ Added 'confidence_score' column")
        except asyncpg.exceptions.DuplicateColumnError:
            print("✅ 'confidence_score' column already exists")

        print("🔧 Patching users table... adding full_name")
        try:
            await conn.execute("""
                ALTER TABLE document_hub.users 
                ADD COLUMN full_name VARCHAR(255)
            """)
            print("✅ Added 'full_name' column")
        except asyncpg.exceptions.DuplicateColumnError:
            print("✅ 'full_name' column already exists")

        await conn.close()
        print("🎉 Successfully executed comprehensive patch.")
    except Exception as e:
        print(f"❌ Error during migration: {e}")

if __name__ == "__main__":
    asyncio.run(comprehensive_patch())
