"""
Simple Migration Script for Contract Reviewer v2
Easy-to-use migration script that can be run from the app
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from migrate_redis_to_postgres import DocumentCacheMigration


class SimpleMigration:
    """Simple migration interface for Contract Reviewer v2"""
    
    def __init__(self):
        self.migration = None
        self.results = None
    
    async def run_migration(
        self,
        redis_url: str = "redis://localhost:6379",
        postgres_url: str = "postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub",
        migrate_files: bool = True,
        source_dir: Optional[str] = None,
        target_dir: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Run migration with simple parameters
        
        Args:
            redis_url: Redis connection URL
            postgres_url: PostgreSQL connection URL
            migrate_files: Whether to migrate files
            source_dir: Source directory for files
            target_dir: Target directory for files
            dry_run: Whether to perform a dry run
            
        Returns:
            Migration results dictionary
        """
        
        print("🚀 Starting simple migration...")
        
        # Set default directories if not provided
        if migrate_files:
            if not source_dir:
                source_dir = "/tmp/contract-reviewer-v2/uploads"
            if not target_dir:
                target_dir = "/var/lib/postgresql/data/migrated_files"
        
        # Create migration instance
        self.migration = DocumentCacheMigration(
            redis_url=redis_url,
            postgres_url=postgres_url
        )
        
        try:
            # Run migration
            self.results = await self.migration.run_complete_migration(
                migrate_files=migrate_files,
                source_file_dir=source_dir,
                target_file_dir=target_dir,
                dry_run=dry_run
            )
            
            # Save results
            await self._save_results()
            
            return self.results
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return {"error": str(e), "success": False}
    
    async def validate_migration(self) -> Dict[str, Any]:
        """Validate the migration results"""
        if not self.migration:
            return {"error": "No migration instance available"}
        
        try:
            await self.migration.initialize()
            validation_results = await self.migration.validate_migration()
            return validation_results
        except Exception as e:
            return {"error": str(e)}
    
    async def cleanup_redis(self, confirm: bool = False) -> Dict[str, Any]:
        """Clean up Redis data after successful migration"""
        if not self.migration:
            return {"error": "No migration instance available"}
        
        if not confirm:
            return {"error": "Confirmation required"}
        
        try:
            await self.migration.initialize()
            cleanup_results = await self.migration.cleanup_redis_data(confirm=True)
            return cleanup_results
        except Exception as e:
            return {"error": str(e)}
    
    async def _save_results(self):
        """Save migration results to file"""
        if not self.results:
            return
        
        try:
            # Create results directory
            results_dir = Path("migration_results")
            results_dir.mkdir(exist_ok=True)
            
            # Save detailed results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = results_dir / f"migration_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(f"📄 Migration results saved to: {results_file}")
            
            # Save summary
            summary_file = results_dir / f"migration_summary_{timestamp}.txt"
            with open(summary_file, 'w') as f:
                f.write(self._generate_summary())
            
            print(f"📊 Migration summary saved to: {summary_file}")
            
        except Exception as e:
            print(f"⚠️ Error saving results: {e}")
    
    def _generate_summary(self) -> str:
        """Generate a human-readable summary of migration results"""
        if not self.results:
            return "No migration results available"
        
        summary = []
        summary.append("=" * 50)
        summary.append("MIGRATION SUMMARY")
        summary.append("=" * 50)
        summary.append(f"Start Time: {self.results.get('start_time', 'Unknown')}")
        summary.append(f"End Time: {self.results.get('end_time', 'Unknown')}")
        summary.append(f"Dry Run: {self.results.get('dry_run', False)}")
        summary.append("")
        
        # Discovery results
        discovery = self.results.get('discovery', {})
        if discovery:
            summary.append("DISCOVERY RESULTS:")
            summary.append(f"  Total Redis Keys: {discovery.get('total_keys', 0)}")
            summary.append(f"  Document Keys: {discovery.get('document_keys', 0)}")
            summary.append(f"  Analysis Keys: {discovery.get('analysis_keys', 0)}")
            summary.append(f"  Session Keys: {discovery.get('session_keys', 0)}")
            summary.append("")
        
        # Migration results
        stats = self.results.get('stats', {})
        summary.append("MIGRATION RESULTS:")
        summary.append(f"  Documents Migrated: {stats.get('documents_migrated', 0)}")
        summary.append(f"  Analyses Migrated: {stats.get('analyses_migrated', 0)}")
        summary.append(f"  Files Copied: {stats.get('files_copied', 0)}")
        summary.append(f"  Errors: {stats.get('errors', 0)}")
        summary.append(f"  Skipped: {stats.get('skipped', 0)}")
        summary.append("")
        
        # Document migration details
        doc_results = self.results.get('documents', {})
        if doc_results:
            summary.append("DOCUMENT MIGRATION:")
            summary.append(f"  Successful: {len(doc_results.get('successful', []))}")
            summary.append(f"  Failed: {len(doc_results.get('failed', []))}")
            summary.append(f"  Skipped: {len(doc_results.get('skipped', []))}")
            summary.append("")
        
        # Analysis migration details
        analysis_results = self.results.get('analyses', {})
        if analysis_results:
            summary.append("ANALYSIS MIGRATION:")
            summary.append(f"  Successful: {len(analysis_results.get('successful', []))}")
            summary.append(f"  Failed: {len(analysis_results.get('failed', []))}")
            summary.append(f"  Skipped: {len(analysis_results.get('skipped', []))}")
            summary.append("")
        
        # File migration details
        file_results = self.results.get('files', {})
        if file_results:
            summary.append("FILE MIGRATION:")
            summary.append(f"  Copied: {len(file_results.get('copied', []))}")
            summary.append(f"  Failed: {len(file_results.get('failed', []))}")
            summary.append(f"  Skipped: {len(file_results.get('skipped', []))}")
            summary.append("")
        
        # Error details
        if stats.get('errors', 0) > 0:
            summary.append("ERRORS:")
            if doc_results and doc_results.get('failed'):
                summary.append("  Document Errors:")
                for error in doc_results['failed'][:5]:  # Show first 5 errors
                    summary.append(f"    - {error.get('key', 'Unknown')}: {error.get('error', 'Unknown error')}")
            
            if analysis_results and analysis_results.get('failed'):
                summary.append("  Analysis Errors:")
                for error in analysis_results['failed'][:5]:  # Show first 5 errors
                    summary.append(f"    - {error.get('key', 'Unknown')}: {error.get('error', 'Unknown error')}")
            summary.append("")
        
        summary.append("=" * 50)
        summary.append("MIGRATION COMPLETE")
        summary.append("=" * 50)
        
        return "\n".join(summary)


