# Phase 3: File-Based Storage Implementation Guide

## Overview

This guide covers the complete implementation of Phase 3: File-Based Storage, which adds comprehensive file organization, versioning, archiving, and report generation capabilities to our Contract Reviewer v2 architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│  Contract Reviewer v2 - Enhanced with File-Based Storage       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                                │
│  File Management | Report Generation | Document Processing      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │     REDIS        │    │   POSTGRESQL    │    │   QDRANT    │ │
│  │   (Caching)      │    │  (Persistence)  │    │ (Vectors)   │ │
│  │                 │    │                 │    │             │ │
│  │ • API Cache      │    │ • Document      │    │ • Text      │ │
│  │ • Doc Cache      │    │   Metadata      │    │   Chunks    │ │
│  │ • Analysis Cache │    │ • Analysis      │    │ • Embeddings│ │
│  │ • Session Data   │    │   Results       │    │ • Similarity│ │
│  │ • Rate Limiting  │    │ • User Data     │    │   Search    │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│                                │                                │
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                FILE-BASED STORAGE                           │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │ │
│  │  │ Documents   │  │ Analysis    │  │ Reports     │         │ │
│  │  │             │  │ Results     │  │             │         │ │
│  │  │ • PDFs      │  │ • JSON      │  │ • PDF       │         │ │
│  │  │ • DOCX      │  │ • XML       │  │ • Word      │         │ │
│  │  │ • TXT       │  │ • YAML      │  │ • HTML      │         │ │
│  │  │ • Images    │  │ • Binary    │  │ • JSON      │         │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │ │
│  │  │ Archives    │  │ Templates   │  │ Backups     │         │ │
│  │  │             │  │             │  │             │         │ │
│  │  │ • ZIP       │  │ • Report    │  │ • Automated │         │ │
│  │  │ • TAR       │  │   Templates │  │ • Manual    │         │ │
│  │  │ • Compressed│  │ • Custom    │  │ • Scheduled │         │ │
│  │  │ • Encrypted │  │   Formats   │  │ • Versioned │         │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Components Implemented

### 1. File-Based Storage Service (`file_based_storage_service.py`)
- **Hierarchical Organization**: Date-based, client-based, document-based folder structure
- **File Operations**: Store, retrieve, delete files with comprehensive metadata
- **Analysis Serialization**: JSON, XML, YAML format support for analysis results
- **File Versioning**: Complete version control with comments and metadata
- **Archiving**: ZIP compression with metadata preservation
- **Storage Management**: Statistics, cleanup, and health monitoring

### 2. Report Generation Service (`report_generation_service.py`)
- **Multiple Formats**: PDF (ReportLab), Word (python-docx), HTML, JSON
- **Template System**: Customizable report templates with styling
- **Report Types**: Analysis summary, detailed analysis, executive summary, compliance reports
- **Dynamic Content**: Charts, tables, formatted text with professional styling
- **Template Management**: Create, manage, and reuse report templates

### 3. File Management API (`file_management_api.py`)
- **REST Endpoints**: Complete API for all file operations
- **File Upload/Download**: Multipart upload with metadata
- **Version Management**: Create and manage file versions
- **Archive Operations**: Create and extract archives
- **Report Generation**: Generate reports via API
- **Storage Monitoring**: Health checks and statistics

### 4. Comprehensive Testing (`test_file_based_storage.py`)
- **Unit Tests**: Test individual components with mocked dependencies
- **Integration Tests**: Test complete workflows with real file operations
- **Performance Tests**: Test bulk operations and scalability
- **Error Handling**: Test error scenarios and recovery

## Setup Instructions

### 1. Prerequisites

Ensure all services are running:
```bash
# Check PostgreSQL
docker exec document-hub-postgres pg_isready -U hub_user -d document_hub

# Check Redis
docker exec redis redis-cli ping

# Check Qdrant
docker exec qdrant curl -s http://localhost:6333/collections
```

### 2. Install Dependencies

