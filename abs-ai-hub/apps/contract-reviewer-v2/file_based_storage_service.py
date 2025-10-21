"""
File-Based Storage Service
Comprehensive file organization system for analysis results, reports, and document archives
"""

import os
import json
import uuid
import shutil
import hashlib
import zipfile
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
import aiofiles
from dataclasses import dataclass, asdict
import mimetypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileType(Enum):
    """File type enumeration"""
    DOCUMENT = "document"
    ANALYSIS_RESULT = "analysis_result"
    REPORT_PDF = "report_pdf"
    REPORT_WORD = "report_word"
    REPORT_JSON = "report_json"
    ARCHIVE = "archive"
    TEMPLATE = "template"
    BACKUP = "backup"
    TEMP = "temp"


class StorageTier(Enum):
    """Storage tier enumeration"""
    HOT = "hot"        # Frequently accessed, fast storage
    WARM = "warm"      # Occasionally accessed, balanced storage
    COLD = "cold"      # Rarely accessed, cost-effective storage


@dataclass
class FileMetadata:
    """File metadata structure"""
    file_id: str
    original_filename: str
    file_type: FileType
    storage_tier: StorageTier
    file_path: str
    file_size: int
    mime_type: str
    checksum: str
    created_at: datetime
    modified_at: datetime
    accessed_at: datetime
    version: int
    parent_document_id: Optional[str] = None
    analysis_id: Optional[str] = None
    client_id: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StorageConfig:
    """Storage configuration"""
    base_path: str
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    max_files_per_directory: int = 10000
    enable_compression: bool = True
    enable_encryption: bool = False
    retention_days: int = 2555  # 7 years
    backup_enabled: bool = True
    backup_frequency_days: int = 30
    archive_enabled: bool = True
    archive_frequency_days: int = 90


