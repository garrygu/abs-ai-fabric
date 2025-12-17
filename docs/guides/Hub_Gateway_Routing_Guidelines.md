# Hub Gateway Routing Guidelines

## Overview

The ABS Hub Gateway implements intelligent routing for Qdrant vector database operations based on embedding models. This ensures proper segregation of vector data and prevents conflicts between different applications using different embedding models.

## Core Concepts

### Collection Segregation Strategy
- **Per-Model Collections**: Each embedding model gets its own Qdrant collection
- **Automatic Routing**: Hub Gateway routes requests based on app configuration
- **Naming Convention**: Collections follow the pattern `{embed_model}_vectors`

### App Identification
- **Header-Based**: Uses `X-ABS-App-Id` header to identify the requesting application
- **Registry Lookup**: Maps app ID to embedding model configuration
- **Fallback Support**: Defaults to global configuration if app-specific config not found

## Routing Rules

### 1. Collection Management

#### Collection Creation
```
PUT /v1/collections/{collection_name}
```
- **Input**: Collection name (ignored, uses model-based naming)
- **App Header**: `X-ABS-App-Id: {app_name}`
- **Routing Logic**: 
  - Looks up app configuration in `registry.json`
  - Extracts `embed_model` from app config
  - Routes to `{embed_model}_vectors` collection
- **Qdrant Target**: `PUT /collections/{embed_model}_vectors`

#### Collection Information
```
GET /v1/collections/{collection_name}
```
- **Input**: Collection name (ignored, uses model-based naming)
- **App Header**: `X-ABS-App-Id: {app_name}`
- **Routing Logic**: Same as collection creation
- **Qdrant Target**: `GET /collections/{embed_model}_vectors`

### 2. Vector Operations

#### Point Upsert
```
PUT /v1/collections/{collection_name}/points
```
- **Input**: Points data with vectors and payloads
- **App Header**: `X-ABS-App-Id: {app_name}`
- **Routing Logic**: Routes to model-specific collection
- **Qdrant Target**: `PUT /collections/{embed_model}_vectors/points`

#### Point Search
```
POST /v1/collections/{collection_name}/points/search
```
- **Input**: Search query with vector and filters
- **App Header**: `X-ABS-App-Id: {app_name}`
- **Routing Logic**: Routes to model-specific collection
- **Qdrant Target**: `POST /collections/{embed_model}_vectors/points/search`

## Configuration

### Registry Structure
```json
{
  "defaults": {
    "embed_model": "bge-small-en-v1.5",
    "dim": 384
  },
  "apps": {
    "contract-reviewer": {
      "embed_model": "legal-bert",
      "dim": 768
    },
    "rag-pdf-voice": {
      "embed_model": "bge-small-en-v1.5",
      "dim": 384
    }
  }
}
```

### Collection Naming Examples
- **Contract Reviewer** (Legal-BERT) → `legal-bert_vectors`
- **RAG PDF Voice** (BGE Small) → `bge-small-en-v1.5_vectors`
- **Default App** (BGE Small) → `bge-small-en-v1.5_vectors`

## Implementation Details

### Hub Gateway Endpoints

#### Collection Creation
```python
@app.put("/v1/collections/{collection_name}")
async def create_collection(collection_name: str, payload: dict, 
                          app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    cfg = pick_app_cfg(app_id)
    embed_model = cfg.get("embed_model") or REG.get("defaults", {}).get("embed_model")
    model_collection = f"{embed_model}_vectors"
    
    r = await HTTP.put(f"http://qdrant:6333/collections/{model_collection}", json=payload)
    return r.json()
```

#### Collection Information
```python
@app.get("/v1/collections/{collection_name}")
async def get_collection_info(collection_name: str, 
                            app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    cfg = pick_app_cfg(app_id)
    embed_model = cfg.get("embed_model") or REG.get("defaults", {}).get("embed_model")
    model_collection = f"{embed_model}_vectors"
    
    r = await HTTP.get(f"http://qdrant:6333/collections/{model_collection}")
    return r.json()
```

#### Point Operations
```python
@app.put("/v1/collections/{collection_name}/points")
async def upsert_points(collection_name: str, payload: dict, 
                       app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    cfg = pick_app_cfg(app_id)
    embed_model = cfg.get("embed_model") or REG.get("defaults", {}).get("embed_model")
    model_collection = f"{embed_model}_vectors"
    
    r = await HTTP.put(f"http://qdrant:6333/collections/{model_collection}/points", json=payload)
    return r.json()

@app.post("/v1/collections/{collection_name}/points/search")
async def search_points(collection_name: str, payload: dict, 
                       app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    cfg = pick_app_cfg(app_id)
    embed_model = cfg.get("embed_model") or REG.get("defaults", {}).get("embed_model")
    model_collection = f"{embed_model}_vectors"
    
    r = await HTTP.post(f"http://qdrant:6333/collections/{model_collection}/points/search", json=payload)
    return r.json()
```

## Client Usage

### App Integration
Apps should use Hub Gateway instead of direct Qdrant access:

