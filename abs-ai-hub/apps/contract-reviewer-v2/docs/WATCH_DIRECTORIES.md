# Watch Directories Feature

## Overview

The Watch Directories feature allows the Contract Reviewer v2 app to automatically process documents from configured locations including local folders, network paths, and cloud drives. The system monitors these directories and automatically processes new PDF and Word documents when they are added.

## Features

- **Automatic Document Processing**: Files placed in watched directories are automatically detected and processed
- **Multiple Location Types**: Support for local folders, network paths (UNC), and cloud drives
- **File Type Filtering**: Only processes PDF, DOC, and DOCX files
- **Recursive Scanning**: Option to include subdirectories in monitoring
- **Manual Scanning**: Trigger on-demand scans of configured directories
- **Enable/Disable**: Toggle monitoring without removing configurations
- **Deduplication**: Prevents reprocessing of already-processed files using SHA256 hashing

## Architecture

### Components

1. **WatchDirectoryService** (`watch_directory_service.py`)
   - File system monitoring using Python's watchdog library
   - Automatic file detection and processing
   - Database management for watch configurations
   - Process tracking to avoid duplicates

2. **Database Tables**
   - `watch_directories`: Stores watch configuration
   - `processed_watch_files`: Tracks processed files and their hashes

3. **API Endpoints** (`app_integrated.py`)
   - `GET /api/watch-directories`: List all configured directories
   - `POST /api/watch-directories`: Add a new watch directory
   - `DELETE /api/watch-directories/{id}`: Remove a watch directory
   - `POST /api/watch-directories/{id}/toggle`: Enable/disable monitoring
   - `POST /api/watch-directories/{id}/scan`: Manually scan a directory

4. **UI Components** (`static/index.html`)
   - Watch Directories panel in the sidebar
   - Modal dialog for adding new directories
   - List of configured directories with controls
   - Enable/disable, scan, and remove buttons

## Usage

### Adding a Watch Directory

1. Click the "Add" button in the Watch Directories section
2. Enter the directory path (local, network, or cloud)
3. Select the path type:
   - **Local**: `C:\Documents\Contracts` or `/data/documents`
   - **Network**: `\\server\share\documents`
   - **Cloud**: Cloud drive mount points
4. Choose whether to watch subdirectories
5. Click "Add"

### Managing Watch Directories

- **Enable/Disable**: Toggle monitoring without removing the configuration
- **Scan Now**: Manually trigger a scan for new files
- **Remove**: Delete the watch configuration

### Supported File Types

- PDF files (`.pdf`)
- Word documents (`.doc`, `.docx`)

## Configuration Options

When adding a watch directory, you can configure:

- **Path**: The directory path to monitor
- **Path Type**: Local, Network, or Cloud
- **Recursive**: Whether to include subdirectories
- **Enabled**: Start monitoring immediately or enable later

## How It Works

1. **File Detection**: The watchdog library monitors configured directories for file creation/modification events
2. **Hashing**: Each detected file is hashed using SHA256 to prevent duplicate processing
3. **Deduplication Check**: The system checks if the file hash has already been processed
4. **Processing**: New files are:
   - Stored in the database with metadata
   - Processed for text extraction
   - Chunked and indexed in the vector database
   - Made available for search and analysis
5. **Tracking**: All processed files are recorded with their hashes and processing status

## Technical Details

### File Monitoring

Uses Python's `watchdog` library which provides cross-platform file system event monitoring. The service watches for:
- File creation events (new files)
- File modification events (updated files)

### Deduplication

Files are hashed using SHA256 and stored in the `processed_watch_files` table. Before processing:
1. Calculate file hash
2. Check database for existing hash
3. Process only if hash doesn't exist

### Background Processing

File processing happens asynchronously without blocking the main application. Errors are logged and tracked in the database.

## Database Schema

### watch_directories

```sql
CREATE TABLE watch_directories (
    id UUID PRIMARY KEY,
    path TEXT NOT NULL,
    path_type VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    recursive BOOLEAN DEFAULT TRUE,
    file_patterns TEXT[],
    processed_files JSONB,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    last_scan_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT
);
```

### processed_watch_files

```sql
CREATE TABLE processed_watch_files (
    id UUID PRIMARY KEY,
    watch_directory_id UUID NOT NULL,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    document_id UUID,
    processing_status VARCHAR(50),
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB,
    UNIQUE(watch_directory_id, file_path)
);
```

## Dependencies

Added to `requirements.txt`:
- `watchdog==3.0.0` - File system monitoring
- `asyncpg==0.29.0` - PostgreSQL async driver

## Security Considerations

- Network paths require proper authentication
- Cloud drives need mounted access
- The service respects file system permissions
- File hashes prevent duplicate processing
- Error handling prevents service crashes

## Limitations

- Windows: Network paths must be accessible to the service
- Linux/Mac: Some cloud drive mount points may need special permissions
- File size limits are enforced (configured via `MAX_FILE_SIZE`)
- Only PDF and Word documents are processed

## Troubleshooting

### Files Not Being Processed

1. Check if the watch directory is enabled
2. Verify the path exists and is accessible
3. Check logs for errors
4. Ensure files are PDF, DOC, or DOCX format
5. Try manual scan to test the configuration

### Performance

- Large directories with many files may take time to scan
- Consider disabling recursive scanning for large hierarchies
- Use manual scan instead of continuous monitoring for busy directories

## Future Enhancements

- Support for additional file formats
- Configurable file size limits per directory
- Email notifications on new documents
- Integration with cloud storage APIs (OneDrive, Google Drive, Dropbox)
- Scheduling automatic scans at specific times
- Per-directory processing rules and filters

