# Data Objects Storage Mapping

## Overview
This document specifies exactly what data objects are stored in each storage system within the hybrid architecture.

## 1. PostgreSQL Database (Structured Metadata)

### Documents Table
```sql
CREATE TABLE documents (
    document_id UUID PRIMARY KEY,           -- Unique document identifier
    filename VARCHAR(255) NOT NULL,        -- Original filename
    client_id VARCHAR(100),                 -- Client/customer identifier
    case_number VARCHAR(100),               -- Legal case reference
    matter_type VARCHAR(50),                -- Contract, NDA, Agreement, etc.
    upload_date TIMESTAMP DEFAULT NOW(),    -- When uploaded
    file_hash VARCHAR(64) UNIQUE,          -- SHA-256 hash for deduplication
    file_size BIGINT,                       -- File size in bytes
    file_type VARCHAR(10),                  -- PDF, DOCX, etc.
    analysis_status VARCHAR(20) DEFAULT 'pending', -- pending, analyzing, completed, failed
    created_by VARCHAR(100),               -- User who uploaded
    updated_at TIMESTAMP DEFAULT NOW()      -- Last modification time
);
```

### Analysis Results Table
```sql
CREATE TABLE analysis_results (
    analysis_id UUID PRIMARY KEY,           -- Unique analysis identifier
    document_id UUID REFERENCES documents(document_id), -- Link to document
    analysis_type VARCHAR(50),              -- comprehensive, quick, risk-focused
    analysis_data JSONB NOT NULL,          -- Complete analysis with citations
    model_used VARCHAR(100),               -- AI model used for analysis
    confidence_score FLOAT DEFAULT 0.0,    -- Analysis confidence (0.0-1.0)
    created_at TIMESTAMP DEFAULT NOW(),    -- Analysis completion time
    analyst_id VARCHAR(100),               -- User who requested analysis
    file_path TEXT,                        -- Path to complete analysis file
    status VARCHAR(20) DEFAULT 'completed', -- completed, failed, partial
    processing_time_seconds INTEGER,       -- How long analysis took
    tokens_used INTEGER,                   -- AI tokens consumed
    cost_usd DECIMAL(10,4)                -- Analysis cost
);
```

#### Enhanced Analysis Data Structure (JSONB)
The `analysis_data` field contains a comprehensive analysis with detailed citations:

```json
{
    "summary": {
        "summary": "Executive summary text",
        "document_type": "Contract|NDA|Agreement|etc",
        "key_points": [
            {
                "point": "Key point description",
                "citation": "Section 3.2, Clause 5.1",
                "importance": "high|medium|low",
                "text_excerpt": "Exact text from document"
            }
        ]
    },
    "risks": [
        {
            "level": "high|medium|low",
            "description": "Risk description",
            "section": "Relevant section or clause",
            "citation": "Specific text excerpt or reference",
            "impact": "Potential impact description",
            "text_excerpt": "Exact text from document"
        }
    ],
    "recommendations": [
        {
            "recommendation": "Specific recommendation",
            "rationale": "Why this recommendation is important",
            "citation": "Relevant section that supports this recommendation",
            "priority": "high|medium|low",
            "text_excerpt": "Supporting text from document"
        }
    ],
    "key_clauses": [
        {
            "clause": "Clause description",
            "type": "liability|termination|payment|confidentiality|etc",
            "citation": "Exact text or section reference",
            "significance": "Why this clause is important",
            "text_excerpt": "Full clause text"
        }
    ],
    "compliance": {
        "gdpr_compliant": true|false,
        "ccpa_compliant": true|false,
        "industry_standards": ["Standard 1", "Standard 2"],
        "compliance_issues": [
            {
                "issue": "Compliance issue description",
                "standard": "GDPR|CCPA|SOX|etc",
                "citation": "Specific section or clause",
                "severity": "high|medium|low",
                "text_excerpt": "Relevant text from document"
            }
        ]
    },
    "confidence_score": 0.85
}
```

