# Tool Interface

Interface contract for utility tools (parsers, processors, etc.).

## Interface ID
`tool`

## Version
`v1`

## Description
Generic interface for utility tools that perform specific processing tasks.

---

## Tool Types

### OCR
| Operation | Method | Description |
| :--- | :--- | :--- |
| `ocr` | `POST /ocr` | Extract text from images |

### Parser
| Operation | Method | Description |
| :--- | :--- | :--- |
| `parse` | `POST /parse/{format}` | Parse document (pdf, docx, etc.) |

### Chunker
| Operation | Method | Description |
| :--- | :--- | :--- |
| `chunk` | `POST /chunk` | Split text into chunks |

### Reranker
| Operation | Method | Description |
| :--- | :--- | :--- |
| `rerank` | `POST /rerank` | Rerank search results |

---

## Common Request Format
```json
{
  "input": "base64_or_text",
  "options": {}
}
```

## Common Response Format
```json
{
  "result": "...",
  "metadata": {}
}
```

---

## Health Endpoint
`GET /health`

---

## Implementations
- `ocr-service` - Tesseract/PaddleOCR
- `pdf-parser` - PDF extraction
- `text-chunker` - Text splitting
- `bge-reranker` - BGE reranking model
