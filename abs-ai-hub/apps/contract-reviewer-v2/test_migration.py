"""
Migration Test Script
Tests the migration process with sample data
"""

import asyncio
import json
import tempfile
import redis
from pathlib import Path
from datetime import datetime
import uuid

from migrate_redis_to_postgres import DocumentCacheMigration
from simple_migration import SimpleMigration


class MigrationTester:
    """Test the migration process with sample data"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.test_data = {}
        self.temp_files = []
    
    async def setup_test_data(self):
        """Set up test data in Redis"""
        print("🔧 Setting up test data...")
        
        # Create temporary files
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_file.write(f"Test contract content {i}".encode())
            temp_file.close()
            self.temp_files.append(temp_file.name)
        
        # Create test documents in Redis
        for i, file_path in enumerate(self.temp_files):
            doc_id = str(uuid.uuid4())
            doc_data = {
                "filename": f"test_contract_{i}.pdf",
                "file_path": file_path,
                "file_size": len(f"Test contract content {i}"),
                "upload_timestamp": datetime.now().isoformat(),
                "metadata": {
                    "client": f"Test Client {i}",
                    "contract_type": "NDA",
                    "test_data": True
                }
            }
            
            self.redis_client.set(f"document:{doc_id}", json.dumps(doc_data))
            self.test_data[f"document:{doc_id}"] = doc_data
            
            # Create test analysis
            analysis_id = str(uuid.uuid4())
            analysis_data = {
                "document_id": doc_id,
                "analysis": {
                    "summary": f"Test analysis for contract {i}",
                    "risks": [
                        {"level": "low", "description": f"Test risk {i}"}
                    ],
                    "recommendations": [
                        f"Test recommendation {i}"
                    ],
                    "key_points": [
                        f"Test key point {i}"
                    ]
                },
                "model_used": "llama3.2:3b",
                "processing_time_ms": 1000 + i * 100
            }
            
            self.redis_client.set(f"analysis:{analysis_id}", json.dumps(analysis_data))
            self.test_data[f"analysis:{analysis_id}"] = analysis_data
        
        print(f"✅ Created {len(self.temp_files)} test documents and analyses")
    
    async def test_discovery(self):
        """Test data discovery"""
        print("🔍 Testing data discovery...")
        
        migration = DocumentCacheMigration()
        await migration.initialize()
        
        try:
            discovery = await migration.discover_redis_data()
            
            print(f"Discovery results:")
            print(f"  Total keys: {discovery['total_keys']}")
            print(f"  Document keys: {discovery['document_keys']}")
            print(f"  Analysis keys: {discovery['analysis_keys']}")
            
            # Validate discovery
            assert discovery['document_keys'] >= 3, "Should find at least 3 document keys"
            assert discovery['analysis_keys'] >= 3, "Should find at least 3 analysis keys"
            
            print("✅ Discovery test passed")
            return discovery
            
        finally:
            await migration.close()
    
    async def test_document_migration(self):
        """Test document migration"""
        print("📄 Testing document migration...")
        
        migration = DocumentCacheMigration()
        await migration.initialize()
        
        try:
            # Get document keys
            doc_keys = [key for key in self.test_data.keys() if key.startswith("document:")]
            
            # Run migration
            results = await migration.migrate_documents(doc_keys)
            
            print(f"Document migration results:")
            print(f"  Successful: {len(results['successful'])}")
            print(f"  Failed: {len(results['failed'])}")
            print(f"  Skipped: {len(results['skipped'])}")
            
            # Validate results
            assert len(results['successful']) >= 3, "Should migrate at least 3 documents"
            assert len(results['failed']) == 0, "Should not have any failures"
            
            print("✅ Document migration test passed")
            return results
            
        finally:
            await migration.close()
    
    async def test_analysis_migration(self):
        """Test analysis migration"""
        print("🔍 Testing analysis migration...")
        
        migration = DocumentCacheMigration()
        await migration.initialize()
        
        try:
            # Get analysis keys
            analysis_keys = [key for key in self.test_data.keys() if key.startswith("analysis:")]
            
            # Run migration
            results = await migration.migrate_analyses(analysis_keys)
            
            print(f"Analysis migration results:")
            print(f"  Successful: {len(results['successful'])}")
            print(f"  Failed: {len(results['failed'])}")
            print(f"  Skipped: {len(results['skipped'])}")
            
            # Validate results
            assert len(results['successful']) >= 3, "Should migrate at least 3 analyses"
            assert len(results['failed']) == 0, "Should not have any failures"
            
            print("✅ Analysis migration test passed")
            return results
            
        finally:
            await migration.close()
    
    async def test_complete_migration(self):
        """Test complete migration process"""
        print("🚀 Testing complete migration...")
        
        migration = SimpleMigration()
        
        try:
            # Run migration
            results = await migration.run_migration(
                migrate_files=False,  # Skip file migration for test
                dry_run=False
            )
            
            print(f"Complete migration results:")
            print(f"  Documents migrated: {results.get('stats', {}).get('documents_migrated', 0)}")
            print(f"  Analyses migrated: {results.get('stats', {}).get('analyses_migrated', 0)}")
            print(f"  Errors: {results.get('stats', {}).get('errors', 0)}")
            
            # Validate results
            assert results.get('stats', {}).get('documents_migrated', 0) >= 3, "Should migrate at least 3 documents"
            assert results.get('stats', {}).get('analyses_migrated', 0) >= 3, "Should migrate at least 3 analyses"
            assert results.get('stats', {}).get('errors', 0) == 0, "Should not have any errors"
            
            print("✅ Complete migration test passed")
            return results
            
        except Exception as e:
            print(f"❌ Complete migration test failed: {e}")
            raise
    
    async def test_validation(self):
        """Test migration validation"""
        print("🔍 Testing migration validation...")
        
        migration = SimpleMigration()
        
        try:
            validation_results = await migration.validate_migration()
            
            print(f"Validation results:")
            print(f"  Redis documents: {validation_results.get('redis_documents', 0)}")
            print(f"  PostgreSQL documents: {validation_results.get('postgres_documents', 0)}")
            print(f"  Redis analyses: {validation_results.get('redis_analyses', 0)}")
            print(f"  PostgreSQL analyses: {validation_results.get('postgres_analyses', 0)}")
            print(f"  Validation passed: {validation_results.get('validation_passed', False)}")
            
            # Validate results
            assert validation_results.get('validation_passed', False), "Validation should pass"
            assert validation_results.get('postgres_documents', 0) >= 3, "Should have at least 3 PostgreSQL documents"
            assert validation_results.get('postgres_analyses', 0) >= 3, "Should have at least 3 PostgreSQL analyses"
            
            print("✅ Validation test passed")
            return validation_results
            
        except Exception as e:
            print(f"❌ Validation test failed: {e}")
            raise
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        
        try:
            # Clean up Redis test data
            for key in self.test_data.keys():
                self.redis_client.delete(key)
            
            # Clean up temporary files
            for file_path in self.temp_files:
                try:
                    Path(file_path).unlink(missing_ok=True)
                except:
                    pass
            
            print("✅ Test data cleaned up")
            
        except Exception as e:
            print(f"⚠️ Error cleaning up test data: {e}")
    
    async def run_all_tests(self):
        """Run all migration tests"""
        print("🧪 Running migration tests...")
        print("=" * 50)
        
        try:
            # Setup
            await self.setup_test_data()
            
            # Run tests
            await self.test_discovery()
            await self.test_document_migration()
            await self.test_analysis_migration()
            await self.test_complete_migration()
            await self.test_validation()
            
            print("\n🎉 All migration tests passed!")
            
        except Exception as e:
            print(f"\n❌ Migration tests failed: {e}")
            raise
        
        finally:
            # Cleanup
            await self.cleanup_test_data()


# ==================== PERFORMANCE TESTS ====================

class MigrationPerformanceTester:
    """Test migration performance with large datasets"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.temp_files = []
    
    async def create_large_dataset(self, num_documents: int = 100):
        """Create a large dataset for performance testing"""
        print(f"🔧 Creating {num_documents} test documents...")
        
        for i in range(num_documents):
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_file.write(f"Test contract content {i}".encode())
            temp_file.close()
            self.temp_files.append(temp_file.name)
            
            # Create document in Redis
            doc_id = str(uuid.uuid4())
            doc_data = {
                "filename": f"perf_test_contract_{i}.pdf",
                "file_path": temp_file.name,
                "file_size": len(f"Test contract content {i}"),
                "upload_timestamp": datetime.now().isoformat(),
                "metadata": {
                    "client": f"Performance Test Client {i}",
                    "contract_type": "NDA",
                    "performance_test": True
                }
            }
            
            self.redis_client.set(f"document:{doc_id}", json.dumps(doc_data))
            
            # Create analysis
            analysis_id = str(uuid.uuid4())
            analysis_data = {
                "document_id": doc_id,
                "analysis": {
                    "summary": f"Performance test analysis for contract {i}",
                    "risks": [{"level": "low", "description": f"Test risk {i}"}],
                    "recommendations": [f"Test recommendation {i}"],
                    "key_points": [f"Test key point {i}"]
                },
                "model_used": "llama3.2:3b",
                "processing_time_ms": 1000 + i * 10
            }
            
            self.redis_client.set(f"analysis:{analysis_id}", json.dumps(analysis_data))
        
        print(f"✅ Created {num_documents} test documents and analyses")
    
    async def test_performance(self, num_documents: int = 100):
        """Test migration performance"""
        print(f"⚡ Testing migration performance with {num_documents} documents...")
        
        try:
            # Create large dataset
            await self.create_large_dataset(num_documents)
            
            # Run migration
            start_time = datetime.now()
            
            migration = SimpleMigration()
            results = await migration.run_migration(
                migrate_files=False,  # Skip file migration for performance test
                dry_run=False
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Calculate performance metrics
            documents_migrated = results.get('stats', {}).get('documents_migrated', 0)
            analyses_migrated = results.get('stats', {}).get('analyses_migrated', 0)
            
            print(f"Performance results:")
            print(f"  Duration: {duration:.2f} seconds")
            print(f"  Documents migrated: {documents_migrated}")
            print(f"  Analyses migrated: {analyses_migrated}")
            print(f"  Documents per second: {documents_migrated / duration:.2f}")
            print(f"  Analyses per second: {analyses_migrated / duration:.2f}")
            
            # Validate performance
            assert duration < 60, "Migration should complete within 60 seconds"
            assert documents_migrated >= num_documents, "Should migrate all documents"
            assert analyses_migrated >= num_documents, "Should migrate all analyses"
            
            print("✅ Performance test passed")
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            raise
        
        finally:
            # Cleanup
            await self.cleanup_performance_data()
    
    async def cleanup_performance_data(self):
        """Clean up performance test data"""
        print("🧹 Cleaning up performance test data...")
        
        try:
            # Clean up Redis data
            doc_keys = self.redis_client.keys("document:*")
            analysis_keys = self.redis_client.keys("analysis:*")
            
            for key in doc_keys + analysis_keys:
                self.redis_client.delete(key)
            
            # Clean up temporary files
            for file_path in self.temp_files:
                try:
                    Path(file_path).unlink(missing_ok=True)
                except:
                    pass
            
            print("✅ Performance test data cleaned up")
            
        except Exception as e:
            print(f"⚠️ Error cleaning up performance test data: {e}")


# ==================== MAIN TEST RUNNER ====================

async def main():
    """Run all migration tests"""
    print("🧪 Migration Test Suite")
    print("=" * 50)
    
    # Run basic tests
    print("\n1. Running basic migration tests...")
    basic_tester = MigrationTester()
    await basic_tester.run_all_tests()
    
    # Run performance tests
    print("\n2. Running performance tests...")
    perf_tester = MigrationPerformanceTester()
    await perf_tester.test_performance(50)  # Test with 50 documents
    
    print("\n🎉 All migration tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
