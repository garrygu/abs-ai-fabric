# ABS AI Hub — Admin API Reference

This document provides a comprehensive reference for the Hub Gateway's Admin APIs, which enable management of services, models, and data inspection.

---

## Table of Contents

1. [Service Management](#service-management)
2. [Model Management](#model-management)
3. [Auto-Wake & Idle Sleep](#auto-wake--idle-sleep)
4. [System Monitoring](#system-monitoring)
5. [Tri-Store Data Inspector](#tri-store-data-inspector)
6. [Asset Management](#asset-management)
7. [Registry Management](#registry-management)

---

## Service Management

### Discover Services
**GET** `/admin/services/discovery`

Discover all available services and their current status.

**Response:**
```json
{
  "discovered_services": {
    "ollama": {
      "name": "ollama",
      "container_name": "abs-ollama",
      "status": "running",
      "ports": "11434/tcp"
    },
    "qdrant": {
      "name": "qdrant", 
      "container_name": "abs-qdrant",
      "status": "running",
      "ports": "6333/tcp"
    }
  },
  "service_registry": {...},
  "timestamp": 1640995200.0
}
```

### Get Services Status
**GET** `/admin/services/status`

Get detailed status of all services including versions and metrics.

**Response:**
```json
{
  "ollama": {
    "status": "online",
    "models": ["llama3.2:3b", "bge-small-en-v1.5"],
    "running_models": ["llama3.2:3b"],
    "model_count": 2,
    "running_count": 1,
    "version": "0.1.0"
  },
  "qdrant": {
    "status": "online",
    "collections": ["legal_documents"],
    "collection_count": 1,
    "total_vectors": 150,
    "version": "1.7.0"
  }
}
```

### Control Service
**POST** `/admin/services/{service_name}/control`

Start, stop, or restart a service.

**Request Body:**
```json
{
  "action": "start"  // "start", "stop", or "restart"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Service ollama started successfully"
}
```

### Ensure Services Ready
**POST** `/admin/services/ensure-ready`

Ensure multiple services and their dependencies are running.

**Request Body:**
```json
["ollama", "qdrant", "redis"]
```

**Response:**
```json
{
  "status": "success",
  "message": "All required services are ready: ['ollama', 'qdrant', 'redis']",
  "resolved_services": ["redis", "qdrant", "ollama"]
}
```

### Get Service Dependencies
**GET** `/admin/services/dependencies`

Get service dependency information and startup order.

**Response:**
```json
{
  "dependencies": {
    "ollama": [],
    "qdrant": [],
    "redis": [],
    "hub-gateway": ["redis"],
    "onyx": ["redis", "qdrant"]
  },
  "startupOrder": ["redis", "qdrant", "ollama", "onyx", "hub-gateway"],
  "containerMap": {
    "ollama": "abs-ollama",
    "qdrant": "abs-qdrant",
    "redis": "abs-redis"
  }
}
```

---

## Model Management

### List Models
**GET** `/admin/models`

List all available models with their status, availability, and usage information.

**Query Parameters:**
- `app_id` (optional): Filter models by app policy

**Response:**
```json
{
  "models": [
    {
      "name": "llama3.2:3b",
      "type": "llm",
      "available": true,
      "running": true,
      "used_by": [
        {
          "id": "contract-reviewer-v2",
          "name": "Contract Reviewer v2",
          "type": "chat"
        }
      ],
      "is_default_chat": true,
      "is_default_embed": false,
      "aliases": {
        "ollama": "llama3.2:3b",
        "openai": "llama3.2:3b"
      },
      "status": "running",
      "allowed": true,
      "auto_unload_countdown": "1h 45m"
    }
  ],
  "summary": {
    "total": 5,
    "llm_models": 3,
    "embedding_models": 2,
    "running": 2,
    "available": 4,
    "unavailable": 1
  }
}
```

### Pull Model
**POST** `/admin/models/{model_name}/pull`

Pull a model from Ollama registry.

**Response:**
```json
{
  "status": "pulling",
  "model": "llama3.2:3b"
}
```

### Load Model
**POST** `/admin/models/{model_name}/load`

Load a model into VRAM (for LLMs) or warm it up (for embeddings).

**Response:**
```json
{
  "status": "loaded",
  "model": "llama3.2:3b"
}
```

### Unload Model
**POST** `/admin/models/{model_name}/unload`

Force unload a model from memory.

**Response:**
```json
{
  "status": "unloaded",
  "model": "llama3.2:3b"
}
```

### Delete Model
**DELETE** `/admin/models/{model_name}`

Delete a model from Ollama storage.

**Response:**
```json
{
  "status": "deleted",
  "model": "llama3.2:3b"
}
```

---

## Auto-Wake & Idle Sleep

### Get Settings
**GET** `/admin/settings`

Get current auto-wake and idle sleep settings.

**Response:**
```json
{
  "autoWakeEnabled": true,
  "idleTimeout": 60,
  "modelKeepAlive": 2,
  "idleSleepEnabled": true,
  "idleCheckInterval": 5,
  "serviceRegistry": {...},
  "modelRegistry": {...},
  "serviceDependencies": {...},
  "startupOrder": [...]
}
```

### Update Settings
**POST** `/admin/settings`

Update auto-wake and idle sleep settings.

**Request Body:**
```json
{
  "autoWakeEnabled": true,
  "idleTimeout": 90,
  "modelKeepAlive": 3,
  "idleSleepEnabled": true,
  "idleCheckInterval": 10
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Settings updated successfully"
}
```

### Toggle Service Idle Sleep
**POST** `/admin/services/{service_name}/idle-sleep`

Enable or disable idle sleep for a specific service.

**Request Body:**
```json
{
  "enabled": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Idle sleep enabled for ollama",
  "service": "ollama",
  "idle_sleep_enabled": true
}
```

### Get Idle Status
**GET** `/admin/idle-status`

Get current idle status of all services and models.

**Response:**
```json
{
  "idle_sleep_enabled": true,
  "idle_timeout_minutes": 60,
  "model_keep_alive_hours": 2,
  "services": {
    "ollama": {
      "last_used": 1640995200.0,
      "idle_for_minutes": 15.5,
      "idle_sleep_enabled": true,
      "desired": "on",
      "actual": "running",
      "will_sleep_in_minutes": 44.5
    }
  },
  "models": {
    "llama3.2:3b": {
      "last_used": 1640995200.0,
      "keep_alive_until": 1641002400.0,
      "will_unload_in_minutes": 120.0,
      "provider": "ollama"
    }
  },
  "monitor_task_running": true
}
```

---

## System Monitoring

### Get System Metrics
**GET** `/admin/system/metrics`

Get real-time system metrics including CPU, memory, disk, network, and GPU.

**Response:**
```json
{
  "cpu": {
    "usage_percent": 25.5,
    "cores": 8
  },
  "memory": {
    "total": 17179869184,
    "available": 8589934592,
    "used": 8589934592,
    "usage_percent": 50.0
  },
  "disk": {
    "total": 1000000000000,
    "used": 500000000000,
    "free": 500000000000,
    "usage_percent": 50.0
  },
  "network": {
    "bytes_sent": 1000000,
    "bytes_recv": 2000000,
    "packets_sent": 1000,
    "packets_recv": 2000
  },
  "gpu": [
    {
      "id": 0,
      "name": "NVIDIA GeForce RTX 4090",
      "utilization": 75,
      "memory_utilization": 60,
      "memory_total": 24576000000,
      "memory_used": 14745600000,
      "memory_free": 9830400000,
      "temperature": 65,
      "power_usage": 300.5
    }
  ],
  "timestamp": 1640995200.0
}
```

### Get Service Logs
**GET** `/admin/logs/{service_name}`

Get logs for a specific service.

**Query Parameters:**
- `lines` (optional): Number of lines to retrieve (default: 100)

**Response:**
```json
{
  "service": "ollama",
  "logs": "2024-01-01T12:00:00Z [INFO] Starting Ollama server...\n2024-01-01T12:00:01Z [INFO] Server ready on port 11434"
}
```

### PostgreSQL Health Check
**GET** `/api/health/postgresql`

Check PostgreSQL service health and connectivity.

**Response:**
```json
{
  "status": "healthy",
  "service": "postgresql",
  "container_status": "Up 2 hours",
  "database_connectivity": "ok"
}
```

### PostgreSQL Metrics
**GET** `/api/metrics/postgresql`

Get PostgreSQL performance metrics.

**Response:**
```json
{
  "container": {
    "cpu_percent": "5.2%",
    "memory_usage": "256MB",
    "memory_percent": "12.5%",
    "network_io": "1.2MB / 0.8MB",
    "block_io": "512KB / 256KB"
  },
  "database": {
    "database_size": "125 MB",
    "active_connections": 3,
    "table_statistics": [
      {
        "schema": "document_hub",
        "table": "documents",
        "inserts": 150,
        "updates": 25,
        "deletes": 5
      }
    ],
    "uptime_since": "2024-01-01T10:00:00Z"
  },
  "timestamp": 1640995200.0
}
```

---

## Tri-Store Data Inspector

### Inspect Document
**GET** `/admin/inspector/{doc_id}`

Inspect a document across all three stores (PostgreSQL, Redis, Qdrant).

**Query Parameters:**
- `env` (optional): Environment (default: "prod")

**Response:**
```json
{
  "doc_id": "0901f9d9-ea66-4ca4-a3c3-122d83e5e909",
  "requested_at": "2024-01-01T12:00:00Z",
  "env": "prod",
  "postgres": {
    "found": true,
    "store_type": "postgres",
    "key": "0901f9d9-ea66-4ca4-a3c3-122d83e5e909",
    "payload": {
      "id": "0901f9d9-ea66-4ca4-a3c3-122d83e5e909",
      "filename": "contract.docx",
      "file_size": 50000,
      "status": "analyzed"
    },
    "checksum": "f768baa3ced593d6",
    "updated_at": "2024-01-01T11:30:00Z"
  },
  "redis": {
    "found": true,
    "store_type": "redis",
    "key": "analysis:abc123",
    "payload": {...},
    "checksum": "f768baa3ced593d6",
    "ttl_seconds": 3600,
    "updated_at": "2024-01-01T11:30:00Z"
  },
  "qdrant": {
    "found": true,
    "store_type": "qdrant",
    "key": "0901f9d9-ea66-4ca4-a3c3-122d83e5e909",
    "payload": {
      "document_id": "0901f9d9-ea66-4ca4-a3c3-122d83e5e909",
      "chunks": [...],
      "total_chunks": 5
    },
    "checksum": "f768baa3ced593d6",
    "updated_at": "2024-01-01T11:30:00Z"
  },
  "consistency": {
    "status": "OK",
    "problems": [],
    "field_diff": [],
    "found_stores": ["postgres", "redis", "qdrant"],
    "checksums": {
      "postgres": "f768baa3ced593d6",
      "redis": "f768baa3ced593d6",
      "qdrant": "f768baa3ced593d6"
    }
  }
}
```

### Get Document Diff
**GET** `/admin/inspector/diff/{doc_id}`

Get only the consistency analysis for a document.

**Response:**
```json
{
  "status": "WARNING",
  "problems": [
    {
      "code": "MISSING_STORES",
      "message": "Document missing from: redis, qdrant",
      "severity": "WARNING"
    }
  ],
  "field_diff": [
    {
      "field": "updated_at",
      "values": {
        "postgres": "2024-01-01T11:30:00Z",
        "redis": null,
        "qdrant": null
      }
    }
  ],
  "found_stores": ["postgres"],
  "checksums": {
    "postgres": "f768baa3ced593d6"
  }
}
```

### Batch Inspect Documents
**POST** `/admin/inspector/batch`

Inspect multiple documents in batch.

**Request Body:**
```json
{
  "doc_ids": [
    "0901f9d9-ea66-4ca4-a3c3-122d83e5e909",
    "06df2a06-84f7-4e1f-96c5-7bb65235fba6"
  ],
  "env": "prod"
}
```

**Response:**
```json
{
  "results": [
    {
      "doc_id": "0901f9d9-ea66-4ca4-a3c3-122d83e5e909",
      "consistency": {...}
    },
    {
      "doc_id": "06df2a06-84f7-4e1f-96c5-7bb65235fba6",
      "consistency": {...}
    }
  ],
  "total": 2
}
```

### Inspector Health Check
**GET** `/admin/inspector/health`

Health check for all data stores.

**Response:**
```json
{
  "postgres": {
    "status": "healthy",
    "error": null
  },
  "redis": {
    "status": "healthy",
    "error": null
  },
  "qdrant": {
    "status": "healthy",
    "error": null
  }
}
```

### Analyze Vector Neighborhood
**GET** `/admin/inspector/vectors/{doc_id}`

Analyze vector neighborhood for a document.

**Query Parameters:**
- `limit` (optional): Number of neighbors to analyze (default: 5, max: 20)
- `env` (optional): Environment (default: "prod")

**Response:**
```json
{
  "doc_id": "0901f9d9-ea66-4ca4-a3c3-122d83e5e909",
  "vector_dimensions": 384,
  "neighbors": [
    {
      "id": "neighbor-doc-1",
      "score": 0.95,
      "payload": {...},
      "stores": {
        "qdrant": true,
        "postgres": true,
        "redis": false
      }
    }
  ],
  "analysis": {
    "total_neighbors_found": 10,
    "neighbors_in_all_stores": 3,
    "neighbors_missing_from_stores": 7
  }
}
```

### Export Document Inspection
**GET** `/admin/inspector/export/{doc_id}`

Export document inspection results in JSON or CSV format.

**Query Parameters:**
- `format`: Export format ("json" or "csv", default: "json")
- `env` (optional): Environment (default: "prod")

**Response:** File download with appropriate Content-Type header.

### Export Batch Inspection
**POST** `/admin/inspector/export/batch`

Export batch inspection results.

**Request Body:**
```json
{
  "doc_ids": ["doc1", "doc2"],
  "env": "prod"
}
```

**Query Parameters:**
- `format`: Export format ("json" or "csv", default: "json")

**Response:** File download with appropriate Content-Type header.

---

## Asset Management

### List Assets
**GET** `/assets`

List all assets from the unified catalog.

**Response:**
```json
[
  {
    "id": "contract-reviewer-v2",
    "class": "app",
    "name": "Contract Reviewer v2",
    "version": "2.0.0",
    "owner": null,
    "lifecycle": {
      "desired": "running",
      "actual": "running"
    },
    "policy": {...},
    "health": {...},
    "metadata": {...}
  }
]
```

### Get Asset
**GET** `/assets/{asset_id}`

Get specific asset information.

**Response:**
```json
{
  "id": "contract-reviewer-v2",
  "class": "app",
  "name": "Contract Reviewer v2",
  "version": "2.0.0",
  "owner": null,
  "lifecycle": {
    "desired": "running",
    "actual": "running"
  },
  "policy": {...},
  "health": {...},
  "metadata": {...}
}
```

### Create Asset
**POST** `/admin/assets`

Add a new asset to the catalog.

**Request Body:**
```json
{
  "id": "new-app",
  "class": "app",
  "name": "New Application",
  "version": "1.0.0",
  "policy": {
    "allowed_models": ["llama3.2:3b"],
    "allowed_embeddings": ["bge-small-en-v1.5"]
  },
  "metadata": {
    "description": "A new application",
    "category": "general"
  }
}
```

**Response:**
```json
{
  "status": "created",
  "asset": {...}
}
```

### Update Asset
**PUT** `/admin/assets/{asset_id}`

Update an existing asset in the catalog.

**Request Body:**
```json
{
  "name": "Updated Application Name",
  "policy": {
    "allowed_models": ["llama3.2:3b", "llama3:8b"]
  }
}
```

**Response:**
```json
{
  "status": "updated",
  "asset": {...}
}
```

### Delete Asset
**DELETE** `/admin/assets/{asset_id}`

Delete an asset from the catalog.

**Response:**
```json
{
  "status": "deleted",
  "asset": {...}
}
```

### Set Asset Lifecycle
**POST** `/admin/assets/{asset_id}/lifecycle`

Set desired lifecycle state for an asset.

**Request Body:**
```json
{
  "desired": "running"  // "running", "stopped", or "paused"
}
```

**Response:**
```json
{
  "status": "updated",
  "asset": {...}
}
```

---

## Registry Management

### Get Config Paths
**GET** `/admin/config/paths`

Expose effective file paths used by the gateway for troubleshooting mounts.

**Response:**
```json
{
  "REGISTRY_PATH": "/app/registry.json",
  "CATALOG_PATH": "/app/catalog.json",
  "APPS_REGISTRY_PATH": "/app/../abs-ai-hub/apps-registry.json"
}
```

### Flush Registry
**POST** `/admin/registry/flush`

Force-write the in-memory registry to file.

**Request Body:**
```json
{
  "defaults": {...},
  "apps": {...},
  "aliases": {...}
}
```

**Response:**
```json
{
  "status": "ok",
  "path": "/app/registry.json",
  "size": 1024
}
```

### Upsert Registry Alias
**POST** `/admin/registry/alias`

Upsert a logical alias mapping.

**Request Body:**
```json
{
  "id": "llama4:scout",
  "providers": {
    "ollama": "llama4:scout",
    "openai": "llama4:scout"
  }
}
```

**Response:**
```json
{
  "status": "upserted",
  "id": "llama4:scout",
  "providers": {
    "ollama": "llama4:scout",
    "openai": "llama4:scout"
  }
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Service unavailable and auto-wake failed"
}
```

---

## Authentication & Authorization

Currently, the Admin APIs do not require authentication. In production environments, consider implementing:

- API key authentication
- JWT token validation
- Role-based access control (RBAC)
- Rate limiting per client

---

## Rate Limiting

No rate limiting is currently implemented. Consider adding:

- Per-IP rate limits
- Per-endpoint rate limits
- Burst protection
- Redis-based token bucket implementation