class FileBasedStorageService:
    """Service for managing file-based storage with hierarchical organization"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.base_path = Path(config.base_path)
        self.file_registry: Dict[str, FileMetadata] = {}
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directory structure"""
        directories = [
            self.base_path,
            self.base_path / "documents",
            self.base_path / "analysis_results",
            self.base_path / "reports",
            self.base_path / "archives",
            self.base_path / "templates",
            self.base_path / "backups",
            self.base_path / "temp",
            self.base_path / "metadata"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Directory ensured: {directory}")
    
    # ==================== HIERARCHICAL FILE ORGANIZATION ====================
    
    def generate_file_path(
        self,
        file_type: FileType,
        client_id: Optional[str] = None,
        document_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        filename: Optional[str] = None,
        version: int = 1
    ) -> Path:
        """
        Generate hierarchical file path based on organization rules
        
        Args:
            file_type: Type of file
            client_id: Client identifier
            document_id: Document identifier
            analysis_id: Analysis identifier
            filename: Original filename
            version: File version
            
        Returns:
            Path object for the file
        """
        try:
            # Ensure file_type is an enum, not a string
            if isinstance(file_type, str):
                # Convert string to enum
                file_type = FileType(file_type)
            
            # Base directory based on file type
            base_dir = self.base_path / file_type.value
            
            # Generate path components
            path_components = []
            
            # Add date-based organization (YYYY/MM/DD)
            now = datetime.now()
            path_components.extend([
                str(now.year),
                f"{now.month:02d}",
                f"{now.day:02d}"
            ])
            
            # Add client-based organization if available
            if client_id:
                # Sanitize client ID for filesystem
                safe_client_id = self._sanitize_filename(client_id)
                path_components.append(f"client_{safe_client_id}")
            
            # Add document-based organization if available
            if document_id:
                # Use first 8 characters of document ID for readability
                doc_prefix = document_id[:8]
                path_components.append(f"doc_{doc_prefix}")
            
            # Add analysis-based organization if available
            if analysis_id:
                analysis_prefix = analysis_id[:8]
                path_components.append(f"analysis_{analysis_prefix}")
            
            # Create the directory path
            directory_path = base_dir
            for component in path_components:
                directory_path = directory_path / component
            
            # Ensure directory exists
            directory_path.mkdir(parents=True, exist_ok=True)
            
            # Generate filename if not provided
            if not filename:
                timestamp = now.strftime("%Y%m%d_%H%M%S")
                extension = self._get_default_extension(file_type)
                filename = f"{file_type.value}_{timestamp}_{uuid.uuid4().hex[:8]}{extension}"
            
            # Add version suffix if version > 1
            if version > 1:
                name_parts = filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    filename = f"{name_parts[0]}_v{version}.{name_parts[1]}"
                else:
                    filename = f"{filename}_v{version}"
            
            # Sanitize filename
            filename = self._sanitize_filename(filename)
            
            # Final file path
            file_path = directory_path / filename
            
            logger.info(f"Generated file path: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"❌ Error generating file path: {e}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def _get_default_extension(self, file_type: FileType) -> str:
        """Get default file extension for file type"""
        extensions = {
            FileType.DOCUMENT: ".pdf",
            FileType.ANALYSIS_RESULT: ".json",
            FileType.REPORT_PDF: ".pdf",
            FileType.REPORT_WORD: ".docx",
            FileType.REPORT_JSON: ".json",
            FileType.ARCHIVE: ".zip",
            FileType.TEMPLATE: ".json",
            FileType.BACKUP: ".zip",
            FileType.TEMP: ".tmp"
        }
        return extensions.get(file_type, ".bin")
    
    # ==================== FILE OPERATIONS ====================
    
    async def store_file(
        self,
        file_data: Union[bytes, str, Dict[str, Any]],
        file_type: FileType,
        original_filename: str,
        client_id: Optional[str] = None,
        document_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: int = 1
    ) -> FileMetadata:
        """
        Store file with metadata
        
        Args:
            file_data: File content (bytes, string, or dict for JSON)
            file_type: Type of file
            original_filename: Original filename
            client_id: Client identifier
            document_id: Document identifier
            analysis_id: Analysis identifier
            metadata: Additional metadata
            version: File version
            
        Returns:
            FileMetadata object
        """
        try:
            # Ensure file_type is an enum, not a string
            if isinstance(file_type, str):
                file_type = FileType(file_type)
            
            logger.info(f"Storing file: {original_filename} (type: {file_type.value})")
            
            # Generate file path
            file_path = self.generate_file_path(
                file_type=file_type,
                client_id=client_id,
                document_id=document_id,
                analysis_id=analysis_id,
                filename=original_filename,
                version=version
            )
            
            # Convert data to bytes
            if isinstance(file_data, dict):
                file_bytes = json.dumps(file_data, indent=2, default=str).encode('utf-8')
            elif isinstance(file_data, str):
                file_bytes = file_data.encode('utf-8')
            else:
                file_bytes = file_data
            
            # Check file size
            if len(file_bytes) > self.config.max_file_size:
                raise ValueError(f"File size {len(file_bytes)} exceeds maximum {self.config.max_file_size}")
            
            # Calculate checksum
            checksum = hashlib.sha256(file_bytes).hexdigest()
            
            # Write file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_bytes)
            
            # Get file info
            file_stat = file_path.stat()
            mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            
            # Create file metadata
            file_metadata = FileMetadata(
                file_id=str(uuid.uuid4()),
                original_filename=original_filename,
                file_type=file_type,
                storage_tier=StorageTier.HOT,
                file_path=str(file_path),
                file_size=file_stat.st_size,
                mime_type=mime_type,
                checksum=checksum,
                created_at=datetime.fromtimestamp(file_stat.st_ctime),
                modified_at=datetime.fromtimestamp(file_stat.st_mtime),
                accessed_at=datetime.fromtimestamp(file_stat.st_atime),
                version=version,
                parent_document_id=document_id,
                analysis_id=analysis_id,
                client_id=client_id,
                metadata=metadata or {}
            )
            
            # Store metadata
            await self._store_file_metadata(file_metadata)
            
            # Register file
            self.file_registry[file_metadata.file_id] = file_metadata
            
            logger.info(f"✅ File stored: {file_metadata.file_id} -> {file_path}")
            return file_metadata
            
        except Exception as e:
            logger.error(f"❌ Error storing file: {e}")
            raise
    
    async def retrieve_file(self, file_id: str) -> Tuple[bytes, FileMetadata]:
        """
        Retrieve file by ID
        
        Args:
            file_id: File identifier
            
        Returns:
            Tuple of (file_content, file_metadata)
        """
        try:
            logger.info(f"Retrieving file: {file_id}")
            
            # Get file metadata
            file_metadata = await self._get_file_metadata(file_id)
            if not file_metadata:
                raise FileNotFoundError(f"File not found: {file_id}")
            
            # Check if file exists
            file_path = Path(file_metadata.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File path not found: {file_path}")
            
            # Read file
            async with aiofiles.open(file_path, 'rb') as f:
                file_content = await f.read()
            
            # Verify checksum
            calculated_checksum = hashlib.sha256(file_content).hexdigest()
            if calculated_checksum != file_metadata.checksum:
                logger.warning(f"Checksum mismatch for file {file_id}")
            
            # Update access time
            file_metadata.accessed_at = datetime.now()
            await self._store_file_metadata(file_metadata)
            
            logger.info(f"✅ File retrieved: {file_id}")
            return file_content, file_metadata
            
        except Exception as e:
            logger.error(f"❌ Error retrieving file: {e}")
            raise
    
    async def delete_document_files(self, document_id: str) -> bool:
        """
        Delete all files associated with a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🗑️ Deleting all files for document: {document_id}")
            
            # Find all files for this document
            deleted_count = 0
            
            # Search through all file types
            for file_type in FileType:
                type_dir = self.base_path / file_type.value
                if not type_dir.exists():
                    continue
                
                # Search recursively for files with this document_id
                for file_path in type_dir.rglob("*"):
                    if file_path.is_file() and file_path.suffix == '.json':
                        # Check if this is a metadata file for our document
                        try:
                            async with aiofiles.open(file_path, 'r') as f:
                                metadata = json.loads(await f.read())
                                if metadata.get('document_id') == document_id:
                                    # Delete the metadata file and associated data file
                                    data_file_path = file_path.with_suffix('')
                                    if data_file_path.exists():
                                        data_file_path.unlink()
                                        logger.info(f"  - Deleted data file: {data_file_path}")
                                    
                                    file_path.unlink()
                                    logger.info(f"  - Deleted metadata file: {file_path}")
                                    deleted_count += 1
                        except Exception as e:
                            logger.warning(f"  - Error reading metadata file {file_path}: {e}")
                            continue
            
            logger.info(f"✅ Deleted {deleted_count} files for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting files for document {document_id}: {e}")
            return False

    async def delete_file(self, file_id: str, permanent: bool = False) -> bool:
        """
        Delete file
        
        Args:
            file_id: File identifier
            permanent: Whether to permanently delete (vs move to trash)
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting file: {file_id} (permanent: {permanent})")
            
            # Get file metadata
            file_metadata = await self._get_file_metadata(file_id)
            if not file_metadata:
                logger.warning(f"File metadata not found: {file_id}")
                return False
            
            file_path = Path(file_metadata.file_path)
            
            if permanent:
                # Permanently delete file
                if file_path.exists():
                    file_path.unlink()
                
                # Remove metadata
                await self._delete_file_metadata(file_id)
                
                # Remove from registry
                if file_id in self.file_registry:
                    del self.file_registry[file_id]
            else:
                # Move to trash/archive
                trash_dir = self.base_path / "trash" / datetime.now().strftime("%Y/%m/%d")
                trash_dir.mkdir(parents=True, exist_ok=True)
                
                trash_path = trash_dir / f"{file_id}_{file_path.name}"
                if file_path.exists():
                    shutil.move(str(file_path), str(trash_path))
                
                # Update metadata
                file_metadata.file_path = str(trash_path)
                file_metadata.metadata["deleted_at"] = datetime.now().isoformat()
                file_metadata.metadata["deleted"] = True
                await self._store_file_metadata(file_metadata)
            
            logger.info(f"✅ File deleted: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting file: {e}")
            raise
    
    # ==================== ANALYSIS RESULT SERIALIZATION ====================
    
    async def store_analysis_result(
        self,
        analysis_data: Dict[str, Any],
        document_id: str,
        analysis_id: str,
        client_id: Optional[str] = None,
        format: str = "json"
    ) -> FileMetadata:
        """
        Store analysis result with proper serialization
        
        Args:
            analysis_data: Analysis result data
            document_id: Document identifier
            analysis_id: Analysis identifier
            client_id: Client identifier
            format: Storage format (json, xml, yaml)
            
        Returns:
            FileMetadata object
        """
        try:
            logger.info(f"Storing analysis result: {analysis_id}")
            
            # Prepare analysis result data
            serialized_data = {
                "analysis_id": analysis_id,
                "document_id": document_id,
                "client_id": client_id,
                "analysis_data": analysis_data,
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "format": format,
                    "version": "1.0",
                    "storage_service": "file_based_storage"
                }
            }
            
            # Determine file type and extension
            if format == "json":
                file_type = FileType.ANALYSIS_RESULT
                filename = f"analysis_{analysis_id}.json"
            elif format == "xml":
                file_type = FileType.ANALYSIS_RESULT
                filename = f"analysis_{analysis_id}.xml"
            elif format == "yaml":
                file_type = FileType.ANALYSIS_RESULT
                filename = f"analysis_{analysis_id}.yaml"
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Store file
            file_metadata = await self.store_file(
                file_data=serialized_data,
                file_type=file_type,
                original_filename=filename,
                client_id=client_id,
                document_id=document_id,
                analysis_id=analysis_id,
                metadata={
                    "analysis_format": format,
                    "analysis_type": analysis_data.get("analysis_type", "unknown"),
                    "model_used": analysis_data.get("model_used", "unknown"),
                    "processing_time_ms": analysis_data.get("processing_time_ms", 0)
                }
            )
            
            logger.info(f"✅ Analysis result stored: {file_metadata.file_id}")
            return file_metadata
            
        except Exception as e:
            logger.error(f"❌ Error storing analysis result: {e}")
            raise
    
    async def retrieve_analysis_result(self, analysis_id: str) -> Dict[str, Any]:
        """
        Retrieve analysis result
        
        Args:
            analysis_id: Analysis identifier
            
        Returns:
            Analysis result data
        """
        try:
            logger.info(f"Retrieving analysis result: {analysis_id}")
            
            # Find file by analysis ID
            file_metadata = await self._find_file_by_analysis_id(analysis_id)
            if not file_metadata:
                raise FileNotFoundError(f"Analysis result not found: {analysis_id}")
            
            # Retrieve file
            file_content, _ = await self.retrieve_file(file_metadata.file_id)
            
            # Parse content
            if file_metadata.file_path.endswith('.json'):
                analysis_data = json.loads(file_content.decode('utf-8'))
            else:
                raise ValueError(f"Unsupported file format: {file_metadata.file_path}")
            
            logger.info(f"✅ Analysis result retrieved: {analysis_id}")
            return analysis_data
            
        except Exception as e:
            logger.error(f"❌ Error retrieving analysis result: {e}")
            raise
    
    # ==================== FILE VERSIONING ====================
    
    async def create_file_version(
        self,
        file_id: str,
        new_file_data: Union[bytes, str, Dict[str, Any]],
        version_comment: Optional[str] = None
    ) -> FileMetadata:
        """
        Create a new version of an existing file
        
        Args:
            file_id: Original file identifier
            new_file_data: New file content
            version_comment: Comment for this version
            
        Returns:
            FileMetadata for new version
        """
        try:
            logger.info(f"Creating new version for file: {file_id}")
            
            # Get original file metadata
            original_metadata = await self._get_file_metadata(file_id)
            if not original_metadata:
                raise FileNotFoundError(f"Original file not found: {file_id}")
            
            # Calculate new version number
            latest_version = await self._get_latest_version(original_metadata.parent_document_id or file_id)
            new_version = latest_version + 1
            
            # Generate new file path
            new_file_path = self.generate_file_path(
                file_type=original_metadata.file_type,
                client_id=original_metadata.client_id,
                document_id=original_metadata.parent_document_id,
                analysis_id=original_metadata.analysis_id,
                filename=original_metadata.original_filename,
                version=new_version
            )
            
            # Convert data to bytes
            if isinstance(new_file_data, dict):
                file_bytes = json.dumps(new_file_data, indent=2, default=str).encode('utf-8')
            elif isinstance(new_file_data, str):
                file_bytes = new_file_data.encode('utf-8')
            else:
                file_bytes = new_file_data
            
            # Write new version
            async with aiofiles.open(new_file_path, 'wb') as f:
                await f.write(file_bytes)
            
            # Create new metadata
            file_stat = new_file_path.stat()
            checksum = hashlib.sha256(file_bytes).hexdigest()
            
            new_metadata = FileMetadata(
                file_id=str(uuid.uuid4()),
                original_filename=original_metadata.original_filename,
                file_type=original_metadata.file_type,
                storage_tier=original_metadata.storage_tier,
                file_path=str(new_file_path),
                file_size=file_stat.st_size,
                mime_type=original_metadata.mime_type,
                checksum=checksum,
                created_at=datetime.fromtimestamp(file_stat.st_ctime),
                modified_at=datetime.fromtimestamp(file_stat.st_mtime),
                accessed_at=datetime.fromtimestamp(file_stat.st_atime),
                version=new_version,
                parent_document_id=original_metadata.parent_document_id,
                analysis_id=original_metadata.analysis_id,
                client_id=original_metadata.client_id,
                tags=original_metadata.tags.copy(),
                metadata={
                    **original_metadata.metadata,
                    "version_comment": version_comment,
                    "parent_file_id": file_id,
                    "version_created_at": datetime.now().isoformat()
                }
            )
            
            # Store new metadata
            await self._store_file_metadata(new_metadata)
            
            # Register new file
            self.file_registry[new_metadata.file_id] = new_metadata
            
            logger.info(f"✅ File version created: {new_metadata.file_id} (v{new_version})")
            return new_metadata
            
        except Exception as e:
            logger.error(f"❌ Error creating file version: {e}")
            raise
    
    async def get_file_versions(self, document_id: str) -> List[FileMetadata]:
        """
        Get all versions of a file
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of file metadata for all versions
        """
        try:
            logger.info(f"Getting file versions: {document_id}")
            
            # Find all files for this document
            versions = await self._find_files_by_document_id(document_id)
            
            # Sort by version number
            versions.sort(key=lambda x: x.version)
            
            logger.info(f"✅ Found {len(versions)} versions for document {document_id}")
            return versions
            
        except Exception as e:
            logger.error(f"❌ Error getting file versions: {e}")
            raise
    
    # ==================== ARCHIVING ====================
    
    async def archive_files(
        self,
        file_ids: List[str],
        archive_name: Optional[str] = None,
        compression_level: int = 6
    ) -> FileMetadata:
        """
        Archive multiple files into a single archive
        
        Args:
            file_ids: List of file identifiers to archive
            archive_name: Name for the archive
            compression_level: Compression level (0-9)
            
        Returns:
            FileMetadata for the archive
        """
        try:
            logger.info(f"Archiving {len(file_ids)} files")
            
            # Generate archive name
            if not archive_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"archive_{timestamp}"
            
            # Create temporary directory for archive
            temp_dir = self.base_path / "temp" / f"archive_{uuid.uuid4().hex[:8]}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Collect files to archive
                files_to_archive = []
                for file_id in file_ids:
                    file_content, file_metadata = await self.retrieve_file(file_id)
                    
                    # Create file in temp directory
                    temp_file_path = temp_dir / file_metadata.original_filename
                    async with aiofiles.open(temp_file_path, 'wb') as f:
                        await f.write(file_content)
                    
                    files_to_archive.append((temp_file_path, file_metadata))
                
                # Create archive
                archive_path = temp_dir / f"{archive_name}.zip"
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zipf:
                    for temp_file_path, file_metadata in files_to_archive:
                        # Add file to archive with metadata
                        arcname = f"{file_metadata.file_type.value}/{file_metadata.original_filename}"
                        zipf.write(temp_file_path, arcname)
                        
                        # Add metadata file
                        metadata_filename = f"{file_metadata.original_filename}.metadata.json"
                        metadata_dict = asdict(file_metadata)
                        # Convert enum to string for JSON serialization
                        metadata_dict["file_type"] = file_metadata.file_type.value
                        metadata_dict["storage_tier"] = file_metadata.storage_tier.value
                        metadata_content = json.dumps(metadata_dict, indent=2, default=str)
                        zipf.writestr(f"metadata/{metadata_filename}", metadata_content)
                
                # Read archive content
                async with aiofiles.open(archive_path, 'rb') as f:
                    archive_content = await f.read()
                
                # Store archive
                archive_metadata = await self.store_file(
                    file_data=archive_content,
                    file_type=FileType.ARCHIVE,
                    original_filename=f"{archive_name}.zip",
                    metadata={
                        "archived_files": len(file_ids),
                        "compression_level": compression_level,
                        "archive_created_at": datetime.now().isoformat(),
                        "file_ids": file_ids
                    }
                )
                
                logger.info(f"✅ Archive created: {archive_metadata.file_id}")
                return archive_metadata
                
            finally:
                # Clean up temp directory
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"❌ Error creating archive: {e}")
            raise
    
    async def extract_archive(self, archive_id: str, extract_to: Optional[Path] = None) -> List[FileMetadata]:
        """
        Extract files from an archive
        
        Args:
            archive_id: Archive file identifier
            extract_to: Directory to extract to (default: temp directory)
            
        Returns:
            List of extracted file metadata
        """
        try:
            logger.info(f"Extracting archive: {archive_id}")
            
            # Get archive metadata
            archive_metadata = await self._get_file_metadata(archive_id)
            if not archive_metadata:
                raise FileNotFoundError(f"Archive not found: {archive_id}")
            
            # Get archive content
            archive_content, _ = await self.retrieve_file(archive_id)
            
            # Create extraction directory
            if not extract_to:
                extract_to = self.base_path / "temp" / f"extract_{uuid.uuid4().hex[:8]}"
            
            extract_to.mkdir(parents=True, exist_ok=True)
            
            try:
                # Extract archive
                extracted_files = []
                with zipfile.ZipFile(io.BytesIO(archive_content)) as zipf:
                    for file_info in zipf.filelist:
                        if not file_info.filename.endswith('.metadata.json'):
                            # Extract file
                            zipf.extract(file_info, extract_to)
                            
                            # Find corresponding metadata
                            metadata_filename = f"{file_info.filename}.metadata.json"
                            try:
                                metadata_content = zipf.read(metadata_filename)
                                metadata_dict = json.loads(metadata_content.decode('utf-8'))
                                
                                # Create new file metadata
                                extracted_file_metadata = FileMetadata(**metadata_dict)
                                extracted_file_metadata.file_path = str(extract_to / file_info.filename)
                                extracted_file_metadata.file_id = str(uuid.uuid4())  # New ID
                                
                                extracted_files.append(extracted_file_metadata)
                                
                            except KeyError:
                                logger.warning(f"Metadata not found for {file_info.filename}")
                
                logger.info(f"✅ Archive extracted: {len(extracted_files)} files")
                return extracted_files
                
            finally:
                # Note: Don't clean up extract_to as caller might need the files
                pass
                
        except Exception as e:
            logger.error(f"❌ Error extracting archive: {e}")
            raise
    
    # ==================== METADATA MANAGEMENT ====================
    
    async def _store_file_metadata(self, file_metadata: FileMetadata):
        """Store file metadata"""
        metadata_path = self.base_path / "metadata" / f"{file_metadata.file_id}.json"
        
        metadata_dict = asdict(file_metadata)
        # Convert enums to strings for JSON serialization
        metadata_dict["file_type"] = file_metadata.file_type.value
        metadata_dict["storage_tier"] = file_metadata.storage_tier.value
        metadata_dict["created_at"] = file_metadata.created_at.isoformat()
        metadata_dict["modified_at"] = file_metadata.modified_at.isoformat()
        metadata_dict["accessed_at"] = file_metadata.accessed_at.isoformat()
        
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata_dict, indent=2))
    
    async def _get_file_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata"""
        metadata_path = self.base_path / "metadata" / f"{file_id}.json"
        
        if not metadata_path.exists():
            return None
        
        try:
            async with aiofiles.open(metadata_path, 'r') as f:
                metadata_dict = json.loads(await f.read())
            
            # Convert datetime strings back to datetime objects
            metadata_dict["created_at"] = datetime.fromisoformat(metadata_dict["created_at"])
            metadata_dict["modified_at"] = datetime.fromisoformat(metadata_dict["modified_at"])
            metadata_dict["accessed_at"] = datetime.fromisoformat(metadata_dict["accessed_at"])
            
            # Convert string enums back to enum objects
            if isinstance(metadata_dict.get("file_type"), str):
                metadata_dict["file_type"] = FileType(metadata_dict["file_type"])
            if isinstance(metadata_dict.get("storage_tier"), str):
                metadata_dict["storage_tier"] = StorageTier(metadata_dict["storage_tier"])
            
            return FileMetadata(**metadata_dict)
            
        except Exception as e:
            logger.error(f"Error reading metadata for {file_id}: {e}")
            return None
    
    async def _delete_file_metadata(self, file_id: str):
        """Delete file metadata"""
        metadata_path = self.base_path / "metadata" / f"{file_id}.json"
        if metadata_path.exists():
            metadata_path.unlink()
    
    async def _find_file_by_analysis_id(self, analysis_id: str) -> Optional[FileMetadata]:
        """Find file by analysis ID"""
        metadata_dir = self.base_path / "metadata"
        
        for metadata_file in metadata_dir.glob("*.json"):
            try:
                async with aiofiles.open(metadata_file, 'r') as f:
                    metadata_dict = json.loads(await f.read())
                
                if metadata_dict.get("analysis_id") == analysis_id:
                    # Convert datetime strings back to datetime objects
                    metadata_dict["created_at"] = datetime.fromisoformat(metadata_dict["created_at"])
                    metadata_dict["modified_at"] = datetime.fromisoformat(metadata_dict["modified_at"])
                    metadata_dict["accessed_at"] = datetime.fromisoformat(metadata_dict["accessed_at"])
                    
                    return FileMetadata(**metadata_dict)
                    
            except Exception as e:
                logger.warning(f"Error reading metadata file {metadata_file}: {e}")
                continue
        
        return None
    
    async def _find_files_by_document_id(self, document_id: str) -> List[FileMetadata]:
        """Find all files by document ID"""
        metadata_dir = self.base_path / "metadata"
        files = []
        
        for metadata_file in metadata_dir.glob("*.json"):
            try:
                async with aiofiles.open(metadata_file, 'r') as f:
                    metadata_dict = json.loads(await f.read())
                
                if metadata_dict.get("parent_document_id") == document_id:
                    # Convert datetime strings back to datetime objects
                    metadata_dict["created_at"] = datetime.fromisoformat(metadata_dict["created_at"])
                    metadata_dict["modified_at"] = datetime.fromisoformat(metadata_dict["modified_at"])
                    metadata_dict["accessed_at"] = datetime.fromisoformat(metadata_dict["accessed_at"])
                    
                    files.append(FileMetadata(**metadata_dict))
                    
            except Exception as e:
                logger.warning(f"Error reading metadata file {metadata_file}: {e}")
                continue
        
        return files
    
    async def _get_latest_version(self, document_id: str) -> int:
        """Get latest version number for a document"""
        files = await self._find_files_by_document_id(document_id)
        if not files:
            return 0
        
        return max(file.version for file in files)
    
    # ==================== UTILITY METHODS ====================
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_files = 0
            total_size = 0
            files_by_type = {}
            files_by_tier = {}
            
            metadata_dir = self.base_path / "metadata"
            
            for metadata_file in metadata_dir.glob("*.json"):
                try:
                    async with aiofiles.open(metadata_file, 'r') as f:
                        metadata_dict = json.loads(await f.read())
                    
                    total_files += 1
                    total_size += metadata_dict.get("file_size", 0)
                    
                    file_type = metadata_dict.get("file_type", "unknown")
                    storage_tier = metadata_dict.get("storage_tier", "unknown")
                    
                    files_by_type[file_type] = files_by_type.get(file_type, 0) + 1
                    files_by_tier[storage_tier] = files_by_tier.get(storage_tier, 0) + 1
                    
                except Exception as e:
                    logger.warning(f"Error reading metadata file {metadata_file}: {e}")
                    continue
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "files_by_type": files_by_type,
                "files_by_tier": files_by_tier,
                "base_path": str(self.base_path),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting storage stats: {e}")
            raise
    
    async def cleanup_old_files(self, days_old: int = 30) -> int:
        """Clean up old temporary files"""
        try:
            logger.info(f"Cleaning up files older than {days_old} days")
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleaned_count = 0
            
            metadata_dir = self.base_path / "metadata"
            
            for metadata_file in metadata_dir.glob("*.json"):
                try:
                    async with aiofiles.open(metadata_file, 'r') as f:
                        metadata_dict = json.loads(await f.read())
                    
                    created_at = datetime.fromisoformat(metadata_dict["created_at"])
                    
                    if created_at < cutoff_date and metadata_dict.get("file_type") == "temp":
                        file_id = metadata_dict["file_id"]
                        await self.delete_file(file_id, permanent=True)
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.warning(f"Error processing metadata file {metadata_file}: {e}")
                    continue
            
            logger.info(f"✅ Cleaned up {cleaned_count} old files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old files: {e}")
            raise


# ==================== EXAMPLE USAGE ====================

async def example_usage():
    """Example of how to use the FileBasedStorageService"""
    
    # Initialize service
    config = StorageConfig(
        base_path="/tmp/file_storage_example",
        max_file_size=50 * 1024 * 1024,  # 50MB
        enable_compression=True
    )
    
    storage_service = FileBasedStorageService(config)
    
    try:
        # Store a document
        document_content = b"This is a sample legal document content."
        doc_metadata = await storage_service.store_file(
            file_data=document_content,
            file_type=FileType.DOCUMENT,
            original_filename="sample_contract.pdf",
            client_id="ACME_Corp",
            document_id="doc-001",
            metadata={"contract_type": "NDA", "pages": 5}
        )
        
        print(f"Document stored: {doc_metadata.file_id}")
        
        # Store analysis result
        analysis_data = {
            "summary": "This is a standard NDA contract",
            "risks": [{"level": "low", "description": "Standard clause"}],
            "recommendations": ["Review confidentiality period"]
        }
        
        analysis_metadata = await storage_service.store_analysis_result(
            analysis_data=analysis_data,
            document_id="doc-001",
            analysis_id="analysis-001",
            client_id="ACME_Corp"
        )
        
        print(f"Analysis result stored: {analysis_metadata.file_id}")
        
        # Create file version
        new_content = b"This is an updated version of the document."
        version_metadata = await storage_service.create_file_version(
            file_id=doc_metadata.file_id,
            new_file_data=new_content,
            version_comment="Updated confidentiality terms"
        )
        
        print(f"File version created: {version_metadata.file_id}")
        
        # Get file versions
        versions = await storage_service.get_file_versions("doc-001")
        print(f"Found {len(versions)} versions")
        
        # Archive files
        archive_metadata = await storage_service.archive_files(
            file_ids=[doc_metadata.file_id, analysis_metadata.file_id],
            archive_name="acme_corp_documents"
        )
        
        print(f"Archive created: {archive_metadata.file_id}")
        
        # Get storage statistics
        stats = await storage_service.get_storage_stats()
        print(f"Storage stats: {stats}")
        
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(config.base_path, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(example_usage())
