# LLM Runtime Interface

**Interface ID:** `llm-runtime`  
**Version:** `v1`

---

## 1. Purpose

Defines the contract for any Large Language Model inference runtime. Implementations must provide chat completion and embedding capabilities via an OpenAI-compatible API.

---

## 2. Required Capabilities

| Capability | Description |
| :--- | :--- |
| `chat` | Text-to-text generation with message history. |
| `embeddings` | Convert text into vector representations. |
| `streaming` | (Optional) Server-sent events for streaming responses. |

---

## 3. Required Endpoints

All implementations MUST expose these endpoints (or the Gateway adapter MUST translate to them):

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/v1/chat/completions` | Generate chat response. |
| `POST` | `/v1/embeddings` | Generate embeddings. |
| `GET` | `/v1/models` | List available models. |

---

## 4. Metadata

Implementations MUST provide:

| Field | Type | Description |
| :--- | :--- | :--- |
| `model_id` | `string` | Unique identifier for the model. |
| `context_length` | `int` | Maximum context window in tokens. |
| `gpu_required` | `bool` | Whether GPU is needed for inference. |

---

## 5. Known Implementations

| Implementation | Notes |
| :--- | :--- |
| Ollama | Uses `/api/chat`, `/api/embeddings` natively. Adapter required. |
| vLLM | OpenAI-compatible natively. |
| OpenAI API | Cloud-based, OpenAI-compatible. |
