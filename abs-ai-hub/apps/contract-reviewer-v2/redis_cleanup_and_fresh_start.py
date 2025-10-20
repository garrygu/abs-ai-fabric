"""
Redis Cleanup and Fresh PostgreSQL Implementation
Clear Redis data and implement clean PostgreSQL-first architecture
"""

import asyncio
import redis
import json
from typing import Dict, Any, Optional
from datetime import datetime

from document_service import DocumentService


class RedisCleanup:
    """Clean up Redis data and prepare for fresh PostgreSQL implementation"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.cleanup_stats = {
            "keys_deleted": 0,
            "keys_skipped": 0,
            "errors": 0
        }
    
    async def discover_redis_data(self) -> Dict[str, Any]:
        """Discover what data exists in Redis"""
        try:
            print("🔍 Discovering Redis data...")
            
            # Get all keys
            all_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, "*"
            )
            
            # Categorize keys
            document_keys = [k for k in all_keys if k.startswith("document:")]
            analysis_keys = [k for k in all_keys if k.startswith("analysis:")]
            session_keys = [k for k in all_keys if k.startswith("session:")]
            other_keys = [k for k in all_keys if not any(k.startswith(prefix) for prefix in ["document:", "analysis:", "session:"])]
            
            discovery_result = {
                "total_keys": len(all_keys),
                "document_keys": len(document_keys),
                "analysis_keys": len(analysis_keys),
                "session_keys": len(session_keys),
                "other_keys": len(other_keys),
                "keys_by_type": {
                    "documents": document_keys,
                    "analyses": analysis_keys,
                    "sessions": session_keys,
                    "other": other_keys
                }
            }
            
            print(f"📊 Redis Discovery Results:")
            print(f"   Total keys: {discovery_result['total_keys']}")
            print(f"   Document keys: {discovery_result['document_keys']}")
            print(f"   Analysis keys: {discovery_result['analysis_keys']}")
            print(f"   Session keys: {discovery_result['session_keys']}")
            print(f"   Other keys: {discovery_result['other_keys']}")
            
            return discovery_result
            
        except Exception as e:
            print(f"❌ Error discovering Redis data: {e}")
            raise
    
    async def clear_redis_data(self, confirm: bool = False) -> Dict[str, Any]:
        """Clear all Redis data"""
        if not confirm:
            print("⚠️ Redis cleanup requires explicit confirmation")
            return {"error": "Confirmation required"}
        
        print("🧹 Clearing Redis data...")
        
        try:
            # Get all keys
            all_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, "*"
            )
            
            if not all_keys:
                print("✅ Redis is already empty")
                return {"keys_deleted": 0, "keys_skipped": 0, "errors": 0}
            
            # Delete all keys
            deleted_count = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.delete, *all_keys
            )
            
            self.cleanup_stats["keys_deleted"] = deleted_count
            
            print(f"✅ Redis cleanup complete:")
            print(f"   Keys deleted: {deleted_count}")
            print(f"   Redis is now clean and ready for fresh implementation")
            
            return self.cleanup_stats
            
        except Exception as e:
            print(f"❌ Error clearing Redis: {e}")
            self.cleanup_stats["errors"] += 1
            return {"error": str(e)}
    
    async def verify_redis_empty(self) -> bool:
        """Verify that Redis is empty"""
        try:
            keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, "*"
            )
            
            is_empty = len(keys) == 0
            
            if is_empty:
                print("✅ Redis is confirmed empty")
            else:
                print(f"⚠️ Redis still contains {len(keys)} keys")
            
            return is_empty
            
        except Exception as e:
            print(f"❌ Error verifying Redis: {e}")
            return False


class FreshPostgreSQLImplementation:
    """Implement fresh PostgreSQL-first architecture"""
    
    def __init__(self, postgres_url: str = "postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub"):
        self.doc_service = DocumentService(postgres_url)
        self.redis_client = None  # Will be used only for caching
    
    async def initialize(self):
        """Initialize PostgreSQL service"""
        try:
            await self.doc_service.initialize()
            print("✅ PostgreSQL service initialized")
        except Exception as e:
            print(f"❌ Failed to initialize PostgreSQL: {e}")
            raise
    
    async def close(self):
        """Close PostgreSQL service"""
        try:
            await self.doc_service.close()
            print("✅ PostgreSQL service closed")
        except Exception as e:
            print(f"⚠️ Error closing PostgreSQL: {e}")
    
    async def test_postgresql_connection(self) -> bool:
        """Test PostgreSQL connection and basic operations"""
        try:
            print("🔍 Testing PostgreSQL connection...")
            
            # Test basic connection
            documents, total = await self.doc_service.get_documents(limit=1, offset=0)
            
            print(f"✅ PostgreSQL connection successful")
            print(f"   Current documents in database: {total}")
            
            return True
            
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    async def create_sample_data(self) -> Dict[str, Any]:
        """Create sample data to test the fresh implementation"""
        try:
            print("📝 Creating sample data...")
            
            # Create a sample document
            sample_document = await self.doc_service.create_document(
                file_path="/tmp/sample_contract.pdf",
                original_filename="sample_contract.pdf",
                metadata={
                    "client": "Sample Client",
                    "contract_type": "NDA",
                    "test_data": True,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            print(f"✅ Created sample document: {sample_document['id']}")
            
            # Create a sample analysis
            sample_analysis = await self.doc_service.create_analysis_result(
                document_id=sample_document["id"],
                analysis_type="contract_review",
                analysis_data={
                    "summary": "This is a sample contract analysis",
                    "risks": [
                        {"level": "low", "description": "Standard confidentiality clause"}
                    ],
                    "recommendations": [
                        "Review confidentiality period"
                    ],
                    "key_points": [
                        "Confidentiality period: 2 years",
                        "Governing law: California"
                    ]
                },
                model_used="llama3.2:3b",
                processing_time_ms=1500
            )
            
            print(f"✅ Created sample analysis: {sample_analysis['id']}")
            
            return {
                "document": sample_document,
                "analysis": sample_analysis,
                "status": "success"
            }
            
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            return {"error": str(e)}
    
    async def verify_sample_data(self) -> Dict[str, Any]:
        """Verify that sample data was created correctly"""
        try:
            print("🔍 Verifying sample data...")
            
            # Get all documents
            documents, total_docs = await self.doc_service.get_documents(limit=10, offset=0)
            
            # Get all analyses
            all_analyses = []
            for doc in documents:
                analyses = await self.doc_service.get_analysis_results_by_document(doc["id"])
                all_analyses.extend(analyses)
            
            verification_result = {
                "documents_count": total_docs,
                "analyses_count": len(all_analyses),
                "documents": documents,
                "analyses": all_analyses,
                "verification_passed": total_docs > 0 and len(all_analyses) > 0
            }
            
            print(f"📊 Verification Results:")
            print(f"   Documents: {verification_result['documents_count']}")
            print(f"   Analyses: {verification_result['analyses_count']}")
            print(f"   Verification passed: {verification_result['verification_passed']}")
            
            return verification_result
            
        except Exception as e:
            print(f"❌ Error verifying sample data: {e}")
            return {"error": str(e)}


async def main():
    """Main function to clean Redis and implement fresh PostgreSQL"""
    
    print("🚀 Redis Cleanup and Fresh PostgreSQL Implementation")
    print("=" * 60)
    
    # Step 1: Discover Redis data
    print("\n1. Discovering Redis data...")
    redis_cleanup = RedisCleanup()
    
    try:
        discovery = await redis_cleanup.discover_redis_data()
        
        if discovery["total_keys"] == 0:
            print("✅ Redis is already empty - no cleanup needed")
        else:
            print(f"\n📊 Found {discovery['total_keys']} keys in Redis:")
            print(f"   Documents: {discovery['document_keys']}")
            print(f"   Analyses: {discovery['analysis_keys']}")
            print(f"   Sessions: {discovery['session_keys']}")
            print(f"   Other: {discovery['other_keys']}")
            
            # Ask for confirmation
            confirm = input("\n⚠️  This will DELETE ALL Redis data. Continue? (yes/no): ").lower()
            
            if confirm == "yes":
                # Step 2: Clear Redis data
                print("\n2. Clearing Redis data...")
                cleanup_result = await redis_cleanup.clear_redis_data(confirm=True)
                
                if "error" not in cleanup_result:
                    print(f"✅ Redis cleanup successful: {cleanup_result['keys_deleted']} keys deleted")
                else:
                    print(f"❌ Redis cleanup failed: {cleanup_result['error']}")
                    return
            else:
                print("❌ Redis cleanup cancelled")
                return
        
        # Step 3: Verify Redis is empty
        print("\n3. Verifying Redis is empty...")
        is_empty = await redis_cleanup.verify_redis_empty()
        
        if not is_empty:
            print("❌ Redis is not empty - cleanup may have failed")
            return
        
    except Exception as e:
        print(f"❌ Error during Redis cleanup: {e}")
        return
    
    # Step 4: Initialize fresh PostgreSQL implementation
    print("\n4. Initializing fresh PostgreSQL implementation...")
    fresh_impl = FreshPostgreSQLImplementation()
    
    try:
        await fresh_impl.initialize()
        
        # Step 5: Test PostgreSQL connection
        print("\n5. Testing PostgreSQL connection...")
        connection_ok = await fresh_impl.test_postgresql_connection()
        
        if not connection_ok:
            print("❌ PostgreSQL connection failed")
            return
        
        # Step 6: Create sample data
        print("\n6. Creating sample data...")
        sample_result = await fresh_impl.create_sample_data()
        
        if "error" in sample_result:
            print(f"❌ Sample data creation failed: {sample_result['error']}")
            return
        
        # Step 7: Verify sample data
        print("\n7. Verifying sample data...")
        verification = await fresh_impl.verify_sample_data()
        
        if verification.get("verification_passed", False):
            print("\n🎉 Fresh PostgreSQL implementation successful!")
            print("✅ Redis is clean and ready for caching")
            print("✅ PostgreSQL is ready for persistent storage")
            print("✅ Sample data created and verified")
        else:
            print("❌ Sample data verification failed")
        
    except Exception as e:
        print(f"❌ Error during PostgreSQL implementation: {e}")
    
    finally:
        try:
            await fresh_impl.close()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
