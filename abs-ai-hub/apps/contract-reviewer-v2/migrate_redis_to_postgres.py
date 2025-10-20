"""
Migration Tool: Redis Document Cache to PostgreSQL
Migrates existing document cache data from Redis to PostgreSQL persistence
"""

import asyncio
import json
import redis
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
import os
import shutil

from document_service import DocumentService


class DocumentCacheMigration:
    """Migrates document cache from Redis to PostgreSQL"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        postgres_url: str = "postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub"
    ):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.doc_service = DocumentService(postgres_url)
        self.migration_log = []
        self.stats = {
            "documents_migrated": 0,
            "analyses_migrated": 0,
            "errors": 0,
            "skipped": 0,
            "files_copied": 0
        }
    
    async def initialize(self):
        """Initialize both Redis and PostgreSQL connections"""
        try:
            # Test Redis connection
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.ping
            )
            print("✅ Redis connection established")
            
            # Initialize PostgreSQL service
            await self.doc_service.initialize()
            print("✅ PostgreSQL connection established")
            
        except Exception as e:
            print(f"❌ Failed to initialize connections: {e}")
            raise
    
    async def close(self):
        """Close all connections"""
        try:
            self.redis_client.close()
            await self.doc_service.close()
            print("✅ Migration connections closed")
        except Exception as e:
            print(f"⚠️ Error closing connections: {e}")
    
    # ==================== REDIS DATA DISCOVERY ====================
    
    async def discover_redis_data(self) -> Dict[str, Any]:
        """Discover all document-related data in Redis"""
        try:
            print("🔍 Discovering Redis data...")
            
            # Get all keys
            all_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, "*"
            )
            
            # Categorize keys
            document_keys = []
            analysis_keys = []
            session_keys = []
            other_keys = []
            
            for key in all_keys:
                if key.startswith("document:"):
                    document_keys.append(key)
                elif key.startswith("analysis:"):
                    analysis_keys.append(key)
                elif key.startswith("session:"):
                    session_keys.append(key)
                else:
                    other_keys.append(key)
            
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
            
            print(f"📊 Discovery complete:")
            print(f"   Total keys: {discovery_result['total_keys']}")
            print(f"   Document keys: {discovery_result['document_keys']}")
            print(f"   Analysis keys: {discovery_result['analysis_keys']}")
            print(f"   Session keys: {discovery_result['session_keys']}")
            
            return discovery_result
            
        except Exception as e:
            print(f"❌ Error discovering Redis data: {e}")
            raise
    
    # ==================== DOCUMENT MIGRATION ====================
    
    async def migrate_documents(self, document_keys: List[str]) -> Dict[str, Any]:
        """Migrate document data from Redis to PostgreSQL"""
        print(f"📄 Migrating {len(document_keys)} documents...")
        
        migration_results = {
            "successful": [],
            "failed": [],
            "skipped": []
        }
        
        for key in document_keys:
            try:
                # Get document data from Redis
                doc_data = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.get, key
                )
                
                if not doc_data:
                    print(f"⚠️ No data found for key: {key}")
                    migration_results["skipped"].append(key)
                    continue
                
                # Parse document data
                try:
                    doc_json = json.loads(doc_data)
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON for key: {key}")
                    migration_results["skipped"].append(key)
                    continue
                
                # Extract document information
                document_id = key.replace("document:", "")
                filename = doc_json.get("filename", f"migrated_{document_id}.pdf")
                file_path = doc_json.get("file_path", f"/migrated/{filename}")
                
                # Check if file exists
                if not Path(file_path).exists():
                    print(f"⚠️ File not found: {file_path}")
                    migration_results["skipped"].append(key)
                    continue
                
                # Create document in PostgreSQL
                migrated_doc = await self.doc_service.create_document(
                    file_path=file_path,
                    original_filename=filename,
                    metadata={
                        "migrated_from_redis": True,
                        "redis_key": key,
                        "redis_document_id": document_id,
                        "migration_timestamp": datetime.now().isoformat(),
                        **doc_json.get("metadata", {})
                    }
                )
                
                migration_results["successful"].append({
                    "redis_key": key,
                    "postgres_id": migrated_doc["id"],
                    "filename": filename
                })
                
                self.stats["documents_migrated"] += 1
                print(f"✅ Migrated document: {filename} -> {migrated_doc['id']}")
                
            except Exception as e:
                print(f"❌ Error migrating document {key}: {e}")
                migration_results["failed"].append({
                    "key": key,
                    "error": str(e)
                })
                self.stats["errors"] += 1
        
        return migration_results
    
    # ==================== ANALYSIS MIGRATION ====================
    
    async def migrate_analyses(self, analysis_keys: List[str]) -> Dict[str, Any]:
        """Migrate analysis data from Redis to PostgreSQL"""
        print(f"🔍 Migrating {len(analysis_keys)} analyses...")
        
        migration_results = {
            "successful": [],
            "failed": [],
            "skipped": []
        }
        
        for key in analysis_keys:
            try:
                # Get analysis data from Redis
                analysis_data = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.get, key
                )
                
                if not analysis_data:
                    print(f"⚠️ No data found for key: {key}")
                    migration_results["skipped"].append(key)
                    continue
                
                # Parse analysis data
                try:
                    analysis_json = json.loads(analysis_data)
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON for key: {key}")
                    migration_results["skipped"].append(key)
                    continue
                
                # Extract analysis information
                analysis_id = key.replace("analysis:", "")
                document_id = analysis_json.get("document_id")
                
                if not document_id:
                    print(f"⚠️ No document_id found for analysis: {key}")
                    migration_results["skipped"].append(key)
                    continue
                
                # Find corresponding document in PostgreSQL
                # First try to find by Redis document ID
                postgres_doc = await self._find_migrated_document(document_id)
                
                if not postgres_doc:
                    print(f"⚠️ Could not find migrated document for analysis: {key}")
                    migration_results["skipped"].append(key)
                    continue
                
                # Extract analysis data
                analysis_result_data = analysis_json.get("analysis", {})
                if not analysis_result_data:
                    analysis_result_data = {
                        "summary": analysis_json.get("summary", ""),
                        "risks": analysis_json.get("risks", []),
                        "recommendations": analysis_json.get("recommendations", []),
                        "key_points": analysis_json.get("key_points", []),
                        "citations": analysis_json.get("citations", [])
                    }
                
                # Create analysis result in PostgreSQL
                migrated_analysis = await self.doc_service.create_analysis_result(
                    document_id=postgres_doc["id"],
                    analysis_type="contract_review",
                    analysis_data=analysis_result_data,
                    model_used=analysis_json.get("model_used", "llama3.2:3b"),
                    processing_time_ms=analysis_json.get("processing_time_ms", 0)
                )
                
                migration_results["successful"].append({
                    "redis_key": key,
                    "postgres_id": migrated_analysis["id"],
                    "document_id": postgres_doc["id"]
                })
                
                self.stats["analyses_migrated"] += 1
                print(f"✅ Migrated analysis: {key} -> {migrated_analysis['id']}")
                
            except Exception as e:
                print(f"❌ Error migrating analysis {key}: {e}")
                migration_results["failed"].append({
                    "key": key,
                    "error": str(e)
                })
                self.stats["errors"] += 1
        
        return migration_results
    
    async def _find_migrated_document(self, redis_document_id: str) -> Optional[Dict[str, Any]]:
        """Find a migrated document by Redis document ID"""
        try:
            # Search for document with Redis document ID in metadata
            documents, _ = await self.doc_service.get_documents(limit=1000, offset=0)
            
            for doc in documents:
                metadata = doc.get("metadata", {})
                if metadata.get("redis_document_id") == redis_document_id:
                    return doc
            
            return None
            
        except Exception as e:
            print(f"❌ Error finding migrated document: {e}")
            return None
    
    # ==================== FILE MIGRATION ====================
    
    async def migrate_files(self, source_dir: str, target_dir: str) -> Dict[str, Any]:
        """Migrate files from source directory to target directory"""
        print(f"📁 Migrating files from {source_dir} to {target_dir}...")
        
        migration_results = {
            "copied": [],
            "failed": [],
            "skipped": []
        }
        
        try:
            source_path = Path(source_dir)
            target_path = Path(target_dir)
            
            if not source_path.exists():
                print(f"⚠️ Source directory does not exist: {source_dir}")
                return migration_results
            
            # Create target directory
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Find all files in source directory
            for file_path in source_path.rglob("*"):
                if file_path.is_file():
                    try:
                        # Calculate relative path
                        relative_path = file_path.relative_to(source_path)
                        target_file = target_path / relative_path
                        
                        # Create target directory if needed
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(file_path, target_file)
                        
                        migration_results["copied"].append({
                            "source": str(file_path),
                            "target": str(target_file)
                        })
                        
                        self.stats["files_copied"] += 1
                        print(f"✅ Copied file: {relative_path}")
                        
                    except Exception as e:
                        print(f"❌ Error copying file {file_path}: {e}")
                        migration_results["failed"].append({
                            "file": str(file_path),
                            "error": str(e)
                        })
                        self.stats["errors"] += 1
            
        except Exception as e:
            print(f"❌ Error migrating files: {e}")
            self.stats["errors"] += 1
        
        return migration_results
    
    # ==================== COMPLETE MIGRATION ====================
    
    async def run_complete_migration(
        self,
        migrate_files: bool = True,
        source_file_dir: Optional[str] = None,
        target_file_dir: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Run complete migration from Redis to PostgreSQL"""
        
        print("🚀 Starting complete migration from Redis to PostgreSQL...")
        print(f"   Dry run: {dry_run}")
        print(f"   Migrate files: {migrate_files}")
        
        migration_summary = {
            "start_time": datetime.now().isoformat(),
            "dry_run": dry_run,
            "discovery": None,
            "documents": None,
            "analyses": None,
            "files": None,
            "stats": self.stats.copy(),
            "end_time": None
        }
        
        try:
            # Initialize connections
            await self.initialize()
            
            # 1. Discover Redis data
            discovery = await self.discover_redis_data()
            migration_summary["discovery"] = discovery
            
            if dry_run:
                print("🔍 DRY RUN: Would migrate the following:")
                print(f"   Documents: {discovery['document_keys']}")
                print(f"   Analyses: {discovery['analysis_keys']}")
                return migration_summary
            
            # 2. Migrate documents
            if discovery["document_keys"]:
                doc_results = await self.migrate_documents(discovery["keys_by_type"]["documents"])
                migration_summary["documents"] = doc_results
            
            # 3. Migrate analyses
            if discovery["analysis_keys"]:
                analysis_results = await self.migrate_analyses(discovery["keys_by_type"]["analyses"])
                migration_summary["analyses"] = analysis_results
            
            # 4. Migrate files (if requested)
            if migrate_files and source_file_dir and target_file_dir:
                file_results = await self.migrate_files(source_file_dir, target_file_dir)
                migration_summary["files"] = file_results
            
            # 5. Generate migration report
            migration_summary["end_time"] = datetime.now().isoformat()
            migration_summary["stats"] = self.stats.copy()
            
            print("\n📊 Migration Summary:")
            print(f"   Documents migrated: {self.stats['documents_migrated']}")
            print(f"   Analyses migrated: {self.stats['analyses_migrated']}")
            print(f"   Files copied: {self.stats['files_copied']}")
            print(f"   Errors: {self.stats['errors']}")
            print(f"   Skipped: {self.stats['skipped']}")
            
            return migration_summary
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            migration_summary["error"] = str(e)
            migration_summary["end_time"] = datetime.now().isoformat()
            return migration_summary
        
        finally:
            await self.close()
    
    # ==================== VALIDATION ====================
    
    async def validate_migration(self) -> Dict[str, Any]:
        """Validate that migration was successful"""
        print("🔍 Validating migration...")
        
        validation_results = {
            "redis_documents": 0,
            "postgres_documents": 0,
            "redis_analyses": 0,
            "postgres_analyses": 0,
            "validation_passed": False
        }
        
        try:
            # Count Redis documents
            redis_doc_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, "document:*"
            )
            validation_results["redis_documents"] = len(redis_doc_keys)
            
            # Count Redis analyses
            redis_analysis_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, "analysis:*"
            )
            validation_results["redis_analyses"] = len(redis_analysis_keys)
            
            # Count PostgreSQL documents
            postgres_docs, _ = await self.doc_service.get_documents(limit=10000)
            validation_results["postgres_documents"] = len(postgres_docs)
            
            # Count PostgreSQL analyses
            postgres_analyses = []
            for doc in postgres_docs:
                analyses = await self.doc_service.get_analysis_results_by_document(doc["id"])
                postgres_analyses.extend(analyses)
            validation_results["postgres_analyses"] = len(postgres_analyses)
            
            # Validate migration
            validation_results["validation_passed"] = (
                validation_results["postgres_documents"] >= validation_results["redis_documents"] and
                validation_results["postgres_analyses"] >= validation_results["redis_analyses"]
            )
            
            print(f"📊 Validation Results:")
            print(f"   Redis documents: {validation_results['redis_documents']}")
            print(f"   PostgreSQL documents: {validation_results['postgres_documents']}")
            print(f"   Redis analyses: {validation_results['redis_analyses']}")
            print(f"   PostgreSQL analyses: {validation_results['postgres_analyses']}")
            print(f"   Validation passed: {validation_results['validation_passed']}")
            
            return validation_results
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            validation_results["error"] = str(e)
            return validation_results
    
    # ==================== CLEANUP ====================
    
    async def cleanup_redis_data(self, confirm: bool = False) -> Dict[str, Any]:
        """Clean up migrated data from Redis (use with caution!)"""
        if not confirm:
            print("⚠️ Cleanup requires explicit confirmation")
            return {"error": "Confirmation required"}
        
        print("🧹 Cleaning up Redis data...")
        
        cleanup_results = {
            "documents_deleted": 0,
            "analyses_deleted": 0,
            "errors": 0
        }
        
        try:
            # Delete document keys
            doc_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, "document:*"
            )
            
            for key in doc_keys:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.delete, key
                    )
                    cleanup_results["documents_deleted"] += 1
                    print(f"🗑️ Deleted Redis key: {key}")
                except Exception as e:
                    print(f"❌ Error deleting {key}: {e}")
                    cleanup_results["errors"] += 1
            
            # Delete analysis keys
            analysis_keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, "analysis:*"
            )
            
            for key in analysis_keys:
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.delete, key
                    )
                    cleanup_results["analyses_deleted"] += 1
                    print(f"🗑️ Deleted Redis key: {key}")
                except Exception as e:
                    print(f"❌ Error deleting {key}: {e}")
                    cleanup_results["errors"] += 1
            
            print(f"✅ Cleanup complete:")
            print(f"   Documents deleted: {cleanup_results['documents_deleted']}")
            print(f"   Analyses deleted: {cleanup_results['analyses_deleted']}")
            print(f"   Errors: {cleanup_results['errors']}")
            
            return cleanup_results
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            cleanup_results["error"] = str(e)
            return cleanup_results