```bash
cd abs-ai-hub/apps/contract-reviewer-v2

# Install file storage dependencies
pip install aiofiles reportlab python-docx

# Or use requirements file
pip install -r requirements.txt
```

### 3. Configure Storage

```bash
# Set environment variables
export FILE_STORAGE_PATH="/data/file_storage"
export MAX_FILE_SIZE="100"  # MB
export ENABLE_COMPRESSION="true"
```

### 4. Initialize File Storage

```bash
# Test file storage service
python -c "
import asyncio
from file_based_storage_service import FileBasedStorageService, StorageConfig

async def test():
    config = StorageConfig(base_path='/tmp/test_storage')
    service = FileBasedStorageService(config)
    print('✅ File storage service initialized')

asyncio.run(test())
"
```

## API Endpoints

### File Operations
```http
# Upload file
POST /api/files/upload
Content-Type: multipart/form-data
file: [binary file data]
file_type: document
client_id: ACME_Corp
document_id: doc-001

# Download file
GET /api/files/download/{file_id}

# Get file info
GET /api/files/info/{file_id}

# Delete file
DELETE /api/files/delete/{file_id}?permanent=false
```

### File Versioning
```http
# Create file version
POST /api/files/version/{file_id}
{
    "version_comment": "Updated content"
}

# Get file versions
GET /api/files/versions/{document_id}
```

### Archiving
```http
# Create archive
POST /api/files/archive
{
    "file_ids": ["file1", "file2", "file3"],
    "archive_name": "client_documents",
    "compression_level": 6
}

# Extract archive
POST /api/files/extract/{archive_id}
```

### Report Generation
```http
# Generate report
POST /api/files/reports/generate
{
    "report_id": "report-001",
    "report_type": "analysis_summary",
    "format": "pdf",
    "document_ids": ["doc-001"],
    "analysis_ids": ["analysis-001"],
    "client_id": "ACME_Corp"
}

# List templates
GET /api/files/reports/templates?report_type=analysis_summary
```

### Storage Management
```http
# Get storage stats
GET /api/files/storage/stats

# Cleanup old files
POST /api/files/storage/cleanup?days_old=30

# Health check
GET /api/files/storage/health
```

## Usage Examples

### 1. File Upload and Storage

```python
import requests

# Upload document
with open("contract.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8080/api/files/upload",
        files={"file": f},
        params={
            "file_type": "document",
            "client_id": "ACME_Corp",
            "document_id": "doc-001",
            "metadata": '{"contract_type": "NDA", "pages": 5}'
        }
    )

result = response.json()
print(f"File uploaded: {result['file_id']}")
print(f"File path: {result['file_path']}")
```

### 2. Store Analysis Results

```python
# Store analysis result
analysis_data = {
    "summary": "Comprehensive analysis of confidentiality agreement",
    "risks": [{"level": "low", "description": "Standard clause"}],
    "recommendations": ["Review confidentiality period"]
}

response = requests.post(
    "http://localhost:8080/api/files/upload",
    files={"file": ("analysis.json", json.dumps(analysis_data))},
    params={
        "file_type": "analysis_result",
        "client_id": "ACME_Corp",
        "document_id": "doc-001",
        "analysis_id": "analysis-001"
    }
)
```

### 3. Generate Reports

```python
# Generate PDF report
report_request = {
    "report_id": "report-001",
    "report_type": "analysis_summary",
    "format": "pdf",
    "document_ids": ["doc-001"],
    "analysis_ids": ["analysis-001"],
    "client_id": "ACME_Corp",
    "include_charts": True,
    "include_appendix": True
}

response = requests.post(
    "http://localhost:8080/api/files/reports/generate",
    json=report_request
)

result = response.json()
print(f"Report generated: {result['file_id']}")
print(f"Download URL: {result['download_url']}")
```

### 4. File Versioning

