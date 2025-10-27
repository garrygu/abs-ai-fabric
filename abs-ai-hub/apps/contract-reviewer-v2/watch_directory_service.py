"""
Watch Directory Service
Monitors configured directories for new documents and processes them automatically
"""

import asyncio
import os
import hashlib
import uuid
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import asyncpg
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.pdf', '.doc', '.docx']


class DocumentWatcher(FileSystemEventHandler):
    """File system watcher for detecting new documents"""
    
    def __init__(self, process_callback, supported_extensions: List[str] = None):
        self.process_callback = process_callback
        self.supported_extensions = supported_extensions or SUPPORTED_EXTENSIONS
        self.processed_files = set()
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.supported_extensions:
                logger.info(f"📄 New document detected: {file_path}")
                self.process_callback(str(file_path))
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.supported_extensions:
                # Only process if not already processed
                if str(file_path) not in self.processed_files:
                    logger.info(f"📝 Document modified: {file_path}")
                    self.process_callback(str(file_path))
                    self.processed_files.add(str(file_path))


class WatchDirectoryService:
    """Service for managing watch directories and automatic document processing"""
    
    def __init__(
        self,
        db_pool: asyncpg.Pool,
        processing_service,
        doc_service,
        storage_service
    ):
        self.db_pool = db_pool
        self.processing_service = processing_service
        self.doc_service = doc_service
        self.storage_service = storage_service
        self.observers: List[Observer] = []
        self.watchers: Dict[str, DocumentWatcher] = {}
        self._running = False
        self._processing_queue = None  # Will be created in async context
        self._processing_task = None
    
    async def initialize(self):
        """Initialize the watch directory service"""
        try:
            self._running = True
            
            # Create async queue
            self._processing_queue = asyncio.Queue()
            
            # Create watch directories table if not exists
            await self._create_watch_directories_table()
            
            # Start the processing task
            self._processing_task = asyncio.create_task(self._process_file_queue())
            
            # Note: We don't start watching directories automatically on startup
            # Users need to configure and enable watch directories via the API/UI
            
            logger.info("✅ Watch directory service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize watch directory service: {e}")
            raise
    
    async def _create_watch_directories_table(self):
        """Create the watch_directories table in the database"""
        async with self.db_pool.acquire() as conn:
            # Enable UUID extension if not already enabled
            await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS watch_directories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    path TEXT NOT NULL,
                    path_type VARCHAR(50) NOT NULL, -- 'local', 'network', 'cloud'
                    enabled BOOLEAN DEFAULT TRUE,
                    recursive BOOLEAN DEFAULT TRUE,
                    file_patterns TEXT[], -- e.g., ['*.pdf', '*.docx']
                    processed_files JSONB DEFAULT '[]'::jsonb,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    last_scan_at TIMESTAMP WITH TIME ZONE,
                    last_error TEXT
                )
            """)
            
            # Create processed documents tracking table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_watch_files (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    watch_directory_id UUID NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash VARCHAR(64) NOT NULL,
                    document_id UUID,
                    processing_status VARCHAR(50) NOT NULL,
                    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT,
                    metadata JSONB,
                    UNIQUE(watch_directory_id, file_path)
                )
            """)
    
    async def add_watch_directory(
        self,
        path: str,
        path_type: str = "local",
        enabled: bool = True,
        recursive: bool = True,
        file_patterns: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Add a new watch directory
        
        Args:
            path: Directory path to watch
            path_type: Type of path ('local', 'network', 'cloud')
            enabled: Whether monitoring is enabled
            recursive: Watch subdirectories
            file_patterns: File patterns to watch (default: PDF, DOC, DOCX)
            metadata: Additional metadata
            
        Returns:
            UUID of the watch directory
        """
        try:
            if not os.path.exists(path):
                raise ValueError(f"Path does not exist: {path}")
            
            file_patterns = file_patterns or ['*.pdf', '*.doc', '*.docx']
            
            async with self.db_pool.acquire() as conn:
                watch_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO watch_directories 
                    (id, path, path_type, enabled, recursive, file_patterns, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, watch_id, path, path_type, enabled, recursive, file_patterns, json.dumps(metadata or {}))
            
            logger.info(f"✅ Added watch directory: {path} ({watch_id})")
            
            # Start watching if enabled
            if enabled:
                await self._start_watch(watch_id, path, recursive)
            
            return watch_id
            
        except Exception as e:
            logger.error(f"❌ Error adding watch directory: {e}")
            raise
    
    async def remove_watch_directory(self, watch_id: str) -> bool:
        """Remove a watch directory"""
        try:
            # Stop watching
            await self._stop_watch(watch_id)
            
            # Delete from database
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM watch_directories WHERE id = $1",
                    watch_id
                )
            
            logger.info(f"✅ Removed watch directory: {watch_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error removing watch directory: {e}")
            raise
    
    async def get_watch_directories(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """Get all watch directories"""
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT id, path, path_type, enabled, recursive, file_patterns,
                           processed_files, metadata, created_at, updated_at, last_scan_at, last_error
                    FROM watch_directories
                """
                
                if enabled_only:
                    query += " WHERE enabled = TRUE"
                
                query += " ORDER BY created_at DESC"
                
                rows = await conn.fetch(query)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Error getting watch directories: {e}")
            raise
    
    async def toggle_watch_directory(self, watch_id: str, enabled: bool) -> bool:
        """Enable or disable a watch directory"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get current directory info
                row = await conn.fetchrow(
                    "SELECT path FROM watch_directories WHERE id = $1",
                    watch_id
                )
                
                if not row:
                    raise ValueError(f"Watch directory {watch_id} not found")
                
                # Update database
                await conn.execute(
                    "UPDATE watch_directories SET enabled = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2",
                    enabled, watch_id
                )
                
                # Start or stop watching
                if enabled:
                    await self._start_watch(watch_id, row['path'], recursive=True)
                else:
                    await self._stop_watch(watch_id)
                
                logger.info(f"✅ Toggled watch directory {watch_id} to {enabled}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error toggling watch directory: {e}")
            raise
    
    async def _start_all_watches(self):
        """Start watching all enabled directories"""
        watch_directories = await self.get_watch_directories(enabled_only=True)
        
        for watch_dir in watch_directories:
            try:
                await self._start_watch(
                    watch_dir['id'],
                    watch_dir['path'],
                    watch_dir['recursive']
                )
            except Exception as e:
                logger.error(f"❌ Failed to start watching {watch_dir['path']}: {e}")
    
    async def _start_watch(self, watch_id: str, path: str, recursive: bool):
        """Start watching a directory"""
        try:
            watcher = DocumentWatcher(
                process_callback=lambda file_path: self._add_to_queue(watch_id, file_path),
                supported_extensions=SUPPORTED_EXTENSIONS
            )
            
            observer = Observer()
            observer.schedule(watcher, path, recursive=recursive)
            observer.start()
            
            self.observers.append(observer)
            self.watchers[watch_id] = watcher
            
            logger.info(f"✅ Started watching: {path}")
            
            # Update last_scan_at
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE watch_directories SET last_scan_at = CURRENT_TIMESTAMP WHERE id = $1",
                    watch_id
                )
                
        except Exception as e:
            logger.error(f"❌ Error starting watch for {path}: {e}")
            raise
    
    def _add_to_queue(self, watch_id: str, file_path: str):
        """Add file to processing queue (thread-safe for watchdog thread)"""
        try:
            if self._processing_queue:
                # Schedule coroutine from watchdog thread
                asyncio.run_coroutine_threadsafe(
                    self._processing_queue.put((watch_id, file_path)),
                    asyncio.get_running_loop()
                )
        except Exception as e:
            logger.error(f"Error adding file to queue: {e}")
    
    async def _process_file_queue(self):
        """Process files from the queue"""
        while self._running:
            try:
                # Use asyncio.wait_for for timeout
                watch_id, file_path = await asyncio.wait_for(
                    self._processing_queue.get(),
                    timeout=1.0
                )
                await self._process_detected_file(watch_id, file_path)
            except asyncio.TimeoutError:
                # Timeout is normal, continue loop
                continue
            except Exception as e:
                logger.error(f"Error processing file from queue: {e}")
    
    async def _stop_watch(self, watch_id: str):
        """Stop watching a directory"""
        try:
            if watch_id in self.watchers:
                # Find and stop corresponding observer
                for i, observer in enumerate(self.observers):
                    observer.stop()
                    observer.join()
                self.observers = []
                del self.watchers[watch_id]
                
                logger.info(f"✅ Stopped watching directory: {watch_id}")
                
        except Exception as e:
            logger.error(f"❌ Error stopping watch: {e}")
    
    async def _process_detected_file(self, watch_id: str, file_path: str):
        """Process a file detected by the watcher"""
        file_hash = None
        try:
            # Calculate file hash
            file_hash = await self._calculate_file_hash(file_path)
            
            # Check if already processed
            async with self.db_pool.acquire() as conn:
                existing = await conn.fetchrow(
                    """
                    SELECT processing_status, document_id FROM processed_watch_files
                    WHERE watch_directory_id = $1 AND file_hash = $2
                    """,
                    watch_id, file_hash
                )
                
                if existing and existing['processing_status'] == 'completed':
                    logger.info(f"⏭️  File already processed: {file_path}")
                    return
            
            # Wait a bit to ensure file is fully written
            await asyncio.sleep(2)
            
            logger.info(f"🔄 Processing file from watch directory: {file_path}")
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Create document record
            document = await self.doc_service.create_document(
                file_path=file_path,
                original_filename=Path(file_path).name,
                metadata={
                    "upload_source": "watch_directory",
                    "watch_directory_id": watch_id,
                    "watch_path": file_path,
                    "detected_at": datetime.now().isoformat(),
                    "file_type": Path(file_path).suffix,
                    "upload_timestamp": datetime.now().isoformat()
                }
            )
            
            # Process document
            processing_result = await self.processing_service.process_document(
                document_id=document_id,
                file_path=file_path,
                metadata={
                    "from_watch_directory": watch_id,
                    "auto_processed": True
                }
            )
            
            # Record successful processing
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO processed_watch_files
                    (watch_directory_id, file_path, file_hash, document_id, processing_status, metadata)
                    VALUES ($1, $2, $3, $4, 'completed', $5)
                    ON CONFLICT (watch_directory_id, file_path) DO UPDATE
                    SET processing_status = 'completed', processed_at = CURRENT_TIMESTAMP
                """, watch_id, file_path, file_hash, document_id, json.dumps({
                    "upload_timestamp": datetime.now().isoformat(),
                    "chunks_created": processing_result.get('chunks_created', 0)
                }))
                
                # Update watch directory's processed_files
                await conn.execute("""
                    UPDATE watch_directories
                    SET last_scan_at = CURRENT_TIMESTAMP,
                        processed_files = processed_files || $1::jsonb
                    WHERE id = $2
                """, [{"file_path": file_path, "processed_at": datetime.now().isoformat()}], watch_id)
            
            logger.info(f"✅ Successfully processed file from watch directory: {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Error processing file from watch: {e}")
            
            # Record error
            try:
                # Calculate hash if not already calculated
                if file_hash is None:
                    file_hash = await self._calculate_file_hash(file_path)
                    
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO processed_watch_files
                        (watch_directory_id, file_path, file_hash, processing_status, error_message)
                        VALUES ($1, $2, $3, 'failed', $4)
                    """, watch_id, file_path, file_hash, str(e))
            except Exception as cleanup_error:
                logger.error(f"Failed to record error in database: {cleanup_error}")
                pass
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read file in chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    async def manual_scan(self, watch_id: str) -> Dict[str, Any]:
        """Manually scan a watch directory for new files"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT path, recursive FROM watch_directories WHERE id = $1",
                    watch_id
                )
                
                if not row:
                    raise ValueError(f"Watch directory {watch_id} not found")
                
                path = row['path']
                recursive = row['recursive']
                
                # Find all supported files
                files_found = []
                for root, dirs, files in os.walk(path) if recursive else [(path, [], os.listdir(path))]:
                    for file in files:
                        file_path = os.path.join(root, file)
                        if Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS:
                            files_found.append(file_path)
                
                logger.info(f"🔍 Found {len(files_found)} files in {path}")
                
                # Process each file
                processed_count = 0
                for file_path in files_found:
                    await self._process_detected_file(watch_id, file_path)
                    processed_count += 1
                
                # Update scan time
                await conn.execute(
                    "UPDATE watch_directories SET last_scan_at = CURRENT_TIMESTAMP WHERE id = $1",
                    watch_id
                )
                
                return {
                    "watch_id": watch_id,
                    "files_found": len(files_found),
                    "processed": processed_count,
                    "scan_time": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error in manual scan: {e}")
            raise
    
    async def close(self):
        """Stop all watchers and cleanup"""
        self._running = False
        
        # Cancel processing task
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        # Stop watchers
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        self.observers = []
        self.watchers = {}
        
        logger.info("✅ Watch directory service closed")


if __name__ == "__main__":
    # Example usage
    print("Watch Directory Service - Run from main application")