#### Citation Standards
Each citation includes:
- **Section References**: "Section 3.2", "Clause 5.1", "Page 3"
- **Text Excerpts**: Exact quotes from the document
- **Location Data**: Specific paragraph or line references
- **Context**: Supporting rationale for each finding

### Document Chunks Table
```sql
CREATE TABLE document_chunks (
    chunk_id UUID PRIMARY KEY,             -- Unique chunk identifier
    document_id UUID REFERENCES documents(document_id),
    chunk_index INTEGER,                   -- Order within document
    chunk_text TEXT,                       -- Text content of chunk
    chunk_type VARCHAR(50),                -- paragraph, section, clause, etc.
    start_position INTEGER,               -- Character position in original
    end_position INTEGER,                 -- Character position in original
    word_count INTEGER,                   -- Number of words in chunk
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Users and Permissions
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255),
    role VARCHAR(50),                      -- admin, lawyer, analyst, viewer
    client_access TEXT[],                 -- Array of client IDs user can access
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    document_id UUID REFERENCES documents(document_id),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```

### Audit Logs
```sql
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(100),                  -- upload, analyze, view, delete, export
    document_id UUID REFERENCES documents(document_id),
    analysis_id UUID REFERENCES analysis_results(analysis_id),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    details JSONB                         -- Additional action details
);
```

## 2. Qdrant Vector Database (Semantic Search)

### Document Chunks Collection
```python
# Collection: "legal_document_chunks"
PointStruct(
    id=chunk_id,                          # UUID matching PostgreSQL chunk_id
    vector=embedding_vector,               # 768-dimensional embedding
    payload={
        "document_id": str(document_id),   # Link to PostgreSQL document
        "chunk_text": chunk_text,          # Text content for display
        "chunk_type": "clause",            # paragraph, section, clause, etc.
        "client_id": "ABC-Corp",          # Client identifier
        "case_number": "2024-001",        # Case reference
        "matter_type": "NDA",             # Document type
        "upload_date": "2024-01-15T10:30:00Z",
        "chunk_index": 5,                 # Order within document
        "word_count": 150,                # Word count for filtering
        "language": "en",                 # Document language
        "confidence": 0.95                # Chunk analysis confidence
    }
)
```

### Analysis Results Collection
```python
# Collection: "analysis_insights"
PointStruct(
    id=analysis_insight_id,               # UUID for insight
    vector=insight_embedding,              # Embedding of analysis insight
    payload={
        "analysis_id": str(analysis_id),   # Link to PostgreSQL analysis
        "document_id": str(document_id),   # Link to source document
        "insight_type": "risk",            # risk, recommendation, clause, summary
        "insight_text": "High liability risk in section 4.2",
        "severity": "high",               # low, medium, high
        "category": "liability",          # liability, payment, termination, etc.
        "client_id": "ABC-Corp",
        "created_at": "2024-01-15T10:30:00Z",
        "model_used": "gpt-4",
        "confidence": 0.87
    }
)
```

### Similar Documents Collection
```python
# Collection: "document_similarity"
PointStruct(
    id=similarity_id,                     # UUID for similarity record
    vector=document_embedding,             # Overall document embedding
    payload={
        "document_id": str(document_id),
        "document_title": "ABC Corp NDA Agreement",
        "client_id": "ABC-Corp",
        "matter_type": "NDA",
        "upload_date": "2024-01-15T10:30:00Z",
        "file_size": 125000,
        "word_count": 2500,
        "language": "en",
        "key_terms": ["confidentiality", "liability", "termination"],
        "similarity_score": 0.92           # Similarity to other documents
    }
)
```

## 3. File-Based Storage (Complete Analysis Results)

