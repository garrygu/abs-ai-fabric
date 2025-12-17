"""
Database Migration Handler
Integrates migrations into the application startup process
"""

import asyncio
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def run_migrations_on_startup():
    """
    Run database migrations on application startup.
    This is safe to run multiple times because migrations are idempotent.
    """
    try:
        logger.info("🔄 Running database migrations on startup...")
        
        # Run the migration script
        script_path = Path(__file__).parent / "migrate_add_source_type.py"
        
        if not script_path.exists():
            logger.warning("⚠️ Migration script not found, skipping...")
            return
        
        # Run migration in subprocess
        result = subprocess.run(
            ["python", str(script_path)],
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Database migrations completed successfully")
            if result.stdout:
                logger.debug(f"Migration output: {result.stdout}")
        else:
            logger.warning(f"⚠️ Migration returned non-zero exit code: {result.returncode}")
            if result.stderr:
                logger.warning(f"Migration stderr: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        logger.error("❌ Migration script timed out after 60 seconds")
    except Exception as e:
        logger.warning(f"⚠️ Could not run migrations: {e}")
        logger.warning("⚠️ Application will continue, but database may not be fully migrated")
        # Don't fail startup - migrations are idempotent


def should_run_migrations() -> bool:
    """
    Check if migrations should be run.
    Returns False if migrations have already been applied.
    """
    # Add logic here to check if migrations are needed
    # For now, always run (migrations are idempotent)
    return True


if __name__ == "__main__":
    asyncio.run(run_migrations_on_startup())