# ==================== FASTAPI INTEGRATION ====================

def create_migration_endpoints(app):
    """Add migration endpoints to FastAPI app"""
    
    migration_instance = SimpleMigration()
    
    @app.post("/api/migration/run")
    async def run_migration(
        redis_url: str = "redis://localhost:6379",
        postgres_url: str = "postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub",
        migrate_files: bool = True,
        source_dir: str = "/tmp/contract-reviewer-v2/uploads",
        target_dir: str = "/var/lib/postgresql/data/migrated_files",
        dry_run: bool = False
    ):
        """Run migration from Redis to PostgreSQL"""
        try:
            results = await migration_instance.run_migration(
                redis_url=redis_url,
                postgres_url=postgres_url,
                migrate_files=migrate_files,
                source_dir=source_dir,
                target_dir=target_dir,
                dry_run=dry_run
            )
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @app.post("/api/migration/validate")
    async def validate_migration():
        """Validate migration results"""
        try:
            validation_results = await migration_instance.validate_migration()
            return {
                "success": True,
                "validation": validation_results
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @app.post("/api/migration/cleanup")
    async def cleanup_redis(confirm: bool = False):
        """Clean up Redis data after migration"""
        if not confirm:
            return {
                "success": False,
                "error": "Confirmation required"
            }
        
        try:
            cleanup_results = await migration_instance.cleanup_redis(confirm=True)
            return {
                "success": True,
                "cleanup": cleanup_results
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @app.get("/api/migration/status")
    async def get_migration_status():
        """Get migration status"""
        return {
            "migration_available": True,
            "last_migration": migration_instance.results.get('end_time') if migration_instance.results else None
        }


# ==================== COMMAND LINE INTERFACE ====================

async def cli_migration():
    """Simple command-line interface for migration"""
    
    print("🚀 Contract Reviewer v2 - Redis to PostgreSQL Migration")
    print("=" * 60)
    
    # Get user input
    print("\nMigration Settings:")
    migrate_files = input("Migrate files? (y/n): ").lower().startswith('y')
    
    source_dir = None
    target_dir = None
    if migrate_files:
        source_dir = input("Source directory (default: /tmp/contract-reviewer-v2/uploads): ").strip()
        if not source_dir:
            source_dir = "/tmp/contract-reviewer-v2/uploads"
        
        target_dir = input("Target directory (default: /var/lib/postgresql/data/migrated_files): ").strip()
        if not target_dir:
            target_dir = "/var/lib/postgresql/data/migrated_files"
    
    dry_run = input("Perform dry run first? (y/n): ").lower().startswith('y')
    
    # Run migration
    migration = SimpleMigration()
    
    try:
        if dry_run:
            print("\n🔍 Running dry run...")
            results = await migration.run_migration(
                migrate_files=migrate_files,
                source_dir=source_dir,
                target_dir=target_dir,
                dry_run=True
            )
            
            print(f"\nDry run results: {results}")
            
            proceed = input("\nProceed with actual migration? (y/n): ").lower().startswith('y')
            if not proceed:
                print("Migration cancelled.")
                return
        
        print("\n🚀 Running actual migration...")
        results = await migration.run_migration(
            migrate_files=migrate_files,
            source_dir=source_dir,
            target_dir=target_dir,
            dry_run=False
        )
        
        print(f"\nMigration completed!")
        print(f"Results: {results}")
        
        # Ask about cleanup
        cleanup = input("\nClean up Redis data? (y/n): ").lower().startswith('y')
        if cleanup:
            confirm = input("Are you sure? This will delete Redis data! (y/n): ").lower().startswith('y')
            if confirm:
                cleanup_results = await migration.cleanup_redis(confirm=True)
                print(f"Cleanup results: {cleanup_results}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")


if __name__ == "__main__":
    asyncio.run(cli_migration())
