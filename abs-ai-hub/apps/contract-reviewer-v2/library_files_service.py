"""
Library Files Service
Manages indexed files in the Document Library
"""

import asyncio
import hashlib
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import asyncpg

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = ['.pdf', '.doc', '.docx']


class LibraryFilesService:
    """Service for managing library files and their indexes"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def initialize(self):
        """Initialize the library files service"""
        try:
            logger.info("✅ Library files service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize library files service: {e}")
            raise
    
    async def index_files_in_directory(
        self,
        watch_directory_id: str,
        directory_path: str,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Index all supported files in a directory
        
        Args:
            watch_directory_id: ID of the watch directory
            directory_path: Path to the directory to index
            recursive: Whether to search recursively
            
        Returns:
            Dictionary with indexing results
        """
        try:
            if not os.path.exists(directory_path):
                raise ValueError(f"Directory does not exist: {directory_path}")
            
            files_indexed = []
            files_found = []
            
            # Walk through directory
            for root, dirs, files in os.walk(directory_path) if recursive else [(directory_path, [], os.listdir(directory_path))]:
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS:
                        files_found.append(file_path)
                        
                        # Index the file
                        indexed_file = await self._index_file(
                            watch_directory_id=watch_directory_id,
                            file_path=file_path
                        )
                        
                        if indexed_file:
                            files_indexed.append(indexed_file)
            
            return {
                "watch_directory_id": watch_directory_id,
                "files_found": len(files_found),
                "files_indexed": len(files_indexed),
                "index_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error indexing files in directory: {e}")
            raise
    
    async def _index_file(
        self,
        watch_directory_id: str,
        file_path: str
    ) -> Optional[Dict[str, Any]]:
        """Index a single file"""
        try:
            file_path_obj = Path(file_path)
            
            # Calculate file hash
            file_hash = await self._calculate_file_hash(file_path)
            
            # Get file metadata
            file_stat = file_path_obj.stat()
            
            # Get mime type
            import mimetypes
            mime_type = mimetypes.guess_type(str(file_path_obj))[0]
            
            # Check if already indexed
            async with self.db_pool.acquire() as conn:
                existing = await conn.fetchrow(
                    """
                    SELECT id FROM library_files
                    WHERE watch_directory_id = $1 AND file_path = $2
                    """,
                    watch_directory_id, file_path
                )
                
                if existing:
                    # Update existing record
                    await conn.execute(
                        """
                        UPDATE library_files
                        SET file_size = $1, file_hash = $2, 
                            indexed_at = CURRENT_TIMESTAMP,
                            indexed_status = 'indexed'
                        WHERE id = $3
                        """,
                        file_stat.st_size, file_hash, existing['id']
                    )
                    return {"id": existing['id'], "file_path": file_path, "status": "updated"}
                else:
                    # Insert new record
                    library_file_id = await conn.fetchval(
                        """
                        INSERT INTO library_files
                        (watch_directory_id, file_path, filename, file_size, 
                         file_type, mime_type, file_hash, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        RETURNING id
                        """,
                        watch_directory_id, file_path, file_path_obj.name,
                        file_stat.st_size, file_path_obj.suffix, mime_type, file_hash,
                        json.dumps({
                            "indexed_at": datetime.now().isoformat(),
                            "file_modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                        })
                    )
                    
                    return {"id": library_file_id, "file_path": file_path, "status": "created"}
                    
        except Exception as e:
            logger.error(f"❌ Error indexing file {file_path}: {e}")
            return None
    
    async def get_library_files(
        self,
        watch_directory_id: Optional[str] = None,
        analyzed: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get library files
        
        Args:
            watch_directory_id: Optional filter by watch directory
            analyzed: Optional filter by analyzed status
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of library files
        """
        try:
            async with self.db_pool.acquire() as conn:
                query = """
                    SELECT id, watch_directory_id, file_path, filename, file_size,
                           file_type, mime_type, file_hash, indexed_at, indexed_status,
                           analyzed, document_id, metadata
                    FROM library_files
                    WHERE 1=1
                """
                params = []
                param_count = 0
                
                if watch_directory_id:
                    param_count += 1
                    query += f" AND watch_directory_id = ${param_count}"
                    params.append(watch_directory_id)
                
                if analyzed is not None:
                    param_count += 1
                    query += f" AND analyzed = ${param_count}"
                    params.append(analyzed)
                
                query += " ORDER BY indexed_at DESC"
                query += f" LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
                params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ Error getting library files: {e}")
            raise
    
    async def link_library_file_to_document(
        self,
        library_file_id: str,
        document_id: str
    ) -> bool:
        """
        Link a library file to a document (after analysis)
        
        Args:
            library_file_id: ID of the library file
            document_id: ID of the document
            
        Returns:
            True if successful
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE library_files
                    SET document_id = $1, analyzed = TRUE
                    WHERE id = $2
                    """,
                    document_id, library_file_id
                )
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error linking library file to document: {e}")
            raise
    
    async def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics"""
        try:
            async with self.db_pool.acquire() as conn:
                # Total library files
                total_files = await conn.fetchval("SELECT COUNT(*) FROM library_files")
                
                # Analyzed files
                analyzed_files = await conn.fetchval(
                    "SELECT COUNT(*) FROM library_files WHERE analyzed = TRUE"
                )
                
                # Files by watch directory
                files_by_directory = await conn.fetch(
                    """
                    SELECT watch_directory_id, COUNT(*) as count
                    FROM library_files
                    GROUP BY watch_directory_id
                    """
                )
                
                return {
                    "total_files": total_files or 0,
                    "analyzed_files": analyzed_files or 0,
                    "pending_files": (total_files or 0) - (analyzed_files or 0),
                    "files_by_directory": [
                        {"watch_directory_id": str(row['watch_directory_id']), "count": row['count']}
                        for row in files_by_directory
                    ]
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting library stats: {e}")
            raise
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()


if __name__ == "__main__":
    print("Library Files Service - Run from main application")


