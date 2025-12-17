# Core Interfaces

This directory contains interface contract specifications for ABS AI Fabric.

Interfaces define the **required capabilities** that asset implementations must provide.
Apps bind to interfaces, not implementations — the Gateway resolves bindings at runtime.

---

## Interfaces

| Interface | Description | Implementations |
| :--- | :--- | :--- |
| [llm-runtime](./llm-runtime.md) | LLM inference (chat, embeddings) | ollama |
| [vector-store](./vector-store.md) | Vector database | qdrant |
| [cache-queue](./cache-queue.md) | Caching and message queues | redis |
| [metadata-store](./metadata-store.md) | Structured data storage | postgresql |
| [speech](./speech.md) | ASR/TTS audio processing | whisper-server |
| [tool](./tool.md) | Utility tools (OCR, parsing) | ocr-service, pdf-parser, etc. |
| [dataset](./dataset.md) | Data access | contracts-corpus, ndas-sample |

---

## Bindings

Bindings map interfaces to implementations. See [`core/bindings.yaml`](../core/bindings.yaml):

```yaml
core_bindings:
  llm-runtime: ollama
  vector-store: qdrant
  cache-queue: redis
```
