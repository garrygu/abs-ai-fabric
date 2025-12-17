# Vector Store Interface

**Interface ID:** `vector-store`  
**Version:** `v1`

---

## 1. Purpose

Defines the contract for vector databases used for semantic search and retrieval.

---

## 2. Required Capabilities

| Capability | Description |
| :--- | :--- |
| `upsert` | Insert or update vectors with payloads. |
| `search` | KNN search with optional filters. |
| `delete` | Remove vectors by ID or filter. |
| `collections` | Manage named collections of vectors. |

---

## 3. Required Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/collections` | List all collections. |
| `PUT` | `/collections/{name}` | Create a collection. |
| `POST` | `/collections/{name}/points` | Upsert vectors. |
| `POST` | `/collections/{name}/points/search` | Search vectors. |

---

## 4. Known Implementations

| Implementation | Notes |
| :--- | :--- |
| Qdrant | Native REST API matches this interface. |
| Milvus | Requires adapter for REST compatibility. |