```python
# Create file version
version_request = {
    "version_comment": "Updated confidentiality terms"
}

response = requests.post(
    f"http://localhost:8080/api/files/version/{file_id}",
    json=version_request
)

result = response.json()
print(f"Version created: {result['file_id']} (v{result['version']})")

# Get all versions
response = requests.get(f"http://localhost:8080/api/files/versions/{document_id}")
versions = response.json()
print(f"Found {versions['total_versions']} versions")
```

### 5. Archive Management

```python
# Create archive
archive_request = {
    "file_ids": ["file1", "file2", "file3"],
    "archive_name": "acme_corp_documents",
    "compression_level": 6
}

response = requests.post(
    "http://localhost:8080/api/files/archive",
    json=archive_request
)

result = response.json()
print(f"Archive created: {result['archive_id']}")
print(f"Archived {result['archived_files']} files")

# Extract archive
response = requests.post(f"http://localhost:8080/api/files/extract/{archive_id}")
extracted = response.json()
print(f"Extracted {extracted['total_files']} files")
```

## File Organization Structure

### Hierarchical Directory Layout
```
/data/file_storage/
├── documents/
│   └── 2024/
│       └── 01/
│           └── 15/
│               └── client_ACME_Corp/
│                   └── doc_doc-001/
│                       ├── contract.pdf
│                       └── contract_v2.pdf
├── analysis_results/
│   └── 2024/
│       └── 01/
│           └── 15/
│               └── client_ACME_Corp/
│                   └── doc_doc-001/
│                       └── analysis_analysis-001/
│                           └── analysis.json
├── reports/
│   └── 2024/
│       └── 01/
│           └── 15/
│               └── client_ACME_Corp/
│                   ├── report_001.pdf
│                   ├── report_002.docx
│                   └── report_003.html
├── archives/
│   └── 2024/
│       └── 01/
│           └── 15/
│               └── archive_acme_corp_documents.zip
├── templates/
│   ├── analysis_summary_default.json
│   ├── detailed_analysis_default.json
│   └── executive_summary_default.json
├── backups/
│   └── 2024/
│       └── 01/
│           └── 15/
│               └── backup_20240115.zip
├── temp/
│   └── temp_files/
└── metadata/
    ├── file1.json
    ├── file2.json
    └── ...
```

### File Naming Conventions
- **Documents**: `{original_filename}` or `{file_type}_{timestamp}_{uuid}.{ext}`
- **Analysis Results**: `analysis_{analysis_id}.json`
- **Reports**: `{report_type}_{report_id}.{format}`
- **Archives**: `{archive_name}_{timestamp}.zip`
- **Versions**: `{filename}_v{version}.{ext}`

## Configuration Options

### Storage Configuration
```python
config = StorageConfig(
    base_path="/data/file_storage",           # Base storage directory
    max_file_size=100 * 1024 * 1024,         # 100MB max file size
    max_files_per_directory=10000,           # Max files per directory
    enable_compression=True,                  # Enable compression
    enable_encryption=False,                  # Enable encryption (future)
    retention_days=2555,                      # 7 years retention
    backup_enabled=True,                      # Enable backups
    backup_frequency_days=30,                 # Backup frequency
    archive_enabled=True,                     # Enable archiving
    archive_frequency_days=90                 # Archive frequency
)
```

### Report Configuration
```python
# Report templates
template_data = {
    "sections": [
        "executive_summary",
        "key_findings", 
        "risk_assessment",
        "recommendations",
        "appendix"
    ],
    "styling": {
        "font_family": "Helvetica",
        "font_size": 12,
        "line_spacing": 1.2,
        "margins": {"top": 1, "bottom": 1, "left": 1, "right": 1}
    }
}
```

## Testing

### Run Unit Tests
```bash
# Test file storage functionality
python -m pytest test_file_based_storage.py -v

# Test specific components
python -m pytest test_file_based_storage.py::TestFileBasedStorageService -v
python -m pytest test_file_based_storage.py::TestReportGenerationService -v
```

### Run Integration Tests
```bash
# Test with real file operations
python -m pytest test_file_based_storage.py::TestFileManagementIntegration -v
```

