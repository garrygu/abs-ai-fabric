# Phase 2: Qdrant Vector Storage Implementation Guide

## Overview

This guide covers the complete implementation of Phase 2: Qdrant Vector Storage, which adds semantic search capabilities to our PostgreSQL-first Contract Reviewer v2 architecture.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│  Contract Reviewer v2 - Enhanced with Vector Search            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                                │
│  Document Processing | Vector Storage | Semantic Search          │
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
└─────────────────────────────────────────────────────────────────┘
```

## Components Implemented

### 1. Vector Storage Service (`vector_storage_service.py`)
- **Text Chunking**: Paragraph, sentence, and fixed-size chunking
- **Embedding Generation**: Using SentenceTransformers (all-MiniLM-L6-v2)
- **Vector Storage**: Store and manage document chunks in Qdrant
- **Semantic Search**: Find similar content across documents
- **Document Similarity**: Find documents similar to a given document

### 2. Document Processing Service (`document_processing_service.py`)
- **Text Extraction**: PDF, DOCX, TXT file processing
- **Document Processing**: Extract, chunk, and store documents
- **Batch Processing**: Process multiple documents efficiently
- **Search Integration**: Enhanced search with document metadata

### 3. Vector Search API (`vector_search_api.py`)
- **REST Endpoints**: Complete API for vector operations
- **Semantic Search**: Search across all documents
- **Similarity Search**: Find similar documents
- **Document Processing**: Process documents for vector storage

### 4. Enhanced App (`app_enhanced_with_vectors.py`)
- **Integrated Architecture**: PostgreSQL + Qdrant + Redis
- **Enhanced Upload**: Automatic vector processing on upload
- **Semantic Search**: Built-in search functionality
- **Document Similarity**: Find similar documents

## Setup Instructions

### 1. Prerequisites

Ensure all services are running:
```bash
# Check Qdrant
docker exec qdrant curl -s http://localhost:6333/collections

# Check PostgreSQL
docker exec document-hub-postgres pg_isready -U hub_user -d document_hub

# Check Redis
docker exec redis redis-cli ping
```

### 2. Install Dependencies

```bash
cd abs-ai-hub/apps/contract-reviewer-v2

# Install vector storage dependencies
pip install sentence-transformers qdrant-client

# Or use requirements file
pip install -r requirements.txt
```

### 3. Initialize Vector Storage

```bash
# Test vector storage service
python -c "
import asyncio
from vector_storage_service import VectorStorageService

async def test():
    service = VectorStorageService()
    await service.initialize()
    print('✅ Vector storage service initialized')

asyncio.run(test())
"
```

### 4. Run Enhanced App

```bash
# Use the enhanced app with vector search
python app_enhanced_with_vectors.py
```

## API Endpoints

### Document Upload with Vector Processing
```http
POST /api/upload?process_vectors=true
Content-Type: multipart/form-data

file: [binary file data]
```

### Semantic Search
```http
POST /api/search
Content-Type: application/json

{
    "query": "confidentiality agreement",
    "limit": 10,
    "score_threshold": 0.7,
    "include_analysis": false
}
```

### Find Similar Documents
```http
GET /api/similar/{document_id}?limit=5&score_threshold=0.8
```

### Vector Processing
```http
POST /api/vector/process
Content-Type: application/json

{
    "document_id": "doc-uuid",
    "file_path": "/path/to/document.pdf",
    "metadata": {"client": "ACME Corp"}
}
```

## Usage Examples

### 1. Upload and Process Document

```python
import requests

# Upload document with vector processing
with open("contract.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8080/api/upload?process_vectors=true",
        files={"file": f}
    )

result = response.json()
print(f"Document uploaded: {result['document_id']}")
print(f"Vector processing: {result['vector_processing']}")
```

### 2. Semantic Search

```python
# Search for confidentiality-related content
search_request = {
    "query": "confidentiality agreement terms",
    "limit": 10,
    "score_threshold": 0.7,
    "include_analysis": True
}

response = requests.post(
    "http://localhost:8080/api/search",
    json=search_request
)

results = response.json()
for result in results["results"]:
    print(f"Score: {result['score']:.3f}")
    print(f"Document: {result['filename']}")
    print(f"Text: {result['chunk_text'][:100]}...")
    print("---")
```

### 3. Find Similar Documents

```python
# Find documents similar to a specific document
response = requests.get(
    "http://localhost:8080/api/similar/doc-uuid-here",
    params={"limit": 5, "score_threshold": 0.8}
)

similar_docs = response.json()
for doc in similar_docs["similar_documents"]:
    print(f"Similarity: {doc['max_score']:.3f}")
    print(f"Document: {doc['filename']}")
    print("---")
```

### 4. Process Existing Document

```python
# Process an existing document for vector search
process_request = {
    "document_id": "doc-uuid-here",
    "file_path": "/path/to/document.pdf",
    "metadata": {"client": "ACME Corp", "document_type": "NDA"}
}

