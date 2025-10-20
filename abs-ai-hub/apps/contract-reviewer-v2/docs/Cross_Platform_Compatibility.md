# Cross-Platform Compatibility for Shared Document Storage

## Overview
This document analyzes the cross-platform compatibility of the shared document storage architecture and provides solutions for both Windows and Ubuntu environments.

## Current Architecture Analysis

### ✅ Cross-Platform Compatible Components

#### 1. PostgreSQL Database
```python
# Works on both Windows and Ubuntu via Docker
import asyncpg

# Connection string works identically on both platforms
conn = await asyncpg.connect("postgresql://user:pass@localhost/document_hub")
```

#### 2. JSON Files
```python
# JSON is platform-agnostic
import json

# Works identically on both platforms
with open(analysis_path, 'w') as f:
    json.dump(analysis_result, f)
```

#### 2. Docker Containers
```yaml
# Docker provides platform abstraction
volumes:
  - shared-data:/abs-shared-data  # Works on both Windows and Ubuntu
```

### ⚠️ Platform-Specific Considerations

#### 1. File Path Handling
```python
# Current implementation uses Path objects (good!)
from pathlib import Path

# This works on both platforms
base_path = Path("/abs-shared-data")  # Ubuntu
base_path = Path("C:/abs-shared-data")  # Windows

# But we need to handle path differences
def get_shared_data_path():
    """Get platform-appropriate shared data path"""
    if os.name == 'nt':  # Windows
        return Path("C:/abs-shared-data")
    else:  # Unix-like (Ubuntu)
        return Path("/abs-shared-data")
```

#### 2. File Permissions
```python
# Different permission models
def set_file_permissions(file_path: Path):
    """Set appropriate permissions for the platform"""
    if os.name == 'nt':  # Windows
        # Windows uses ACLs - handled by Docker
        pass
    else:  # Ubuntu
        # Unix permissions
        file_path.chmod(0o644)  # Read/write for owner, read for others
```

## Recommended Cross-Platform Solution

### 1. Environment-Based Configuration

#### Configuration Service
```python
import os
import platform
from pathlib import Path

class CrossPlatformConfig:
    def __init__(self):
        self.platform = platform.system().lower()
        self.is_windows = self.platform == 'windows'
        self.is_linux = self.platform == 'linux'
    
    def get_shared_data_path(self) -> Path:
        """Get platform-appropriate shared data path"""
        if self.is_windows:
            # Windows paths
            base_paths = [
                Path("C:/abs-shared-data"),
                Path("D:/abs-shared-data"),
                Path(os.environ.get('ABS_SHARED_DATA', 'C:/abs-shared-data'))
            ]
        else:
            # Linux/Ubuntu paths
            base_paths = [
                Path("/abs-shared-data"),
                Path("/opt/abs-shared-data"),
                Path(os.environ.get('ABS_SHARED_DATA', '/abs-shared-data'))
            ]
        
        # Find first available path
        for path in base_paths:
            if path.exists() or self.can_create_path(path):
                return path
        
        # Fallback to first option
        return base_paths[0]
    
    def can_create_path(self, path: Path) -> bool:
        """Check if we can create the path"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except PermissionError:
            return False
    
    def get_docker_volume_mapping(self) -> dict:
        """Get Docker volume mapping for the platform"""
        if self.is_windows:
            return {
                'type': 'bind',
                'source': 'C:/abs-shared-data',
                'target': '/abs-shared-data'
            }
        else:
            return {
                'type': 'bind',
                'source': '/abs-shared-data',
                'target': '/abs-shared-data'
            }
```

### 2. Cross-Platform File Operations