### Analysis Result Files
```json
// File: /legal-data/active/2024/01/15/ABC-Corp-NDA-analysis-a1b2c3d4.json
{
    "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "document_id": "doc-123-456-789",
    "analysis_metadata": {
        "created_at": "2024-01-15T10:30:00Z",
        "model_used": "gpt-4",
        "analysis_type": "comprehensive",
        "confidence_score": 0.85,
        "processing_time_seconds": 45,
        "tokens_used": 12500,
        "cost_usd": 0.125,
        "analyst_id": "lawyer-john-doe"
    },
    "document_info": {
        "filename": "ABC-Corp-NDA-Agreement.pdf",
        "client_id": "ABC-Corp",
        "case_number": "2024-001",
        "matter_type": "NDA",
        "file_size": 125000,
        "word_count": 2500
    },
    "summary": {
        "summary": "This NDA agreement between ABC Corp and XYZ Inc establishes mutual confidentiality obligations with potential liability exposure issues.",
        "document_type": "NDA",
        "key_points": [
            {
                "point": "Mutual confidentiality obligations established",
                "citation": "Section 2.1, Page 2",
                "importance": "high",
                "text_excerpt": "Each party agrees to maintain confidentiality of all proprietary information disclosed during the term of this agreement."
            },
            {
                "point": "Unlimited liability exposure for ABC Corp",
                "citation": "Section 4.2, Page 3",
                "importance": "high",
                "text_excerpt": "ABC Corp shall be liable for all damages arising from breach of confidentiality obligations without limitation."
            }
        ]
    },
    "risks": [
        {
            "level": "high",
            "description": "Unlimited liability exposure for ABC Corp",
            "section": "Section 4.2",
            "citation": "Section 4.2, Page 3",
            "impact": "Potential unlimited financial exposure",
            "text_excerpt": "ABC Corp shall be liable for all damages arising from breach of confidentiality obligations without limitation."
        }
    ],
    "recommendations": [
        {
            "recommendation": "Add liability cap of $100,000",
            "rationale": "Protects against unlimited financial exposure",
            "citation": "Section 4.2",
            "priority": "high",
            "text_excerpt": "Neither party's liability shall exceed $100,000 for any breach of confidentiality obligations."
        }
    ],
    "key_clauses": [
        {
            "clause": "Confidentiality Obligations",
            "type": "confidentiality",
            "citation": "Section 2.1, Page 2",
            "significance": "Core purpose of the agreement",
            "text_excerpt": "Each party agrees to maintain confidentiality of all proprietary information disclosed during the term of this agreement."
        }
    ],
    "compliance": {
        "gdpr_compliant": true,
        "ccpa_compliant": true,
        "industry_standards": ["ISO-27001"],
        "compliance_issues": [
            {
                "issue": "Missing data retention policy",
                "standard": "GDPR",
                "citation": "Article 5(1)(e) - data minimization principle",
                "severity": "medium",
                "text_excerpt": "Personal data shall be kept in a form which permits identification of data subjects for no longer than is necessary for the purposes for which the personal data are processed."
            }
        ]
    },
    "extracted_data": {
        "parties": [
            {
                "name": "ABC Corp",
                "type": "company",
                "address": "123 Business St, City, State",
                "role": "disclosing_party"
            }
        ],
        "dates": [
            {
                "type": "effective_date",
                "value": "2024-01-15",
                "location": "Section 1.1"
            }
        ],
        "monetary_amounts": [
            {
                "amount": 100000,
                "currency": "USD",
                "context": "liability cap",
                "location": "Section 4.2"
            }
        ]
    }
}
```

### Generated Reports
```
/legal-data/reports/
├── compliance/
│   ├── ABC-Corp-compliance-report-2024-01-15.pdf
│   └── XYZ-Inc-compliance-summary-2024-01-16.pdf
├── summaries/
│   ├── monthly-analysis-summary-2024-01.pdf
│   └── client-portfolio-analysis-ABC-Corp.pdf
└── exports/
    ├── client-deliverables/
    │   ├── ABC-Corp-analysis-package.zip
    │   └── XYZ-Inc-contract-review.zip
    └── court-submissions/
        ├── discovery-analysis-2024-001.pdf
        └── expert-report-contract-analysis.pdf
```

