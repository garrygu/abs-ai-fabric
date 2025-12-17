# ABS AI Hub — Flexible Core Services and Auto-Wake Architecture

## 📌 Requirement

The **ABS AI Hub** must provide a clean and reliable runtime for legal AI workloads on our workstations.  
Key requirements from product and user experience:

1. **Core Services & Models Always Available by Default**  
   - Core services (Ollama, Qdrant, Redis, RAG/Agent engines like Onyx) and AI models should run by default after installation.  
   - Ensures legal professionals get an **out-of-box working environment** without setup.

2. **Admin Control for Resource Management**  
   - An **Admin Page** should allow users (IT staff, power users) to **manually enable/disable services and models**.  
   - Example: disable Qdrant if only using Onyx, or unload an LLM model to free VRAM.

3. **Auto-Wake on Demand**  
   - When a legal productivity app (e.g., Contract Reviewer, Due Diligence Assistant) requires a service or model that is disabled:  
     - The Hub Gateway **auto-starts the container** (service)  
     - **Auto-loads the required model** into memory/VRAM  
     - Waits for readiness before forwarding the request  
   - This ensures apps always work without manual intervention.

4. **Optional Idle Sleep**  
   - Services/models not used for a configurable period may automatically stop or unload to save resources.  
   - Example: Whisper server stops after 1 hour of no transcription jobs.

5. **User Feedback**  
   - If cold-start is triggered (e.g., loading Llama3-8b), the UI should notify the user:  
     *“Starting Contract Reviewer engine (~20–60s)...”*

---

## 🏗 Architecture Overview
+--------------------------------------------------------+
| ABS AI Hub UI |
| - Legal Apps: Contract Reviewer, Due Diligence, etc. |
| - Admin Page: Service/Model controls |
+--------------------------------------------------------+
| ↑
v |
+--------------------------------------------------------+
| Hub Gateway (Facade API) |
| - Stable API for Apps (/v1/ingest, /v1/answer, etc.) |
| - Provider Adapters (Onyx, Haystack, LlamaIndex, etc.)|
| - Orchestrator: Service Registry + Auto-Wake |
+--------------------------------------------------------+
| ↑
v |
+--------------------------------------------------------+
| Core Services (Dockerized) |
| - Ollama (LLM serving, models lazy-loaded) |
| - Qdrant (Vector DB, optional) |
| - Redis (Cache) |
| - RAG/Agent Engine (Onyx or alternatives) |
| - Whisper (ASR service, optional) |
+--------------------------------------------------------+
|
v
+--------------------------------------------------------+
| GPU + OS Runtime (Windows 10 Pro) |
| - Docker Desktop + WSL2 + NVIDIA runtime |
| - Secure workstation base (BitLocker, isolation) |
+--------------------------------------------------------+


## ⚙️ Implementation Details

### 1. Hub Gateway Orchestrator
- **Service Registry** tracks desired/actual state:
  ```json
  {
    "ollama": {"desired":"on","actual":"running"},
    "qdrant": {"desired":"off","actual":"stopped"},
    "onyx": {"desired":"on","actual":"running"}
  }


Auto-wake sequence:

App calls /v1/answer → needs Ollama + embeddings

Gateway checks registry → Ollama desired=off, actual=stopped

Gateway calls Docker API → docker start abs-ollama

Waits until container healthcheck passes → forwards request

If model not loaded → call Ollama /api/generate with a dummy prompt to pre-load into VRAM

Idle-sleep: background task checks last_used timestamp.
If >N minutes idle and desired=off → stop container or unload model.

2. Health Checks (Docker Compose)
ollama:
  image: ollama/ollama:latest
  healthcheck:
    test: ["CMD", "curl", "-fsS", "http://localhost:11434/api/tags"]
    interval: 10s
    timeout: 5s
    retries: 10
  restart: unless-stopped

3. Model Auto-Load (Ollama)

First inference request triggers cold-load from disk.

Use keep-alive options:

{"options":{"keep_alive":"2h"}}


Admin page provides “Warm Model” button to pre-load into VRAM.

4. Admin Page Features

Service Toggles (Ollama, Qdrant, Onyx, Whisper, Redis)

Model Management (Available, Loaded, Keep-alive time)

Force Stop/Start buttons

Idle Timeout Settings per service

5. User Experience

By default, everything is ON and working.

Advanced users/IT can disable unused services to free resources.

Apps always run successfully because Gateway can auto-start required components.

Cold-start latency is hidden with UI feedback.


✅ Benefits
Out-of-Box Simplicity: Everything works immediately for non-technical users.
Flexibility: Advanced teams can optimize resources (e.g., disable Qdrant if Onyx is used).
Future-Proof: Any RAG/Agent engine (Onyx, Haystack, LlamaIndex, custom) can plug in as a provider.
Security: Gateway ensures services are controlled, auditable, and sandboxed in containers.
Efficiency: Saves GPU memory by unloading models when idle.