#### File Service
```python
import shutil
import stat
from pathlib import Path

class CrossPlatformFileService:
    def __init__(self, config: CrossPlatformConfig):
        self.config = config
        self.base_path = config.get_shared_data_path()
    
    def organize_file_path(self, file_path: Path, metadata: dict) -> Path:
        """Create organized file path for the platform"""
        # Use date-based organization (works on both platforms)
        upload_date = datetime.now()
        year = upload_date.year
        month = upload_date.month
        day = upload_date.day
        
        # Create path structure
        organized_path = (
            self.base_path / "documents" / "raw" / 
            str(year) / f"{month:02d}" / f"{day:02d}" / 
            file_path.name
        )
        
        # Ensure directory exists
        organized_path.parent.mkdir(parents=True, exist_ok=True)
        
        return organized_path
    
    def move_file(self, source: Path, destination: Path) -> bool:
        """Move file with platform-appropriate handling"""
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            shutil.move(str(source), str(destination))
            
            # Set appropriate permissions
            self.set_file_permissions(destination)
            
            return True
        except Exception as e:
            print(f"Error moving file: {e}")
            return False
    
    def set_file_permissions(self, file_path: Path):
        """Set platform-appropriate file permissions"""
        if self.config.is_windows:
            # Windows: Let Docker handle permissions
            pass
        else:
            # Linux: Set Unix permissions
            try:
                file_path.chmod(0o644)  # rw-r--r--
            except PermissionError:
                pass  # Ignore if we can't set permissions
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get file hash (works on both platforms)"""
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
```

### 3. Docker Compose for Both Platforms

#### Windows Docker Compose
```yaml
# docker-compose.windows.yml
version: '3.8'
services:
  contract-reviewer:
    image: contract-reviewer-v2
    volumes:
      - type: bind
        source: C:/abs-shared-data
        target: /abs-shared-data
    environment:
      - PLATFORM=windows
      - SHARED_DATA_PATH=/abs-shared-data
      - HOST_DATA_PATH=C:/abs-shared-data
  
  legal-assistant:
    image: legal-assistant
    volumes:
      - type: bind
        source: C:/abs-shared-data
        target: /abs-shared-data
    environment:
      - PLATFORM=windows
      - SHARED_DATA_PATH=/abs-shared-data
      - HOST_DATA_PATH=C:/abs-shared-data

volumes:
  shared-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: C:/abs-shared-data
```

#### Ubuntu Docker Compose
```yaml
# docker-compose.ubuntu.yml
version: '3.8'
services:
  contract-reviewer:
    image: contract-reviewer-v2
    volumes:
      - type: bind
        source: /abs-shared-data
        target: /abs-shared-data
    environment:
      - PLATFORM=linux
      - SHARED_DATA_PATH=/abs-shared-data
      - HOST_DATA_PATH=/abs-shared-data
  
  legal-assistant:
    image: legal-assistant
    volumes:
      - type: bind
        source: /abs-shared-data
        target: /abs-shared-data
    environment:
      - PLATFORM=linux
      - SHARED_DATA_PATH=/abs-shared-data
      - HOST_DATA_PATH=/abs-shared-data

volumes:
  shared-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /abs-shared-data
```

### 4. Platform Detection and Setup

#### Setup Script for Windows
```powershell
# setup-windows.ps1
Write-Host "Setting up ABS Shared Storage on Windows..."

# Create shared data directory
$sharedPath = "C:\abs-shared-data"
if (-not (Test-Path $sharedPath)) {
    New-Item -ItemType Directory -Path $sharedPath -Force
    Write-Host "Created directory: $sharedPath"
}

# Set permissions (if needed)
# icacls $sharedPath /grant Everyone:F /T

# Create subdirectories
$subdirs = @(
    "documents\raw",
    "documents\processed\text",
    "documents\processed\metadata",
    "documents\chunks",
    "analyses\contract-reviewer",
    "analyses\legal-assistant",
    "analyses\onyx",
    "vectors\document-chunks",
    "vectors\analysis-insights",
    "shared-db",
    "cache\redis",
    "cache\temp"
)

foreach ($dir in $subdirs) {
    $fullPath = Join-Path $sharedPath $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force
        Write-Host "Created directory: $fullPath"
    }
}

Write-Host "Windows setup complete!"
```

#### Setup Script for Ubuntu
```bash
#!/bin/bash
# setup-ubuntu.sh
echo "Setting up ABS Shared Storage on Ubuntu..."

# Create shared data directory
SHARED_PATH="/abs-shared-data"
if [ ! -d "$SHARED_PATH" ]; then
    sudo mkdir -p "$SHARED_PATH"
    echo "Created directory: $SHARED_PATH"
fi

# Set permissions
sudo chown -R $USER:$USER "$SHARED_PATH"
sudo chmod -R 755 "$SHARED_PATH"

# Create subdirectories
subdirs=(
    "documents/raw"
    "documents/processed/text"
    "documents/processed/metadata"
    "documents/chunks"
    "analyses/contract-reviewer"
    "analyses/legal-assistant"
    "analyses/onyx"
    "vectors/document-chunks"
    "vectors/analysis-insights"
    "shared-db"
    "cache/redis"
    "cache/temp"
)

for dir in "${subdirs[@]}"; do
    full_path="$SHARED_PATH/$dir"
    if [ ! -d "$full_path" ]; then
        mkdir -p "$full_path"
        echo "Created directory: $full_path"
    fi
done

echo "Ubuntu setup complete!"
```

