# Cache Queue Interface

Interface contract for cache and message queue services.

## Interface ID
`cache-queue`

## Version
`v1`

## Description
Provides caching, key-value storage, and pub/sub messaging capabilities.

---

## Required Capabilities

### Cache Operations
| Operation | Method | Description |
| :--- | :--- | :--- |
| `get` | `GET /cache/{key}` | Retrieve cached value |
| `set` | `PUT /cache/{key}` | Store value with optional TTL |
| `delete` | `DELETE /cache/{key}` | Remove cached key |
| `exists` | `HEAD /cache/{key}` | Check if key exists |

### Hash Operations
| Operation | Method | Description |
| :--- | :--- | :--- |
| `hget` | `GET /hash/{name}/{key}` | Get hash field |
| `hset` | `PUT /hash/{name}/{key}` | Set hash field |
| `hgetall` | `GET /hash/{name}` | Get all hash fields |

### Queue Operations
| Operation | Method | Description |
| :--- | :--- | :--- |
| `push` | `POST /queue/{name}` | Push to queue |
| `pop` | `DELETE /queue/{name}` | Pop from queue |
| `length` | `GET /queue/{name}/length` | Get queue length |

### Pub/Sub
| Operation | Method | Description |
| :--- | :--- | :--- |
| `publish` | `POST /pubsub/{channel}` | Publish message |
| `subscribe` | `WS /pubsub/{channel}` | Subscribe to channel |

---

## Health Endpoint
`GET /health` or `PING`

---

## Implementations
- `redis` - Redis server (default)
