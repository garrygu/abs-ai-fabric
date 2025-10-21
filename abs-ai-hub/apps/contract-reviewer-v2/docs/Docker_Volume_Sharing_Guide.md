# Docker Volume Sharing Guide for ABS Ecosystem

## Overview

This guide explains how to configure Docker volumes for sharing data between multiple applications in the ABS ecosystem, enabling a centralized document hub architecture.

## 🔄 Volume Sharing Approaches

### 1. **Named Volume Sharing (Recommended)**

Multiple apps can access the same Docker volume by using identical volume names:

```yaml
# App 1: Contract Reviewer v2
volumes:
  - shared-document-hub:/data/shared

# App 2: Legal Assistant  
volumes:
  - shared-document-hub:/data/shared

# App 3: RAG PDF Voice
volumes:
  - shared-document-hub:/data/shared
```

### 2. **External Volume References**

Create volumes outside docker-compose and reference them:

```bash
# Create shared volume
docker volume create shared-document-hub

# Use in multiple docker-compose files
```

### 3. **Host Directory Mounting**

Mount the same host directory to multiple containers:

```yaml
# All apps mount the same host directory
volumes:
  - /host/path/shared-documents:/data/shared
```

## 🏗️ Centralized Document Hub Architecture

### **Shared Storage Structure**

```
/data/shared/
├── documents/                    # All uploaded documents
│   ├── contracts/                # Contract documents
│   ├── legal_docs/              # Legal documents  
│   ├── pdfs/                    # PDF documents
│   └── other/                   # Other document types
├── analysis_results/            # Analysis results from all apps
│   ├── contract_analysis/       # Contract analysis results
│   ├── legal_analysis/          # Legal analysis results
│   └── pdf_analysis/            # PDF analysis results
├── reports/                     # Generated reports
│   ├── contract_reports/        # Contract reports
│   ├── legal_reports/           # Legal reports
│   └── pdf_reports/             # PDF reports
├── archives/                    # Compressed archives
├── templates/                   # Shared report templates
├── metadata/                    # File metadata and indexes
└── temp/                        # Temporary files
```

### **App-Specific Storage**

Each app maintains its own private storage:

```
/data/app-specific/
├── logs/                        # Application logs
├── cache/                       # App-specific cache
├── config/                      # App configuration
└── temp/                        # App temporary files
```

## 🔧 Implementation Examples

### **Contract Reviewer v2 Configuration**

```yaml
services:
  contract-reviewer-v2-integrated:
    volumes:
      # Shared document storage
      - shared-document-hub:/data/shared
      # App-specific storage
      - contract-reviewer-v2-logs:/data/logs
      - contract-reviewer-v2-cache:/data/cache
    environment:
      - FILE_STORAGE_PATH=/data/shared/file_storage
      - SHARED_STORAGE_PATH=/data/shared
```

### **Legal Assistant Configuration**

```yaml
services:
  legal-assistant:
    volumes:
      # Shared document storage
      - shared-document-hub:/data/shared
      # App-specific storage
      - legal-assistant-logs:/data/logs
      - legal-assistant-cache:/data/cache
    environment:
      - DOCUMENT_PATH=/data/shared/legal_documents
      - SHARED_STORAGE_PATH=/data/shared
```

### **RAG PDF Voice Configuration**

```yaml
services:
  rag-pdf-voice:
    volumes:
      # Shared document storage
      - shared-document-hub:/data/shared
      # App-specific storage
      - rag-pdf-voice-logs:/data/logs
      - rag-pdf-voice-cache:/data/cache
    environment:
      - PDF_STORAGE_PATH=/data/shared/pdf_documents
      - SHARED_STORAGE_PATH=/data/shared
```

## 🔒 Security Considerations

### **1. Access Control**

```yaml
# Use read-only mounts where appropriate
volumes:
  - shared-document-hub:/data/shared:ro  # Read-only access

# Or use specific permissions
volumes:
  - shared-document-hub:/data/shared:rw  # Read-write access
```

### **2. User Permissions**

```dockerfile
# In Dockerfile, create shared user
RUN groupadd -r sharedgroup && useradd -r -g sharedgroup shareduser
RUN chown -R shareduser:sharedgroup /data/shared
USER shareduser
```

### **3. Volume Labels**

```yaml
volumes:
  shared-document-hub:
    driver: local
    labels:
      - "abs.shared=true"
      - "abs.access=multi-app"
      - "abs.security=restricted"
```

## 📊 Volume Management Commands

### **Create Shared Volume**

```bash
# Create shared volume
docker volume create shared-document-hub

# Create with specific driver options
docker volume create \
  --driver local \
  --opt type=none \
  --opt o=bind \
  --opt device=/host/path/shared-documents \
  shared-document-hub
```

### **Inspect Shared Volume**

```bash
# List all volumes
docker volume ls

# Inspect specific volume
docker volume inspect shared-document-hub

# Check volume usage
docker system df -v
```

### **Backup Shared Volume**

```bash
# Backup shared volume
docker run --rm \
  -v shared-document-hub:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/shared-documents-backup.tar.gz -C /data .

# Restore shared volume
docker run --rm \
  -v shared-document-hub:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/shared-documents-backup.tar.gz -C /data
```

## 🔄 Data Synchronization

### **Cross-App Data Access**

