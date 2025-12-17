# Onyx Integration Guide & User Manual

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [User Interface Guide](#user-interface-guide)
7. [Integration Examples](#integration-examples)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## 🎯 Overview

Onyx is a powerful AI assistant framework integrated into the ABS AI Hub, providing:
- **Conversational AI Interface**: Natural language chat with multiple LLM models
- **RAG Capabilities**: Retrieval-Augmented Generation for document-based queries
- **Agent Management**: Create and manage custom AI agents for specific workflows
- **Document Ingestion**: Upload and process documents for knowledge base building
- **Multi-Model Support**: Works with Ollama, vLLM, and other inference engines

### Key Features
- ✅ Built-in chat UI accessible at `http://localhost:8000`
- ✅ RESTful API endpoints through Hub Gateway
- ✅ Auto-wake and service management
- ✅ Integration with Qdrant vector database
- ✅ Redis caching for performance
- ✅ Agent workflow automation

---

## 🏗 Architecture

### Service Dependencies
```
┌─────────────────┐
│   Hub Gateway   │
│   (Port 8081)    │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│      Onyx       │
│   (Port 8000)   │
└─────────┬───────┘
          │
    ┌─────┼─────┐
    ▼     ▼     ▼
┌──────┐ ┌────┐ ┌─────┐
│Ollama│ │Qdrant│ │Redis│
│11434 │ │6333 │ │6379 │
└──────┘ └────┘ └─────┘
```

### Data Flow
1. **User Input** → Hub Gateway (`/v1/onyx/*`)
2. **Gateway** → Onyx Service (auto-wake if needed)
3. **Onyx** → Inference Engine (Ollama/vLLM)
4. **Onyx** → Vector DB (Qdrant) for RAG
5. **Onyx** → Cache (Redis) for performance
6. **Response** → User Interface

---

## 🚀 Installation & Setup

### Prerequisites
- Docker Desktop with NVIDIA runtime
- ABS AI Hub Core Services running
- Ollama, Qdrant, and Redis services active

### Quick Start
```bash
# 1. Start Core Services (includes Onyx)
cd C:\ABS\core
.\start-core.ps1

# 2. Verify Onyx is running
docker ps | grep onyx

# 3. Access Onyx Chat UI
# Open browser to: http://localhost:8000
```

### Service Status Check
```bash
# Check Onyx container status
docker logs abs-onyx

# Check Onyx health
curl http://localhost:8000/health

# Check through Hub Gateway
curl http://localhost:8081/admin/services/status
```

---

## ⚙️ Configuration

### Environment Variables
Onyx is configured in `core/core.yml`:

```yaml
onyx:
  image: onyxai/onyx:latest
  container_name: abs-onyx
  environment:
    # Inference Engine Connections
    OLLAMA_BASE_URL: http://ollama:11434
    OPENAI_BASE_URL: http://vllm:8000/v1
    OPENAI_API_KEY: abs-local
    
    # Vector Database Connection
    QDRANT_URL: http://qdrant:6333
    QDRANT_API_KEY: ""
    
    # Cache Connection
    REDIS_URL: redis://redis:6379/0
    
    # Onyx Configuration
    ONYX_PORT: 8000
    ONYX_LOG_LEVEL: info
```

### Hub Gateway Integration
Onyx endpoints are available through the Hub Gateway:

```yaml
hub-gateway:
  environment:
    ONYX_BASE_URL: http://onyx:8000
  depends_on: [redis, onyx]
```

---

## 🔌 API Reference

### Base URLs
- **Direct Onyx**: `http://localhost:8000`
- **Via Hub Gateway**: `http://localhost:8081/v1/onyx`

### Authentication
All requests require the `X-ABS-App-Id` header:
```bash
curl -H "X-ABS-App-Id: your-app-name" \
     http://localhost:8081/v1/onyx/chat
```

### Endpoints

#### 1. Chat Interface
```bash
POST /v1/onyx/chat
```

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "What are the key terms in this contract?"}
  ],
  "model": "llama3.1:8b",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response:**
```json
{
  "id": "chatcmpl_onyx_123",
  "object": "chat.completion",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Based on the contract analysis..."
      }
    }
  ],
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350
  }
}
```

#### 2. RAG Queries
```bash
POST /v1/onyx/rag
```