### Run Performance Tests
```bash
# Test bulk operations
python -m pytest test_file_based_storage.py::TestFileManagementPerformance -v
```

## Monitoring

### Check Storage Status
```bash
# Health check
curl http://localhost:8080/api/files/storage/health

# Storage statistics
curl http://localhost:8080/api/files/storage/stats
```

### Monitor File Operations
```python
from file_based_storage_service import FileBasedStorageService, StorageConfig
import asyncio

async def monitor_storage():
    config = StorageConfig(base_path="/data/file_storage")
    service = FileBasedStorageService(config)
    
    stats = await service.get_storage_stats()
    print(f"Total files: {stats['total_files']}")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")
    print(f"Files by type: {stats['files_by_type']}")
    print(f"Files by tier: {stats['files_by_tier']}")

asyncio.run(monitor_storage())
```

## Performance Optimization

### 1. File Size Optimization
- **Compression**: Enable compression for text files
- **Chunking**: Process large files in chunks
- **Streaming**: Use streaming for large file operations

### 2. Directory Structure Optimization
- **Hierarchical**: Use date-based and client-based organization
- **Limits**: Enforce maximum files per directory
- **Cleanup**: Regular cleanup of temporary files

### 3. Storage Tier Management
```python
# Move files between storage tiers
await storage_service.move_to_tier(file_id, StorageTier.COLD)

# Archive old files
await storage_service.archive_old_files(days_old=90)
```

### 4. Batch Operations
```python
# Batch file operations
file_ids = ["file1", "file2", "file3"]
await storage_service.batch_delete(file_ids)
await storage_service.batch_archive(file_ids)
```

## Troubleshooting

### Common Issues

#### 1. File Size Limits
```python
# Check file size before upload
if file_size > config.max_file_size:
    raise ValueError(f"File size {file_size} exceeds maximum {config.max_file_size}")
```

#### 2. Directory Permission Issues
```bash
# Check directory permissions
ls -la /data/file_storage/
chmod 755 /data/file_storage/
```

#### 3. Disk Space Issues
```bash
# Check disk space
df -h /data/file_storage/
du -sh /data/file_storage/*
```

#### 4. Report Generation Issues
```python
# Check dependencies
try:
    import reportlab
    print("ReportLab available")
except ImportError:
    print("Install ReportLab: pip install reportlab")

try:
    import docx
    print("python-docx available")
except ImportError:
    print("Install python-docx: pip install python-docx")
```

### Error Handling
```python
try:
    file_metadata = await storage_service.store_file(...)
except FileNotFoundError:
    logger.error("File not found")
except PermissionError:
    logger.error("Permission denied")
except OSError as e:
    logger.error(f"OS error: {e}")
```

## Best Practices

### 1. File Organization
- **Consistent Naming**: Use consistent naming conventions
- **Metadata**: Always include comprehensive metadata
- **Versioning**: Use version control for important files
- **Cleanup**: Regular cleanup of temporary files

### 2. Report Generation
- **Templates**: Use templates for consistent formatting
- **Caching**: Cache frequently generated reports
- **Formats**: Choose appropriate formats for different use cases
- **Validation**: Validate report data before generation

### 3. Storage Management
- **Monitoring**: Regular monitoring of storage usage
- **Backups**: Regular backups of important data
- **Archiving**: Archive old files to save space
- **Security**: Implement proper access controls

### 4. Performance
- **Batch Operations**: Use batch operations for efficiency
- **Compression**: Enable compression for text files
- **Streaming**: Use streaming for large files
- **Caching**: Cache frequently accessed files

## Next Steps

1. **Test the implementation** with sample documents and reports
2. **Configure storage settings** for your specific use case
3. **Set up monitoring** and alerting for storage usage
4. **Implement backup strategies** for data protection
5. **Integrate with existing workflows** for seamless operation

The file-based storage implementation provides comprehensive document management, versioning, archiving, and report generation capabilities while maintaining the clean PostgreSQL-first architecture with vector search integration!
