# API Reference and Usage Scenarios

This document outlines the available REST APIs in the **ABS Hub Gateway** and provides common usage scenarios for developers and administrators.

**Base URL**: `http://localhost:8081`

---

## 1. API Reference

All endpoints are standardized under the `/v1` prefix.

### 🤖 LLM & Embeddings

Standard OpenAI-compatible endpoints for dropping into existing SDKs.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/v1/chat/completions` | Generate chat completions. Automatically routes to Ollama or vLLM. |
| `POST` | `/v1/embeddings` | Generate vector embeddings. Caches results in Redis. |
| `GET` | `/v1/models` | List available models (merged from Ollama and Registry). |

### 📦 Assets & Store

Manage the application catalog and installed assets.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/v1/catalog` | Get the full registry of available apps and policies. |
| `GET` | `/v1/assets` | List specific asset definitions. |
| `GET` | `/v1/store/apps` | List installable apps from the central store. |
| `POST` | `/v1/store/apps/{id}/install` | Trigger installation of a new app. |

### ⚙️ Admin & Operations

Control the Core services and monitor system health.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/v1/admin/system/metrics` | Real-time CPU, RAM, and GPU usage. |
| `GET` | `/v1/admin/settings` | View current Auto-Wake configuration. |
| `POST` | `/v1/admin/settings` | Update Auto-Wake settings (e.g., idle timeouts). |
| `POST` | `/v1/admin/services/{name}/control`| Start, Stop, or Restart a service (e.g., `ollama`, `redis`). |
| `POST` | `/v1/admin/services/{name}/idle-sleep`| Enable/Disable idle sleep for a specific service. |

### 🔍 Tri-Store Inspector

Debug data consistency across the stack.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/v1/inspector/{doc_id}` | Check consistency of a document across Postgres, Redis, and Qdrant. |

---

## 2. Usage Scenarios

### Scenario 1: Running a Contract Review

**Goal**: An app needs to analyze a contract using Llama 3, but the model is currently unloaded to save RAM.

1.  **App Request**:
    ```http
    POST /v1/chat/completions
    X-ABS-App-Id: contract-reviewer
    {
      "model": "llama3:8b",
      "messages": [{"role": "user", "content": "Analyze this NDA..."}]
    }
    ```
2.  **Gateway Action** (Auto-Wake):
    *   Detects `ollama` service is running but model is not loaded.
    *   (Optional) If `ollama` was stopped, Gateway starts the Docker container.
    *   Gateway holds the request while the model loads into VRAM.
3.  **App Response**:
    *   Receives standard JSON response once inference is complete.

### Scenario 2: Managing Idle Resources

**Goal**: Admin wants to ensure the specific `whisper` service stops after 30 minutes of inactivity to save power.

1.  **Check Status**:
    ```bash
    curl http://localhost:8081/v1/admin/idle-status
    ```
2.  **Configure Service**:
    ```bash
    curl -X POST http://localhost:8081/v1/admin/services/whisper-server/idle-sleep \
         -H "Content-Type: application/json" \
         -d '{"enabled": true}'
    ```
3.  **Outcome**: The `autowake` background task will now monitor `whisper-server` and stop the container if unused for the configured timeout.

### Scenario 3: Debugging "Missing Document" Issues

**Goal**: A user claims search isn't finding a document they just uploaded.

1.  **Inspect Document**:
    ```bash
    curl http://localhost:8081/v1/inspector/doc-12345
    ```
2.  **Response Analysis**:
    ```json
    {
      "consistency": {
        "postgres": "present",
        "redis": "missing",       <-- PROBLEM FOUND
        "qdrant": "present"
      }
    }
    ```
3.  **Resolution**: The admin sees that Redis (cache/queue) lost the document chunks, explaining the search failure despite the Vector DB having the embeddings.

### Scenario 4: Installing a New App

**Goal**: User wants to install the "Deposition Summarizer" from the local App Store.

1.  **List Apps**:
    ```bash
    curl http://localhost:8081/v1/store/apps?category=legal
    ```
2.  **Install**:
    ```bash
    curl -X POST http://localhost:8081/v1/store/apps/deposition-summarizer/install
    ```
3.  **Result**: The core services pull necessary configs, and the app becomes available in the `/v1/catalog`.
