"""
Quick Redis Cleanup and Fresh Start
Simple script to clear Redis and start with clean PostgreSQL implementation
"""

import asyncio
import redis
from redis_cleanup_and_fresh_start import RedisCleanup, FreshPostgreSQLImplementation


async def quick_cleanup_and_start():
    """Quick cleanup and fresh start"""
    
    print("🧹 Quick Redis Cleanup and Fresh Start")
    print("=" * 50)
    
    # Step 1: Clear Redis
    print("\n1. Clearing Redis data...")
    redis_cleanup = RedisCleanup()
    
    try:
        # Discover what's in Redis
        discovery = await redis_cleanup.discover_redis_data()
        
        if discovery["total_keys"] == 0:
            print("✅ Redis is already empty")
        else:
            print(f"📊 Found {discovery['total_keys']} keys in Redis")
            
            # Clear Redis
            cleanup_result = await redis_cleanup.clear_redis_data(confirm=True)
            
            if "error" not in cleanup_result:
                print(f"✅ Redis cleared: {cleanup_result['keys_deleted']} keys deleted")
            else:
                print(f"❌ Redis cleanup failed: {cleanup_result['error']}")
                return
        
        # Verify Redis is empty
        is_empty = await redis_cleanup.verify_redis_empty()
        if not is_empty:
            print("❌ Redis is not empty - cleanup failed")
            return
            
    except Exception as e:
        print(f"❌ Error during Redis cleanup: {e}")
        return
    
    # Step 2: Test PostgreSQL
    print("\n2. Testing PostgreSQL connection...")
    fresh_impl = FreshPostgreSQLImplementation()
    
    try:
        await fresh_impl.initialize()
        
        # Test connection
        connection_ok = await fresh_impl.test_postgresql_connection()
        
        if not connection_ok:
            print("❌ PostgreSQL connection failed")
            return
        
        # Create sample data
        print("\n3. Creating sample data...")
        sample_result = await fresh_impl.create_sample_data()
        
        if "error" in sample_result:
            print(f"❌ Sample data creation failed: {sample_result['error']}")
            return
        
        # Verify sample data
        print("\n4. Verifying sample data...")
        verification = await fresh_impl.verify_sample_data()
        
        if verification.get("verification_passed", False):
            print("\n🎉 Fresh PostgreSQL implementation successful!")
            print("✅ Redis is clean and ready for caching")
            print("✅ PostgreSQL is ready for persistent storage")
            print("✅ Sample data created and verified")
            print("\n🚀 Ready to use Contract Reviewer v2 with PostgreSQL!")
        else:
            print("❌ Sample data verification failed")
        
    except Exception as e:
        print(f"❌ Error during PostgreSQL setup: {e}")
    
    finally:
        try:
            await fresh_impl.close()
        except:
            pass


def main():
    """Main function"""
    asyncio.run(quick_cleanup_and_start())


if __name__ == "__main__":
    main()