# ==================== CLI INTERFACE ====================

async def main():
    """Command-line interface for migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate document cache from Redis to PostgreSQL")
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="Redis connection URL")
    parser.add_argument("--postgres-url", default="postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub", help="PostgreSQL connection URL")
    parser.add_argument("--migrate-files", action="store_true", help="Migrate files as well")
    parser.add_argument("--source-dir", help="Source directory for files")
    parser.add_argument("--target-dir", help="Target directory for files")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without actual migration")
    parser.add_argument("--validate", action="store_true", help="Validate migration results")
    parser.add_argument("--cleanup", action="store_true", help="Clean up Redis data after migration")
    
    args = parser.parse_args()
    
    # Create migration instance
    migration = DocumentCacheMigration(
        redis_url=args.redis_url,
        postgres_url=args.postgres_url
    )
    
    try:
        if args.validate:
            # Validate existing migration
            await migration.initialize()
            validation_results = await migration.validate_migration()
            print(f"Validation results: {validation_results}")
            
        elif args.cleanup:
            # Clean up Redis data
            await migration.initialize()
            cleanup_results = await migration.cleanup_redis_data(confirm=True)
            print(f"Cleanup results: {cleanup_results}")
            
        else:
            # Run migration
            migration_results = await migration.run_complete_migration(
                migrate_files=args.migrate_files,
                source_file_dir=args.source_dir,
                target_file_dir=args.target_dir,
                dry_run=args.dry_run
            )
            
            print(f"Migration results: {migration_results}")
            
            # Save migration report
            report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(migration_results, f, indent=2)
            print(f"📄 Migration report saved to: {report_file}")
    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