```python
# Example: Contract Reviewer accessing Legal Assistant data
import os
from pathlib import Path

class SharedDocumentService:
    def __init__(self):
        self.shared_path = Path("/data/shared")
        self.documents_path = self.shared_path / "documents"
        self.analysis_path = self.shared_path / "analysis_results"
    
    def get_all_documents(self):
        """Get all documents from all apps"""
        documents = []
        for app_dir in self.documents_path.iterdir():
            if app_dir.is_dir():
                for doc_file in app_dir.glob("**/*"):
                    if doc_file.is_file():
                        documents.append({
                            "app": app_dir.name,
                            "file": doc_file,
                            "path": str(doc_file)
                        })
        return documents
    
    def get_analysis_results(self, document_id):
        """Get analysis results from all apps for a document"""
        results = []
        for app_dir in self.analysis_path.iterdir():
            if app_dir.is_dir():
                analysis_file = app_dir / f"{document_id}.json"
                if analysis_file.exists():
                    results.append({
                        "app": app_dir.name,
                        "analysis": analysis_file
                    })
        return results
```

### **Event-Driven Synchronization**

```python
# Example: Notify other apps when document is uploaded
import redis
import json

class CrossAppNotifier:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
    
    def notify_document_uploaded(self, document_id, app_name, metadata):
        """Notify other apps about document upload"""
        message = {
            "event": "document_uploaded",
            "document_id": document_id,
            "app": app_name,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        # Publish to shared channel
        self.redis_client.publish("shared_documents", json.dumps(message))
    
    def listen_for_events(self, app_name):
        """Listen for events from other apps"""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe("shared_documents")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                if data['app'] != app_name:  # Don't process own events
                    self.handle_shared_event(data)
```

## 🚀 Deployment Strategies

### **1. Single Docker Compose (All Apps)**

```yaml
# Deploy all apps together
version: '3.8'
services:
  contract-reviewer-v2-integrated:
    # ... configuration
  legal-assistant:
    # ... configuration  
  rag-pdf-voice:
    # ... configuration
  postgresql:
    # ... shared database
  qdrant:
    # ... shared vector database
  redis:
    # ... shared cache

volumes:
  shared-document-hub:
    driver: local
```

### **2. Separate Docker Compose Files**

```bash
# Deploy apps separately but share volumes
docker-compose -f contract-reviewer-v2/docker-compose.yml up -d
docker-compose -f legal-assistant/docker-compose.yml up -d
docker-compose -f rag-pdf-voice/docker-compose.yml up -d
```

### **3. Core Services + App Services**

```bash
# Start core services first
docker-compose -f core/core.yml up -d

# Start individual apps
docker-compose -f apps/contract-reviewer-v2/docker-compose.yml up -d
docker-compose -f apps/legal-assistant/docker-compose.yml up -d
```

## 📈 Monitoring and Maintenance

### **Volume Usage Monitoring**

```bash
# Check volume usage
docker system df -v

# Monitor specific volume
docker exec container_name du -sh /data/shared

# Check volume health
docker volume inspect shared-document-hub
```

### **Cross-App Data Integrity**

```python
# Example: Data integrity checker
class SharedDataIntegrityChecker:
    def check_data_consistency(self):
        """Check data consistency across apps"""
        issues = []
        
        # Check for orphaned files
        orphaned_files = self.find_orphaned_files()
        if orphaned_files:
            issues.append(f"Found {len(orphaned_files)} orphaned files")
        
        # Check for duplicate documents
        duplicates = self.find_duplicate_documents()
        if duplicates:
            issues.append(f"Found {len(duplicates)} duplicate documents")
        
        # Check metadata consistency
        metadata_issues = self.check_metadata_consistency()
        if metadata_issues:
            issues.extend(metadata_issues)
        
        return issues
```

## ⚠️ Best Practices

### **1. Volume Naming Convention**

```yaml
# Use consistent naming
volumes:
  abs-shared-document-hub:     # Shared across all ABS apps
  abs-shared-analysis-results: # Shared analysis results
  abs-shared-reports:          # Shared reports
  contract-reviewer-v2-logs:   # App-specific logs
  legal-assistant-logs:        # App-specific logs
```

### **2. Access Patterns**

```yaml
# Define clear access patterns
volumes:
  # Read-write for document uploads
  - shared-document-hub:/data/shared:rw
  
  # Read-only for templates
  - shared-templates:/data/templates:ro
  
  # Read-write for analysis results
  - shared-analysis:/data/analysis:rw
```

### **3. Backup Strategy**

```bash
# Regular backup of shared volumes
#!/bin/bash
BACKUP_DIR="/backups/shared-volumes"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup shared document hub
docker run --rm \
  -v shared-document-hub:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/shared-documents-$DATE.tar.gz -C /data .

# Backup shared analysis results
docker run --rm \
  -v shared-analysis-results:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/shared-analysis-$DATE.tar.gz -C /data .
```

## 🎯 Summary

**Docker volumes CAN be accessed by multiple apps** with these approaches:

1. **✅ Named Volume Sharing**: Multiple apps use same volume name
2. **✅ External Volume References**: Apps reference pre-created volumes
3. **✅ Host Directory Mounting**: Apps mount same host directory
4. **✅ Centralized Document Hub**: Shared storage architecture

**Key Benefits:**
- 🔄 **Data Sharing**: Multiple apps can access same documents
- 💾 **Storage Efficiency**: Avoid duplicate document storage
- 🔍 **Cross-App Search**: Search across all apps' documents
- 📊 **Unified Analytics**: Analyze data across all apps
- 🛡️ **Centralized Backup**: Single backup for all data

**Security Considerations:**
- 🔒 **Access Control**: Proper permissions and read-only mounts
- 👤 **User Management**: Shared user accounts across containers
- 🏷️ **Volume Labels**: Proper labeling for security policies
- 🔐 **Data Encryption**: Encrypt sensitive shared data

This enables a true **Centralized Document Hub Architecture** where all ABS applications can share and collaborate on the same document repository! 🚀