### 5. Application Code Updates

#### Updated Shared Document Service
```python
class SharedDocumentService:
    def __init__(self):
        self.config = CrossPlatformConfig()
        self.base_path = self.config.get_shared_data_path()
        self.db_path = self.base_path / "shared-db" / "documents.db"
        self.file_service = CrossPlatformFileService(self.config)
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database (works on both platforms)"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Create tables (same SQL on both platforms)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_documents (
                document_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_hash TEXT UNIQUE,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                client_id TEXT,
                case_number TEXT,
                matter_type TEXT,
                access_level TEXT DEFAULT 'private'
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_document(self, file_path: Path, metadata: dict) -> str:
        """Register document with cross-platform path handling"""
        # Generate document ID and hash
        document_id = str(uuid.uuid4())
        file_hash = self.file_service.get_file_hash(file_path)
        
        # Check for duplicates
        existing = self.find_by_hash(file_hash)
        if existing:
            return existing['document_id']
        
        # Move file to organized location
        organized_path = self.file_service.organize_file_path(file_path, metadata)
        
        if self.file_service.move_file(file_path, organized_path):
            # Register in database
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO shared_documents 
                (document_id, filename, file_hash, file_path, file_size, file_type, 
                 client_id, case_number, matter_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id, metadata['filename'], file_hash, str(organized_path),
                metadata['file_size'], metadata['file_type'], 
                metadata.get('client_id'), metadata.get('case_number'), 
                metadata.get('matter_type')
            ))
            
            conn.commit()
            conn.close()
            
            return document_id
        
        return None
```

## Testing Cross-Platform Compatibility

### Test Suite
```python
import pytest
import tempfile
from pathlib import Path

class TestCrossPlatformCompatibility:
    def test_path_handling(self):
        """Test path handling on both platforms"""
        config = CrossPlatformConfig()
        base_path = config.get_shared_data_path()
        
        # Test path operations
        test_file = base_path / "test" / "file.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test content")
        
        assert test_file.exists()
        assert test_file.read_text() == "test content"
    
    def test_database_operations(self):
        """Test SQLite operations on both platforms"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Create database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """)
            
            cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
            conn.commit()
            
            # Query database
            cursor.execute("SELECT * FROM test_table")
            result = cursor.fetchone()
            
            assert result[1] == "test"
            conn.close()
    
    def test_file_permissions(self):
        """Test file permission handling"""
        config = CrossPlatformConfig()
        file_service = CrossPlatformFileService(config)
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_text("test content")
            
            # Test permission setting
            file_service.set_file_permissions(temp_path)
            
            assert temp_path.exists()
            temp_path.unlink()
```

## Deployment Considerations

### Windows Deployment
- **Docker Desktop** required for containerization
- **WSL2** recommended for better Linux compatibility
- **PowerShell** scripts for setup and management
- **Windows paths** (C:\abs-shared-data) for host volumes

### Ubuntu Deployment
- **Docker Engine** for containerization
- **Bash scripts** for setup and management
- **Unix permissions** for file access control
- **Linux paths** (/abs-shared-data) for host volumes

### Hybrid Environments
- **Environment variables** for path configuration
- **Docker Compose** with platform-specific overrides
- **Shared network** for cross-platform communication
- **Volume mounts** with platform-appropriate paths

## Conclusion

✅ **Yes, the solution supports both Windows and Ubuntu** with the following modifications:

1. **Cross-platform path handling** using `pathlib.Path`
2. **Platform detection** and appropriate configuration
3. **Environment-based setup** scripts for both platforms
4. **Docker volume mapping** with platform-specific paths
5. **SQLite database** (platform-agnostic)
6. **JSON files** (platform-agnostic)
7. **File permission handling** appropriate for each platform

The shared storage architecture is designed to work seamlessly across both Windows and Ubuntu environments while maintaining the same functionality and data structure.
