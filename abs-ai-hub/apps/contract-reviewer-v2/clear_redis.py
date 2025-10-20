"""
Simple Redis Cleanup Script
Quick script to clear all Redis data and start fresh
"""

import redis
import asyncio
from typing import Dict, Any


def clear_redis_data(redis_url: str = "redis://localhost:6379", confirm: bool = False) -> Dict[str, Any]:
    """Clear all data from Redis"""
    
    if not confirm:
        print("⚠️ This will delete ALL data in Redis!")
        print("To confirm, run: clear_redis_data(confirm=True)")
        return {"error": "Confirmation required"}
    
    try:
        # Connect to Redis
        redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        redis_client.ping()
        print("✅ Connected to Redis")
        
        # Get all keys
        all_keys = redis_client.keys("*")
        
        if not all_keys:
            print("✅ Redis is already empty")
            return {"keys_deleted": 0, "status": "already_empty"}
        
        print(f"📊 Found {len(all_keys)} keys in Redis")
        
        # Show key types
        document_keys = [k for k in all_keys if k.startswith("document:")]
        analysis_keys = [k for k in all_keys if k.startswith("analysis:")]
        session_keys = [k for k in all_keys if k.startswith("session:")]
        other_keys = [k for k in all_keys if not any(k.startswith(prefix) for prefix in ["document:", "analysis:", "session:"])]
        
        print(f"   Document keys: {len(document_keys)}")
        print(f"   Analysis keys: {len(analysis_keys)}")
        print(f"   Session keys: {len(session_keys)}")
        print(f"   Other keys: {len(other_keys)}")
        
        # Delete all keys
        deleted_count = redis_client.delete(*all_keys)
        
        print(f"✅ Deleted {deleted_count} keys from Redis")
        print("✅ Redis is now clean and ready for fresh implementation")
        
        return {
            "keys_deleted": deleted_count,
            "status": "success",
            "key_types": {
                "documents": len(document_keys),
                "analyses": len(analysis_keys),
                "sessions": len(session_keys),
                "other": len(other_keys)
            }
        }
        
    except Exception as e:
        print(f"❌ Error clearing Redis: {e}")
        return {"error": str(e)}


def verify_redis_empty(redis_url: str = "redis://localhost:6379") -> bool:
    """Verify that Redis is empty"""
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        keys = redis_client.keys("*")
        
        is_empty = len(keys) == 0
        
        if is_empty:
            print("✅ Redis is confirmed empty")
        else:
            print(f"⚠️ Redis still contains {len(keys)} keys")
        
        return is_empty
        
    except Exception as e:
        print(f"❌ Error verifying Redis: {e}")
        return False


def main():
    """Main function"""
    print("🧹 Redis Cleanup Script")
    print("=" * 30)
    
    # Clear Redis data
    result = clear_redis_data(confirm=True)
    
    if "error" not in result:
        print(f"\n📊 Cleanup Results:")
        print(f"   Keys deleted: {result['keys_deleted']}")
        print(f"   Status: {result['status']}")
        
        # Verify Redis is empty
        print(f"\n🔍 Verifying Redis is empty...")
        is_empty = verify_redis_empty()
        
        if is_empty:
            print("\n🎉 Redis cleanup successful!")
            print("✅ Redis is clean and ready for fresh PostgreSQL implementation")
        else:
            print("\n❌ Redis cleanup verification failed")
    else:
        print(f"\n❌ Redis cleanup failed: {result['error']}")


if __name__ == "__main__":
    main()