### Document Archives
```
/legal-data/archive/
├── 2023/
│   ├── Q1-analyses.zip
│   ├── Q2-analyses.zip
│   ├── Q3-analyses.zip
│   └── Q4-analyses.zip
├── 2022/
│   └── annual-archive.zip
└── backups/
    ├── daily-backup-2024-01-15.tar.gz
    └── weekly-backup-2024-01-14.tar.gz
```

## 4. Redis Cache (Primary Caching Layer)

### Session Data
```python
# Key: "session:{session_id}"
{
    "user_id": "user-123",
    "document_id": "doc-456",
    "analysis_id": "analysis-789",
    "created_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-15T12:30:00Z",
    "permissions": ["read", "analyze", "export"],
    "client_access": ["ABC-Corp", "XYZ-Inc"]
}
```

### Document Cache
```python
# Key: "document:{document_id}"
{
    "document_id": "doc-456",
    "filename": "ABC-Corp-NDA.pdf",
    "client_id": "ABC-Corp",
    "matter_type": "NDA",
    "upload_date": "2024-01-15T10:30:00Z",
    "processing_status": "completed",
    "analysis_status": "complete",
    "expires_at": "2024-01-15T11:30:00Z"  # 1 hour TTL
}
```

### Analysis Cache
```python
# Key: "analysis:{analysis_id}"
{
    "analysis_id": "analysis-789",
    "document_id": "doc-456",
    "app_name": "contract-reviewer",
    "analysis_type": "comprehensive",
    "confidence_score": 0.85,
    "created_at": "2024-01-15T10:30:00Z",
    "result_path": "/legal-data/active/2024/01/15/analysis-789.json",
    "expires_at": "2024-02-14T10:30:00Z"  # 30 days TTL
}
```

### Search Cache
```python
# Key: "search_cache:{query_hash}"
{
    "query": "liability clauses ABC Corp",
    "results": [
        {
            "document_id": "doc-123",
            "similarity_score": 0.92,
            "chunk_text": "ABC Corp shall be liable for...",
            "location": "Section 4.2"
        }
    ],
    "created_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-01-15T11:30:00Z"  # 1 hour
}
```

## Data Flow Between Storage Systems

### Document Upload Flow
1. **File Upload** → Store file in temporary location
2. **Extract Metadata** → Insert into PostgreSQL `documents` table
3. **Generate Hash** → Check for duplicates in PostgreSQL
4. **Extract Text** → Store chunks in PostgreSQL `document_chunks` table
5. **Generate Embeddings** → Store vectors in Qdrant
6. **Run Analysis** → Save complete results to file system
7. **Update Metadata** → Update PostgreSQL `analysis_results` table
8. **Cache Results** → Store in Redis for fast access

### Query Flow
1. **User Query** → Check Redis cache first
2. **Cache Hit** → Return cached data instantly
3. **Cache Miss** → Query PostgreSQL for document info
4. **Semantic Search** → Query Qdrant for similar content
5. **Full Analysis** → Load complete results from file system
6. **Combine Results** → Merge data from all sources
7. **Cache Results** → Store in Redis with appropriate TTL

## Data Retention Policies

### PostgreSQL
- **Active Data**: Permanent retention
- **Audit Logs**: 7 years minimum
- **User Sessions**: 30 days
- **Analysis Metadata**: Permanent

### Qdrant
- **Active Vectors**: Permanent retention
- **Search Cache**: 1 hour
- **Similarity Data**: Permanent

### File System
- **Active Analyses**: 2 years
- **Archived Analyses**: 7+ years (compressed)
- **Reports**: 5 years
- **Backups**: 1 year

### Redis (Primary Cache)
- **Document Cache**: 1 hour TTL
- **Analysis Cache**: 30 days TTL
- **Search Cache**: 10 minutes TTL
- **Session Data**: 2 hours TTL
- **User Permissions**: 30 minutes TTL
- **All Data**: Automatic expiry based on TTL

This mapping ensures each storage system is optimized for its specific use case while maintaining data consistency and compliance requirements.
