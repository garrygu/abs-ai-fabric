# Document Management CRUD Operations

This document explains how to use the comprehensive CRUD (Create, Read, Update, Delete) operations for documents and analysis results in the PostgreSQL-based document management system.

## Overview

The document management system provides:
- **Full CRUD operations** for documents and analysis results
- **PostgreSQL persistence** with proper indexing and relationships
- **REST API endpoints** for easy integration
- **Comprehensive testing** and validation
- **Migration tools** from Redis-only storage

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│ Document Service │───▶│   PostgreSQL    │
│                 │    │                  │    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  REST Endpoints │    │  CRUD Operations  │    │  Document Tables│
│                 │    │                  │    │  Analysis Tables│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Database Schema

### Documents Table
```sql
CREATE TABLE document_hub.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100),
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    analysis_timestamp TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'uploaded',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Analysis Results Table
```sql
CREATE TABLE document_hub.analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL,
    analysis_data JSONB NOT NULL,
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    model_used VARCHAR(100),
    processing_time_ms INTEGER,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## CRUD Operations

### 1. Document Operations

#### Create Document
```python
from document_service import DocumentService

doc_service = DocumentService()
await doc_service.initialize()

# Create a new document
document = await doc_service.create_document(
    file_path="/path/to/contract.pdf",
    original_filename="contract.pdf",
    metadata={"client": "ACME Corp", "contract_type": "NDA"},
    user_id="user123"
)

print(f"Created document: {document['id']}")
```

#### Read Documents
```python
# Get a specific document
document = await doc_service.get_document_by_id("document-uuid")

# Get documents with pagination
documents, total_count = await doc_service.get_documents(
    limit=10,
    offset=0,
    status="analyzed",
    order_by="upload_timestamp",
    order_direction="DESC"
)

print(f"Found {len(documents)} documents out of {total_count} total")
```

#### Update Document
```python
# Update document status and metadata
updated_document = await doc_service.update_document(
    document_id="document-uuid",
    updates={
        "status": "analyzed",
        "metadata": {"client": "ACME Corp", "status": "reviewed"}
    },
    user_id="user123"
)
```

#### Delete Document
```python
# Delete document and optionally its file
success = await doc_service.delete_document(
    document_id="document-uuid",
    user_id="user123",
    delete_file=True
)

if success:
    print("Document deleted successfully")
```

### 2. Analysis Result Operations

#### Create Analysis Result
```python
# Create analysis result
analysis = await doc_service.create_analysis_result(
    document_id="document-uuid",
    analysis_type="contract_review",
    analysis_data={
        "summary": "Contract analysis complete",
        "risks": [{"level": "low", "description": "Standard clause"}],
        "recommendations": ["Review confidentiality period"]
    },
    model_used="llama3.2:3b",
    processing_time_ms=1500,
    user_id="user123"
)

print(f"Created analysis: {analysis['id']}")
```

#### Read Analysis Results
```python
# Get specific analysis result
analysis = await doc_service.get_analysis_result_by_id("analysis-uuid")

# Get all analysis results for a document
analyses = await doc_service.get_analysis_results_by_document(
    document_id="document-uuid",
    analysis_type="contract_review"
)

print(f"Found {len(analyses)} analyses for document")
```

#### Delete Analysis Result
```python
# Delete analysis result
success = await doc_service.delete_analysis_result(
    analysis_id="analysis-uuid",
    user_id="user123"
)

if success:
    print("Analysis result deleted successfully")
```

## REST API Endpoints

### Document Endpoints

#### Upload Document
```http
POST /api/documents/
Content-Type: multipart/form-data

file: [binary file data]
metadata: {"client": "ACME Corp", "contract_type": "NDA"}
user_id: user123
```

#### Get Documents
```http
GET /api/documents/?limit=10&offset=0&status=analyzed&order_by=upload_timestamp&order_direction=DESC
```

#### Get Specific Document
```http
GET /api/documents/{document_id}
```

#### Update Document
```http
PUT /api/documents/{document_id}
Content-Type: application/json

{
    "status": "analyzed",
    "metadata": {"client": "ACME Corp", "status": "reviewed"}
}
```

#### Delete Document
```http
DELETE /api/documents/{document_id}?delete_file=true
```

### Analysis Result Endpoints

#### Create Analysis Result
```http
POST /api/documents/analysis
Content-Type: application/json

{
    "document_id": "document-uuid",
    "analysis_type": "contract_review",
    "analysis_data": {
        "summary": "Contract analysis complete",
        "risks": [],
        "recommendations": []
    },
    "model_used": "llama3.2:3b",
    "processing_time_ms": 1500
}
```

#### Get Analysis Results
```http
GET /api/documents/{document_id}/analysis?analysis_type=contract_review
```

#### Delete Analysis Result
```http
DELETE /api/documents/analysis/{analysis_id}
```

### Statistics Endpoints

#### Get Statistics
```http
GET /api/documents/stats/overview
```

Response:
```json
{
    "document_stats": {
        "total_documents": 25,
        "analyzed_documents": 20,
        "pending_documents": 5,
        "total_size_bytes": 1024000,
        "avg_file_size_bytes": 40960
    },
    "analysis_stats": [
        {
            "analysis_type": "contract_review",
            "total_analyses": 20,
            "avg_processing_time_ms": 1500,
            "unique_documents_analyzed": 18
        }
    ]
}
```

