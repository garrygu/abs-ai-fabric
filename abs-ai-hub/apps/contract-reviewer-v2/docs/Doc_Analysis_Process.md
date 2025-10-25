Successful Analysis Process:
Document Upload: 📄 Uploading document: sample_purchase_agreement_test.docx
PostgreSQL Storage: ✅ Document created in PostgreSQL: 06df2a06-84f7-4e1f-96c5-7bb65235fba6
File Storage: ✅ File stored in file-based storage: db7f3f7d-b4a7-4cfa-9157-c016f02b4a4f
Vector Processing: 🔍 Processing document 06df2a06-84f7-4e1f-96c5-7bb65235fba6 for vector search...
Text Extraction: Extracting text from /data/file_storage/temp/upload_9c037cbc6cb6432bad379b156583ca82.docx
Chunking: Created 6 chunks from text
Embedding Generation: ✅ Generated 6 embeddings
Qdrant Storage: PUT http://abs-qdrant:6333/collections/legal_documents/points?wait=true "HTTP/1.1 200 OK"
Vector Storage: ✅ Stored 6 vectors for document 06df2a06-84f7-4e1f-96c5-7bb65235fba6


Analysis Process:
Analysis Start: 🔍 Analyzing document: 06df2a06-84f7-4e1f-96c5-7bb65235fba6
Analysis Storage: ✅ Analysis result stored in file system: efdd36fa-d006-4384-9e59-d62af53a20ce
Redis Caching: ✅ Analysis result cached in Redis: f722feab-6a0d-456e-9ca9-41ddf53c7b39
Re-processing: 🔍 Processing document 06df2a06-84f7-4e1f-96c5-7bb65235fba6 for vector search...
Status Update: ✅ Updated document status to 'analyzed' for 06df2a06-84f7-4e1f-96c5-7bb65235fba6

============
Based on the documentation and code analysis, here's the **exact data flow** when a document is uploaded and analyzed in Contract Reviewer v2:

## ✅ **You're Correct! Here's the Precise Flow:**

### **1. Document Upload Phase:**
1. **📄 File Upload** → Document uploaded via `/api/documents/upload`
2. **💾 File Storage** → Original document saved to **named volumes** (file system)
3. **🗄️ PostgreSQL** → Document metadata saved to `document_hub.documents` table
4. **⚡ Redis** → Document info cached for quick access (`document:{doc_id}`)

### **2. Vector Processing Phase:**
5. **🔍 Text Extraction** → Extract text from the uploaded document
6. **✂️ Chunking** → Split text into chunks (typically 6 chunks per document)
7. **🧠 Embedding Generation** → Generate vector embeddings using embedding model
8. **🗂️ Qdrant Storage** → Store chunks + embeddings in `legal_documents` collection

### **3. Analysis Phase:**
9. **🤖 LLM Analysis** → Use LLM model to analyze the document content
10. **📊 Analysis Results Storage** → Save analysis results to:
    - **💾 Named Volumes** → Complete analysis file (JSON/PDF)
    - **🗄️ PostgreSQL** → Analysis metadata in `analysis_results` table
    - **⚡ Redis** → Analysis cached (`analysis:{analysis_id}` + `document_analysis:{doc_id}` mapping)

### **4. Status Updates:**
11. **📝 Status Update** → Update document status to 'analyzed' in PostgreSQL

## **Key Storage Patterns:**

| **Storage System** | **What's Stored** | **Key Pattern** |
|-------------------|------------------|-----------------|
| **Named Volumes** | Original files + Analysis reports | File paths in PostgreSQL |
| **PostgreSQL** | Metadata + Analysis summaries | `document_hub.documents` + `analysis_results` |
| **Redis** | Cached data + Analysis results | `document:{doc_id}` + `analysis:{analysis_id}` |
| **Qdrant** | Text chunks + Embeddings | `legal_documents` collection with `document_id` in payload |

## **Redis Key Patterns:**
- `document:{doc_id}` → Document metadata cache
- `analysis:{analysis_id}` → Analysis results
- `document_analysis:{doc_id}` → Maps document to analysis ID

## **Qdrant Structure:**
- **Collection**: `legal_documents`
- **Point ID**: Random UUID per chunk
- **Payload**: Contains `document_id` to link back to original document
- **Vector**: 384-dimensional embeddings

The system uses this hybrid approach to optimize for different use cases:
- **PostgreSQL** for structured queries and relationships
- **Redis** for fast caching and real-time access
- **Qdrant** for semantic search and similarity
- **Named Volumes** for persistent file storage