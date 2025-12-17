# Dataset Interface

Interface contract for dataset and data source access.

## Interface ID
`dataset`

## Version
`v1`

## Description
Provides access to datasets for RAG, training, and analysis workloads.

---

## Dataset Types

### RAG Dataset
Vectorized document collection for retrieval-augmented generation.

| Property | Description |
| :--- | :--- |
| `vector_db` | Vector database ID (e.g., qdrant) |
| `collection` | Collection name |
| `embedding_dim` | Vector dimension |
| `embed_model` | Embedding model used |

### File Dataset
Raw file collection.

| Property | Description |
| :--- | :--- |
| `path` | Storage path |
| `format` | File formats (pdf, txt, etc.) |

---

## Access Operations

| Operation | Description |
| :--- | :--- |
| `list` | List dataset contents |
| `get` | Retrieve specific item |
| `search` | Search within dataset |

---

## Policy
Datasets support scope-based access control:
```yaml
policy:
  scopes:
    - datasets.{id}.read
    - datasets.{id}.write
```

---

## Implementations
- `contracts-corpus` - Legal contracts vector collection
- `ndas-sample` - NDA sample files