```python
# Instead of direct Qdrant access
# qdrant.upsert("my_collection", points=points)

# Use Hub Gateway routing
response = requests.put(
    f"{HUB_GATEWAY_URL}/v1/collections/my_collection/points",
    json={"points": points},
    headers={"X-ABS-App-Id": "my-app"}
)
```

### Required Headers
All requests must include the app identification header:
```python
headers = {"X-ABS-App-Id": "contract-reviewer"}
```

### Search Request Format
Include `with_payload: true` to retrieve payload data:
```python
payload = {
    "vector": query_vector,
    "limit": 10,
    "with_payload": True,
    "filter": {
        "must": [{"key": "doc_id", "match": {"value": doc_id}}]
    }
}
```

## Benefits

### 1. Conflict Prevention
- **Dimension Isolation**: Different embedding models can coexist
- **Data Separation**: Each app's vectors are isolated
- **No Interference**: Apps don't affect each other's data

### 2. Scalability
- **Easy Expansion**: Add new apps with different embedding models
- **Automatic Routing**: No manual collection management
- **Future-Proof**: Supports any embedding model configuration

### 3. Maintenance
- **Centralized Logic**: All routing logic in Hub Gateway
- **Consistent Behavior**: Uniform routing across all apps
- **Easy Debugging**: Centralized logging and error handling

## Error Handling

### Common Issues

#### 1. Missing App ID Header
```
Error: 500 - Error getting collection info: App ID not provided
```
**Solution**: Include `X-ABS-App-Id` header in all requests

#### 2. Unknown App Configuration
```
Error: 500 - Error getting collection info: App not found in registry
```
**Solution**: Add app configuration to `registry.json`

#### 3. Collection Not Found
```
Error: 404 - Collection `legal-bert_vectors` doesn't exist
```
**Solution**: Create collection via Hub Gateway or ensure app initialization

#### 4. Dimension Mismatch
```
Error: 400 - expected dim: 768, got 384
```
**Solution**: Verify embedding model configuration matches collection dimensions

### Debugging Tips

1. **Check Registry**: Verify app configuration in `registry.json`
2. **Verify Headers**: Ensure `X-ABS-App-Id` header is included
3. **Check Logs**: Review Hub Gateway logs for routing decisions
4. **Test Directly**: Test Qdrant endpoints directly for comparison

## Migration Guide

### From Direct Qdrant Access

#### Before (Direct Access)
```python
from qdrant_client import QdrantClient

qdrant = QdrantClient(url="http://qdrant:6333")
qdrant.upsert("my_collection", points=points)
results = qdrant.search("my_collection", query_vector=vector)
```

#### After (Hub Gateway Routing)
```python
import requests

# Upsert via Hub Gateway
response = requests.put(
    f"{HUB_GATEWAY_URL}/v1/collections/my_collection/points",
    json={"points": points},
    headers={"X-ABS-App-Id": "my-app"}
)

# Search via Hub Gateway
response = requests.post(
    f"{HUB_GATEWAY_URL}/v1/collections/my_collection/points/search",
    json={"vector": vector, "with_payload": True},
    headers={"X-ABS-App-Id": "my-app"}
)
```

### Collection Migration
1. **Update App Code**: Replace direct Qdrant calls with Hub Gateway calls
2. **Add Headers**: Include `X-ABS-App-Id` header in all requests
3. **Update Collection Names**: Use generic names (Hub Gateway handles routing)
4. **Test Integration**: Verify routing works correctly

## Best Practices

### 1. App Configuration
- **Unique App IDs**: Use descriptive, unique app identifiers
- **Consistent Naming**: Follow naming conventions for app IDs
- **Complete Config**: Include all required fields in registry

### 2. Request Headers
- **Always Include**: Never omit `X-ABS-App-Id` header
- **Consistent Values**: Use same app ID across all requests
- **Error Handling**: Handle missing header errors gracefully

### 3. Search Optimization
- **Include Payload**: Always use `with_payload: true` for text retrieval
- **Proper Filtering**: Use appropriate filters for data isolation
- **Limit Results**: Set reasonable limits to avoid large responses

### 4. Error Handling
- **Graceful Degradation**: Handle routing errors appropriately
- **Fallback Logic**: Implement fallback for critical operations
- **Logging**: Log routing decisions for debugging

## Future Enhancements

### Planned Features
1. **Collection Lifecycle Management**: Automatic cleanup of unused collections
2. **Performance Monitoring**: Metrics for routing performance
3. **Advanced Filtering**: Support for complex filter operations
4. **Batch Operations**: Optimized batch upsert and search operations

### Extension Points
1. **Custom Routing Logic**: Support for app-specific routing rules
2. **Multi-Model Support**: Apps using multiple embedding models
3. **Cross-App Queries**: Controlled access to other apps' collections
4. **Dynamic Configuration**: Runtime configuration updates

---

## Summary

The Hub Gateway routing system provides a robust, scalable solution for managing Qdrant collections in a multi-app environment. By implementing per-model collection segregation and automatic routing, it ensures data isolation while maintaining ease of use and future extensibility.

For questions or issues, refer to the Hub Gateway logs and this documentation for troubleshooting guidance.