response = requests.post(
    "http://localhost:8080/api/vector/process",
    json=process_request
)

result = response.json()
print(f"Chunks created: {result['chunks_created']}")
print(f"Vector IDs: {result['vector_ids']}")
```

## Configuration

### Vector Storage Configuration

```python
# In vector_storage_service.py
class VectorStorageService:
    def __init__(
        self,
        qdrant_host: str = "qdrant",
        qdrant_port: int = 6333,
        embedding_model: str = "all-MiniLM-L6-v2",  # 384 dimensions
        collection_name: str = "legal_documents"
    ):
```

### Document Processing Configuration

```python
# In document_processing_service.py
class DocumentProcessingService:
    def __init__(
        self,
        vector_service: VectorStorageService,
        doc_service: DocumentService,
        chunk_size: int = 512,        # Characters per chunk
        chunk_overlap: int = 50,       # Overlap between chunks
        chunk_type: str = "paragraph"  # paragraph, sentence, fixed
    ):
```

## Testing

### Run Unit Tests
```bash
# Test vector storage functionality
python -m pytest test_vector_storage.py -v

# Test specific components
python -m pytest test_vector_storage.py::TestVectorStorageService -v
python -m pytest test_vector_storage.py::TestDocumentProcessingService -v
```

### Run Integration Tests
```bash
# Test with real Qdrant and PostgreSQL
python -m pytest test_vector_storage.py::TestVectorSearchIntegration -v
```

### Run Performance Tests
```bash
# Test bulk processing performance
python -m pytest test_vector_storage.py::TestVectorSearchPerformance -v
```

## Monitoring

### Check Vector Storage Status
```bash
# Health check
curl http://localhost:8080/api/vector/health

# Statistics
curl http://localhost:8080/api/vector/stats
```

### Check Collection Statistics
```python
from vector_storage_service import VectorStorageService
import asyncio

async def check_stats():
    service = VectorStorageService()
    await service.initialize()
    
    stats = await service.get_collection_stats()
    print(f"Vectors: {stats['vectors_count']}")
    print(f"Points: {stats['points_count']}")
    print(f"Status: {stats['status']}")
    
    await service.close()

asyncio.run(check_stats())
```

## Performance Optimization

### 1. Chunk Size Optimization
- **Small chunks (256 chars)**: Better precision, more chunks
- **Large chunks (1024 chars)**: Better context, fewer chunks
- **Recommended**: 512 characters with 50-character overlap

### 2. Embedding Model Selection
- **all-MiniLM-L6-v2**: Fast, 384 dimensions, good for general text
- **all-mpnet-base-v2**: Slower, 768 dimensions, better quality
- **sentence-transformers**: Easy to swap models

### 3. Batch Processing
```python
# Process multiple documents efficiently
document_files = [
    ("doc1", "/path/to/doc1.pdf"),
    ("doc2", "/path/to/doc2.pdf"),
    ("doc3", "/path/to/doc3.pdf")
]

results = await processing_service.process_multiple_documents(
    document_files=document_files,
    metadata={"batch": "legal_docs"}
)
```

## Troubleshooting

### Common Issues

#### 1. Qdrant Connection Issues
```bash
# Check Qdrant container
docker ps | grep qdrant

# Test Qdrant connection
docker exec qdrant curl -s http://localhost:6333/collections
```

#### 2. Embedding Model Download
```python
# Download model manually
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
```

#### 3. Memory Issues
```python
# Reduce batch size for large documents
processing_service = DocumentProcessingService(
    vector_service=vector_service,
    doc_service=doc_service,
    chunk_size=256,  # Smaller chunks
    chunk_overlap=25
)
```

#### 4. Search Quality Issues
```python
# Adjust search parameters
search_results = await processing_service.search_documents(
    query="confidentiality agreement",
    limit=20,           # More results
    score_threshold=0.5  # Lower threshold
)
```

## Best Practices

### 1. Document Processing
- **Process on upload**: Enable vector processing during document upload
- **Batch processing**: Process multiple documents together for efficiency
- **Error handling**: Always handle processing failures gracefully

### 2. Search Optimization
- **Query preprocessing**: Clean and normalize search queries
- **Result filtering**: Use metadata filters to narrow results
- **Caching**: Cache frequent search results in Redis

### 3. Vector Management
- **Regular cleanup**: Remove vectors for deleted documents
- **Monitoring**: Monitor vector database size and performance
- **Backup**: Include vector data in backup strategies

## Next Steps

1. **Test the implementation** with sample documents
2. **Optimize chunk sizes** for your specific use case
3. **Tune search parameters** for better results
4. **Monitor performance** and adjust as needed
5. **Integrate with existing workflows** for seamless operation

The vector storage implementation provides powerful semantic search capabilities while maintaining the clean PostgreSQL-first architecture!