## Integration with Contract Reviewer v2

### Basic Integration
```python
from document_api import integrate_with_contract_reviewer
from fastapi import FastAPI

app = FastAPI()

# Add document management endpoints
integrate_with_contract_reviewer(app)
```

### Enhanced Contract Analysis
```python
from contract_reviewer_persistence import ContractReviewerWithPersistence

# Initialize enhanced reviewer
reviewer = ContractReviewerWithPersistence()
await reviewer.initialize()

# Analyze contract with persistence
result = await reviewer.analyze_contract_with_persistence(
    file_path="/path/to/contract.pdf",
    original_filename="contract.pdf",
    analysis_data={
        "summary": "Contract analysis complete",
        "risks": [],
        "recommendations": []
    }
)

print(f"Document ID: {result['document_id']}")
print(f"Analysis ID: {result['analysis_id']}")
```

## Migration from Redis-Only Storage

### Migration Helper
```python
from contract_reviewer_persistence import MigrationHelper

migration_helper = MigrationHelper()

# Migrate Redis analysis data to PostgreSQL
migration_result = await migration_helper.migrate_redis_analysis_to_postgres(
    redis_data={
        "analysis_id": "redis-analysis-id",
        "file_name": "contract.pdf",
        "summary": {
            "summary": "Contract analysis",
            "risks": [],
            "recommendations": []
        },
        "model_used": "llama3.2:3b",
        "processing_time_ms": 1500
    }
)

print(f"Migration status: {migration_result['migration_status']}")
```

## Testing

### Unit Tests
```bash
# Run unit tests
pytest test_document_service.py -v

# Run integration tests (requires PostgreSQL)
pytest test_document_service.py::TestDocumentServiceIntegration -v

# Run performance tests
pytest test_document_service.py::TestDocumentServicePerformance -v
```

### Test Coverage
The test suite covers:
- All CRUD operations for documents and analysis results
- Error handling and edge cases
- Database transactions and rollbacks
- Performance with bulk operations
- Integration with real PostgreSQL database

## Performance Considerations

### Database Indexes
The system includes optimized indexes for:
- Document filename and upload timestamp
- Analysis results by document and type
- Full-text search on document metadata
- JSONB queries on analysis data

### Connection Pooling
- Uses asyncpg connection pooling
- Configurable pool size (1-10 connections)
- Automatic connection management

### Bulk Operations
```python
# Efficient bulk document creation
tasks = []
for i in range(100):
    task = doc_service.create_document(
        file_path=f"/tmp/doc_{i}.pdf",
        original_filename=f"document_{i}.pdf"
    )
    tasks.append(task)

# Execute all tasks concurrently
documents = await asyncio.gather(*tasks)
```

## Security Features

### Audit Logging
All operations are logged in the `audit_logs` table:
- User ID and action performed
- Resource type and ID
- Timestamp and IP address
- Operation details

### Data Validation
- Pydantic models for request/response validation
- Database constraints for data integrity
- File type and size validation

### Access Control
- User-based operations tracking
- Session management
- Role-based permissions (extensible)

## Monitoring and Statistics

### Built-in Statistics Views
```sql
-- Document statistics
SELECT * FROM document_hub.document_stats;

-- Analysis statistics by type
SELECT * FROM document_hub.analysis_stats;
```

### Health Monitoring
```http
GET /api/documents/health
```

### Performance Metrics
- Processing time tracking
- Database query performance
- File upload/download metrics
- Error rates and success rates

## Best Practices

### 1. Error Handling
```python
try:
    document = await doc_service.create_document(...)
except Exception as e:
    logger.error(f"Failed to create document: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### 2. Transaction Management
```python
async with conn.transaction():
    # Multiple operations in single transaction
    document = await create_document(...)
    analysis = await create_analysis_result(...)
```

### 3. Resource Cleanup
```python
try:
    # Use document service
    result = await doc_service.create_document(...)
finally:
    await doc_service.close()
```

### 4. Pagination
```python
# Always use pagination for large datasets
documents, total = await doc_service.get_documents(
    limit=50,  # Reasonable page size
    offset=0
)
```

## Troubleshooting

### Common Issues

#### Connection Errors
```python
# Check PostgreSQL connection
try:
    await doc_service.initialize()
except Exception as e:
    print(f"Database connection failed: {e}")
    # Check if PostgreSQL container is running
    # Verify connection string
```

#### File Not Found
```python
# Ensure file exists before creating document
if not Path(file_path).exists():
    raise FileNotFoundError(f"File not found: {file_path}")
```

#### Memory Issues
```python
# Use streaming for large files
async def process_large_file(file_path):
    async with aiofiles.open(file_path, 'rb') as f:
        async for chunk in f:
            # Process chunk by chunk
            pass
```

## Future Enhancements

### Planned Features
- [ ] Document versioning
- [ ] Advanced search and filtering
- [ ] Document templates
- [ ] Automated backup and restore
- [ ] Real-time notifications
- [ ] Document collaboration features
- [ ] Advanced analytics and reporting

### Extensibility
The system is designed to be easily extensible:
- Plugin architecture for custom analysis types
- Configurable metadata schemas
- Custom validation rules
- Integration with external services

## Support

For questions or issues:
1. Check the test suite for usage examples
2. Review the API documentation
3. Check PostgreSQL logs for database issues
4. Use the health check endpoints for diagnostics