**Request:**
```json
{
  "query": "Find all clauses related to liability",
  "collection": "contracts",
  "top_k": 5,
  "threshold": 0.7
}
```

**Response:**
```json
{
  "query": "Find all clauses related to liability",
  "results": [
    {
      "content": "The Company shall not be liable for...",
      "score": 0.89,
      "metadata": {
        "source": "contract.pdf",
        "page": 15,
        "section": "Liability"
      }
    }
  ],
  "total_results": 5
}
```

#### 3. Document Ingestion
```bash
POST /v1/onyx/ingest
```

**Request:**
```json
{
  "documents": [
    {
      "text": "Contract content here...",
      "metadata": {
        "source": "contract.pdf",
        "page": 1,
        "document_type": "contract"
      }
    }
  ],
  "collection": "contracts",
  "chunk_size": 512,
  "overlap": 50
}
```

**Response:**
```json
{
  "status": "success",
  "documents_processed": 1,
  "chunks_created": 15,
  "collection": "contracts"
}
```

#### 4. Agent Management
```bash
GET /v1/onyx/agents
POST /v1/onyx/agents/{agent_id}/execute
```

**List Agents Response:**
```json
{
  "agents": [
    {
      "id": "contract-reviewer",
      "name": "Contract Review Agent",
      "description": "Specialized contract analysis agent",
      "status": "active",
      "capabilities": ["analysis", "risk_assessment", "extraction"]
    }
  ]
}
```

---

## 🖥️ User Interface Guide

### Accessing Onyx Chat UI

#### Method 1: Through ABS AI Hub
1. Open `http://localhost:3000`
2. Click "🤖 Onyx AI Assistant" card
3. Click "Open Onyx Chat"

#### Method 2: Direct Access
1. Open `http://localhost:8000`
2. Start chatting immediately

### Chat Interface Features

#### 1. Basic Chat
- **Input**: Type your question or request
- **Send**: Click send button or press Enter
- **History**: Previous conversations are saved
- **Export**: Download conversation history

#### 2. Document Upload
- **Upload**: Drag & drop or click to upload files
- **Supported**: PDF, DOCX, TXT, MD files
- **Processing**: Automatic chunking and indexing
- **Status**: Real-time processing feedback

#### 3. Agent Selection
- **Available Agents**: Dropdown menu of configured agents
- **Custom Agents**: Create specialized workflows
- **Agent Settings**: Configure behavior and capabilities

#### 4. Advanced Features
- **Web Search**: Enable internet search for current information
- **Code Execution**: Run code snippets for calculations
- **File Analysis**: Deep analysis of uploaded documents
- **Multi-Modal**: Handle text, images, and documents

### UI Navigation

#### Main Chat Area
- **Message Input**: Text area for typing
- **Send Button**: Submit message
- **Attach Button**: Upload files
- **Settings**: Configure chat options

#### Sidebar
- **Conversation History**: Previous chats
- **Uploaded Documents**: Document library
- **Agent Management**: Available agents
- **Settings**: User preferences

#### Toolbar
- **New Chat**: Start fresh conversation
- **Export**: Download conversation
- **Share**: Share conversation link
- **Help**: Access documentation

---

## 💻 Integration Examples

### Python Integration

#### Basic Chat
```python
import httpx
import asyncio

async def chat_with_onyx(message: str, app_id: str = "my-app"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8081/v1/onyx/chat",
            headers={"X-ABS-App-Id": app_id},
            json={
                "messages": [{"role": "user", "content": message}],
                "model": "llama3.1:8b",
                "temperature": 0.7
            }
        )
        return response.json()

# Usage
result = asyncio.run(chat_with_onyx("Analyze this contract for risks"))
print(result["choices"][0]["message"]["content"])
```

#### RAG Query
```python
async def query_documents(query: str, collection: str = "contracts"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8081/v1/onyx/rag",
            headers={"X-ABS-App-Id": "document-analyzer"},
            json={
                "query": query,
                "collection": collection,
                "top_k": 5
            }
        )
        return response.json()

# Usage
results = asyncio.run(query_documents("liability clauses"))
for result in results["results"]:
    print(f"Score: {result['score']} - {result['content'][:100]}...")
```

