# Contract Reviewer v2 - Integrated

A comprehensive AI-powered legal document analysis platform that combines PostgreSQL persistence, Qdrant vector search, Redis caching, and file-based storage for complete document management and analysis workflows.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 8GB+ RAM recommended
- 50GB+ free disk space

### One-Command Deployment

**Linux/macOS:**
```bash
./deploy.sh
```

**Windows:**
```cmd
deploy.bat
```

### Manual Deployment
```bash
# 1. Start services
docker-compose up -d

# 2. Check health
curl http://localhost:8082/api/health

# 3. Access application
open http://localhost:8082
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│  Contract Reviewer v2 - Integrated Application                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER                                │
│  Document Service | Vector Service | Processing | Storage       │
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

## 📋 Features

### 🔍 Document Analysis
- **AI-Powered Analysis**: Comprehensive contract analysis using advanced AI models
- **Risk Assessment**: Automated identification and classification of legal risks
- **Recommendations**: Actionable recommendations for contract improvements
- **Legal Citations**: Automatic extraction and validation of legal references
- **Compliance Checking**: GDPR, CCPA, and industry standard compliance verification

### 🔎 Semantic Search
- **Vector-Based Search**: Find documents by meaning, not just keywords
- **Similarity Matching**: Identify similar documents and clauses
- **Context-Aware Results**: Search results with relevant context and analysis
- **Multi-Document Queries**: Search across entire document collections

### 📊 Report Generation
- **Multiple Formats**: PDF, Word, HTML, and JSON report generation
- **Customizable Templates**: Professional report templates for different use cases
- **Executive Summaries**: High-level summaries for stakeholders
- **Detailed Analysis**: Comprehensive analysis reports with citations
- **Compliance Reports**: Specialized reports for regulatory compliance

### 💾 File Management
- **Version Control**: Complete file versioning with change tracking
- **Archiving**: Automated archiving and compression of old documents
- **Backup Management**: Automated backup creation and restoration
- **Storage Optimization**: Intelligent storage management and cleanup
- **Access Control**: Role-based access control for documents and reports

### ⚡ Performance & Scalability
- **Redis Caching**: High-performance caching for frequently accessed data
- **PostgreSQL Persistence**: Reliable data persistence with ACID compliance
- **Vector Search**: Fast semantic search with Qdrant vector database
- **Horizontal Scaling**: Support for multiple application instances
- **Load Balancing**: Built-in load balancing capabilities

## 🛠️ API Endpoints

### Document Management
```http
POST /api/documents/upload          # Upload and process document
GET  /api/documents                  # List documents with processing info
GET  /api/documents/info/{id}        # Get document details
POST /api/analyze/{id}               # Analyze document with AI
```

### Search and Discovery
```http
POST /api/search                     # Semantic search across documents
GET  /api/similar/{id}               # Find similar documents
```

### File Management
```http
POST /api/files/upload               # Upload files to storage
GET  /api/files/download/{id}        # Download files
POST /api/files/version/{id}         # Create file versions
POST /api/files/archive              # Create archives
```

### Report Generation
```http
POST /api/files/reports/generate     # Generate reports
GET  /api/files/reports/templates   # List report templates
```

### System Management
```http
GET  /api/health                     # Health check for all services
GET  /api/stats                      # Comprehensive system statistics
POST /api/files/storage/cleanup      # Cleanup old files
```

## 📖 Usage Examples

### Upload and Analyze Document
```bash
# Upload a contract
curl -X POST "http://localhost:8082/api/documents/upload" \
  -F "file=@contract.pdf" \
  -F "client_id=ACME_Corp" \
  -F "document_type=contract" \
  -F "process_for_search=true" \
  -F "generate_report=true"

# Analyze the document
curl -X POST "http://localhost:8082/api/analyze/doc-001" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "comprehensive",
    "include_risks": true,
    "include_recommendations": true,
    "include_citations": true,
    "process_for_search": true,
    "generate_report": true,
    "report_format": "pdf"
  }'
```

### Semantic Search
```bash
# Search for confidentiality clauses
curl -X POST "http://localhost:8082/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "confidentiality agreement",
    "limit": 10,
    "score_threshold": 0.7,
    "include_analysis": true,
    "include_reports": true
  }'
```

### File Management
```bash
# Create file version
curl -X POST "http://localhost:8082/api/files/version/file-001" \
  -H "Content-Type: application/json" \
  -d '{"version_comment": "Updated content"}'

# Create archive
curl -X POST "http://localhost:8082/api/files/archive" \
  -H "Content-Type: application/json" \
  -d '{
    "file_ids": ["file-001", "file-002"],
    "archive_name": "client_documents",
    "compression_level": 6
  }'
```

## 🔧 Configuration

### Environment Variables
```bash
# Application Configuration
APP_PORT=8080
HUB_GATEWAY_URL=http://hub-gateway:8081

# Database Configuration
POSTGRES_URL=postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub

# Vector Database Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Cache Configuration
REDIS_URL=redis://redis:6379/0