#### Document Ingestion
```python
async def ingest_document(text: str, metadata: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8081/v1/onyx/ingest",
            headers={"X-ABS-App-Id": "document-processor"},
            json={
                "documents": [{"text": text, "metadata": metadata}],
                "collection": "contracts"
            }
        )
        return response.json()

# Usage
result = asyncio.run(ingest_document(
    "Contract terms and conditions...",
    {"source": "contract.pdf", "page": 1}
))
print(f"Processed {result['documents_processed']} documents")
```

### JavaScript/Node.js Integration

#### Basic Chat
```javascript
const axios = require('axios');

async function chatWithOnyx(message, appId = 'my-app') {
    try {
        const response = await axios.post(
            'http://localhost:8081/v1/onyx/chat',
            {
                messages: [{ role: 'user', content: message }],
                model: 'llama3.1:8b',
                temperature: 0.7
            },
            {
                headers: {
                    'X-ABS-App-Id': appId,
                    'Content-Type': 'application/json'
                }
            }
        );
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

// Usage
chatWithOnyx('What are the key risks in this contract?')
    .then(result => console.log(result.choices[0].message.content));
```

### Contract Reviewer Integration

#### Update Contract Reviewer App
```python
# In contract-reviewer/app.py
import httpx

async def query_onyx_for_analysis(contract_text: str):
    """Use Onyx for advanced contract analysis"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://hub-gateway:8081/v1/onyx/rag",
            headers={"X-ABS-App-Id": "contract-reviewer"},
            json={
                "query": f"Analyze this contract for risks: {contract_text[:1000]}",
                "collection": "contracts",
                "top_k": 10
            }
        )
        return response.json()

# Integration in your contract analysis workflow
async def enhanced_contract_analysis(document):
    # Your existing analysis
    basic_analysis = analyze_contract(document)
    
    # Enhanced analysis via Onyx
    onyx_insights = await query_onyx_for_analysis(document.text)
    
    # Combine results
    return {
        "basic_analysis": basic_analysis,
        "onyx_insights": onyx_insights,
        "recommendations": generate_recommendations(basic_analysis, onyx_insights)
    }
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Onyx Service Not Starting
**Symptoms**: Container fails to start or crashes
**Solutions**:
```bash
# Check container logs
docker logs abs-onyx

# Check service dependencies
docker ps | grep -E "(redis|qdrant|ollama)"

# Restart Onyx
docker restart abs-onyx

# Check resource usage
docker stats abs-onyx
```

#### 2. Connection Errors
**Symptoms**: "Connection refused" or timeout errors
**Solutions**:
```bash
# Verify Onyx is running
curl http://localhost:8000/health

# Check network connectivity
docker network ls | grep abs-net

# Test internal connectivity
docker exec abs-onyx curl http://ollama:11434/api/tags
```

#### 3. RAG Queries Failing
**Symptoms**: Empty results or errors in RAG queries
**Solutions**:
```bash
# Check Qdrant status
curl http://localhost:6333/collections

# Verify document ingestion
curl -H "X-ABS-App-Id: test" \
     http://localhost:8081/v1/onyx/rag \
     -d '{"query": "test", "collection": "contracts"}'

# Check embedding model
curl http://localhost:11434/api/tags
```

#### 4. Performance Issues
**Symptoms**: Slow responses or high memory usage
**Solutions**:
```bash
# Monitor resource usage
docker stats abs-onyx

# Check Redis cache
docker exec abs-redis redis-cli info memory

# Optimize model settings
# Reduce max_tokens or temperature in requests
```

### Debug Commands

#### Service Health Check
```bash
#!/bin/bash
echo "=== Onyx Service Health Check ==="
echo "1. Container Status:"
docker ps | grep onyx

echo "2. Service Health:"
curl -s http://localhost:8000/health | jq .

echo "3. Dependencies:"
echo "Ollama:" $(curl -s http://localhost:11434/api/tags | jq -r '.models[0].name // "Not available"')
echo "Qdrant:" $(curl -s http://localhost:6333/collections | jq -r '.collections | length')
echo "Redis:" $(docker exec abs-redis redis-cli ping)

echo "4. Gateway Integration:"
curl -s -H "X-ABS-App-Id: health-check" \
     http://localhost:8081/v1/onyx/agents | jq .
```

#### Log Analysis
```bash
# Real-time logs
docker logs -f abs-onyx

# Error logs only
docker logs abs-onyx 2>&1 | grep -i error

# Performance logs
docker logs abs-onyx 2>&1 | grep -i "slow\|timeout\|memory"
```

---

## 📚 Best Practices

### 1. Performance Optimization

#### Model Selection
- **For Chat**: Use smaller models (3B-7B parameters) for faster responses
- **For Analysis**: Use larger models (8B-13B parameters) for better accuracy
- **For RAG**: Use specialized embedding models for domain-specific tasks

#### Caching Strategy
```python
# Implement response caching
import redis
import json

redis_client = redis.from_url("redis://localhost:6379/0")

def cache_key(query: str, model: str) -> str:
    return f"onyx:cache:{hash(query)}:{model}"

async def cached_chat(query: str, model: str):
    cache_key = cache_key(query, model)
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Make API call
    result = await chat_with_onyx(query, model)
    
    # Cache for 1 hour
    redis_client.setex(cache_key, 3600, json.dumps(result))
    return result
```

### 2. Error Handling

#### Robust API Calls
```python
import httpx
import asyncio
from typing import Optional

async def robust_onyx_call(endpoint: str, payload: dict, 
                          max_retries: int = 3) -> Optional[dict]:
    """Make robust API calls with retry logic"""
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"http://localhost:8081/v1/onyx/{endpoint}",
                    headers={"X-ABS-App-Id": "robust-client"},
                    json=payload
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 503:
                    # Service unavailable, wait and retry
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise httpx.HTTPError(f"HTTP {response.status_code}")
                    
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            else:
                raise e
    
    return None
```

### 3. Security Considerations

#### API Key Management
```python
import os
from typing import Optional

class OnyxClient:
    def __init__(self, app_id: Optional[str] = None):
        self.app_id = app_id or os.getenv("ABS_APP_ID", "default-app")
        self.base_url = os.getenv("ONYX_BASE_URL", "http://localhost:8081/v1/onyx")
    
    async def chat(self, message: str, **kwargs):
        # Implementation with proper authentication
        pass
```

#### Input Validation
```python
def validate_chat_input(messages: list, model: str, temperature: float) -> bool:
    """Validate chat input parameters"""
    
    # Validate messages
    if not isinstance(messages, list) or len(messages) == 0:
        return False
    
    for msg in messages:
        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
            return False
        if msg["role"] not in ["user", "assistant", "system"]:
            return False
    
    # Validate model
    valid_models = ["llama3.1:8b", "llama3.1:7b", "llama3.2:3b"]
    if model not in valid_models:
        return False
    
    # Validate temperature
    if not 0.0 <= temperature <= 2.0:
        return False
    
    return True
```

### 4. Monitoring and Logging

#### Application Metrics
```python
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def monitor_onyx_calls(func):
    """Decorator to monitor Onyx API calls"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(f"Onyx call successful: {func.__name__}, "
                       f"duration: {duration:.2f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Onyx call failed: {func.__name__}, "
                        f"duration: {duration:.2f}s, error: {str(e)}")
            raise
    
    return wrapper

# Usage
@monitor_onyx_calls
async def chat_with_onyx(message: str):
    # Your implementation
    pass
```

### 5. Document Management

#### Efficient Document Ingestion
```python
async def batch_ingest_documents(documents: list, 
                                collection: str = "contracts",
                                batch_size: int = 10):
    """Ingest documents in batches for better performance"""
    
    results = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        
        try:
            result = await ingest_document_batch(batch, collection)
            results.append(result)
            
            # Small delay between batches
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Batch ingestion failed: {e}")
            # Continue with next batch
            continue
    
    return results
```

---

## 📞 Support & Resources

### Documentation Links
- **Onyx Official Docs**: https://docs.onyx.app
- **ABS AI Hub Docs**: `core/docs/`
- **API Reference**: This document

### Community & Support
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check this guide and inline help
- **Logs**: Always check container logs first

### Quick Reference

#### Service URLs
- **Onyx Chat UI**: http://localhost:8000
- **Hub Gateway**: http://localhost:8081
- **ABS AI Hub**: http://localhost:3000

#### Key Commands
```bash
# Start services
cd C:\ABS\core && .\start-core.ps1

# Check status
docker ps | grep onyx

# View logs
docker logs -f abs-onyx

# Health check
curl http://localhost:8000/health
```

---

*This guide is part of the ABS AI Hub documentation. For updates and additional resources, visit the core documentation directory.*