# File Storage Configuration
FILE_STORAGE_PATH=/data/file_storage
MAX_FILE_SIZE=100

# Optional Configuration
ENABLE_COMPRESSION=true
LOG_LEVEL=INFO
```

### Docker Compose Services
- **contract-reviewer-v2-integrated**: Main application
- **postgresql**: Document metadata and analysis results
- **qdrant**: Vector storage for semantic search
- **redis**: Caching and session management

## 📊 Monitoring

### Health Checks
```bash
# Application health
curl http://localhost:8082/api/health

# Service statistics
curl http://localhost:8082/api/stats

# File storage health
curl http://localhost:8082/api/files/storage/health
```

### Logs
```bash
# View application logs
docker-compose logs -f contract-reviewer-v2-integrated

# View all service logs
docker-compose logs -f
```

## 🧪 Testing

### Run Tests
```bash
# Unit tests
python -m pytest test_integrated_app.py -v

# Integration tests
python -m pytest test_integrated_app.py::TestIntegratedWorkflow -v
```

### Test Single Document Workflow
```bash
# 1. Upload document
curl -X POST "http://localhost:8082/api/documents/upload" \
  -F "file=@test_contract.pdf" \
  -F "client_id=Test_Client"

# 2. Analyze document
curl -X POST "http://localhost:8082/api/analyze/doc-001" \
  -H "Content-Type: application/json" \
  -d '{"analysis_type": "comprehensive"}'

# 3. Search documents
curl -X POST "http://localhost:8082/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "confidentiality", "include_analysis": true}'
```

## 🔒 Security

### Authentication
- Role-based access control
- Session management with Redis
- API key authentication support

### Data Protection
- Encrypted file storage (optional)
- Secure database connections
- Audit logging for all operations

### Network Security
- Internal service communication
- Optional SSL/TLS termination
- Firewall configuration support

## 📈 Performance

### Optimization Features
- Redis caching for frequently accessed data
- Database connection pooling
- Vector search optimization
- File compression and archiving

### Scaling
- Horizontal scaling support
- Load balancer integration
- Database read replicas
- Redis clustering

## 🛠️ Development

### Local Development
```bash
# Install dependencies
pip install -r requirements_integrated.txt

# Run in development mode
python app_integrated.py

# Run with auto-reload
uvicorn app_integrated:app --host 0.0.0.0 --port 8080 --reload
```

### Code Structure
```
contract-reviewer-v2/
├── app_integrated.py              # Main integrated application
├── document_service.py            # PostgreSQL document service
├── vector_storage_service.py      # Qdrant vector service
├── document_processing_service.py # Document processing service
├── file_based_storage_service.py  # File storage service
├── report_generation_service.py   # Report generation service
├── file_management_api.py         # File management API
├── test_integrated_app.py         # Test suite
├── requirements_integrated.txt     # Dependencies
├── Dockerfile                     # Docker configuration
├── docker-compose.yml             # Service orchestration
├── deploy.sh                      # Linux deployment script
├── deploy.bat                     # Windows deployment script
├── postgres-init/                 # Database initialization
│   └── 01-init-integrated.sql
└── docs/                          # Documentation
    └── Integrated_Setup_Guide.md
```

## 🚨 Troubleshooting

### Common Issues

#### Service Connection Issues
```bash
# Check if services are running
docker-compose ps

# Check service logs
docker-compose logs postgresql
docker-compose logs qdrant
docker-compose logs redis
```

#### Database Issues
```bash
# Test PostgreSQL connection
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT 1;"

# Check database size
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT pg_size_pretty(pg_database_size('document_hub'));"
```

#### Vector Search Issues
```bash
# Check Qdrant status
curl http://localhost:6333/collections

# Check collection status
curl http://localhost:6333/collections/legal_documents
```

#### File Storage Issues
```bash
# Check file storage permissions
ls -la data/file_storage/

# Check disk space
df -h data/file_storage/
```

### Performance Issues
```bash
# Check memory usage
docker stats

# Check Redis memory
docker exec redis redis-cli info memory

# Check database performance
docker exec document-hub-postgres psql -U hub_user -d document_hub -c "SELECT * FROM pg_stat_activity;"
```

## 📚 Documentation

- [Integrated Setup Guide](docs/Integrated_Setup_Guide.md) - Complete setup and deployment guide
- [Phase 1: PostgreSQL Setup](docs/Phase_1_PostgreSQL_Setup_Guide.md) - PostgreSQL configuration
- [Phase 2: Vector Storage](docs/Phase_2_Vector_Storage_Guide.md) - Qdrant vector storage
- [Phase 3: File-Based Storage](docs/Phase_3_File_Based_Storage_Guide.md) - File storage system
- [API Documentation](http://localhost:8082/docs) - Interactive API documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section above
- Review the documentation
- Open an issue on GitHub
- Contact the development team

---

**Contract Reviewer v2 - Integrated** provides a complete, production-ready legal document analysis platform with comprehensive AI-powered analysis, semantic search, and professional report generation capabilities.
