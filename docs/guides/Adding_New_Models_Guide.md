# ABS AI Hub - Adding New Models Guide

## Overview

This guide provides step-by-step instructions for adding new LLM models to the ABS AI Hub architecture. The hub uses a centralized model registry system with policy enforcement, provider abstraction, and auto-wake capabilities.

## Architecture Components

### Core Components
- **Hub Gateway** (`c:\ABS\core\gateway\`): Central API gateway with model routing and policy enforcement
- **Model Registry** (`registry.json`): Provider-specific model aliases and mappings
- **Asset Catalog** (`catalog.json`): App-specific model policies and configurations
- **Core Services**: Ollama (LLM serving), Qdrant (vector DB), Redis (cache)

### Key Features
- **Provider Abstraction**: Apps don't need to know which backend (Ollama/vLLM/HuggingFace) is active
- **Policy Enforcement**: Per-app model restrictions and access control
- **Auto-Wake System**: Services start/stop based on demand
- **Model Lifecycle Management**: Automatic model loading/unloading

## Step-by-Step Process

### 1. Model Research & Preparation

#### 1.1 Verify Model Availability
```bash
# Check Ollama registry
ollama list | grep <model-name>
# Or visit: https://ollama.ai/library

# Check HuggingFace Hub
# Visit: https://huggingface.co/models
```

#### 1.2 Resource Requirements Assessment
- **Model Size**: Parameters count and file size
- **Memory Requirements**: VRAM needed (FP16/FP32)
- **Quantization Options**: 4-bit, 8-bit options for memory efficiency
- **Hardware Compatibility**: GPU requirements

#### 1.3 Provider Selection
Choose the appropriate provider based on your needs:

| Provider | Best For | Pros | Cons |
|----------|----------|------|------|
| **Ollama** | Local deployment, offline use | Simple setup, auto-pull, good performance | Limited to supported models |
| **HuggingFace** | Latest models, research | Wide model selection, easy access | Requires API key, network dependency |
| **vLLM** | High-performance serving | Fast inference, OpenAI-compatible | Complex setup, resource intensive |

### 2. Update Model Registry

#### 2.0 Registry Data Structure and Resolution

The registry (`c:\ABS\core\gateway\registry.json`) exposes a single top-level object `aliases`.

- Key: the logical model ID you use everywhere in policies and API requests (e.g., `"llama4-scout"` or `"llama3.2:7b"`). This is the stable, provider-agnostic name.
- Value: a map of provider → provider-specific model identifier.
  - `"ollama"`: the exact Ollama model tag (e.g., `"llama4:scout"`).
  - `"openai"`: an OpenAI/vLLM-compatible model name (e.g., `"llama4-scout"`).
  - `"huggingface"`: a Hugging Face repo id (e.g., `"meta-llama/Llama-4-Scout-17B-Instruct"`).

Example:

```json
{
  "aliases": {
    "llama4-scout": {
      "ollama": "llama4:scout",
      "openai": "llama4-scout",
      "huggingface": "meta-llama/Llama-4-Scout-17B-Instruct"
    }
  }
}
```

Resolution at runtime:
- Apps pass a logical ID in `model` (or via policy defaults).
- The Hub Gateway selects a provider (explicit or `provider: "auto"`).
- The gateway looks up `aliases[logicalId][provider]` and forwards the request with that provider-specific identifier.

Naming guidance:
- Choose one logical ID format (dash or colon) and use it consistently in `catalog.json` and UI.
- Prefer including size/variant (e.g., `-7b`, `-70b`, `-instruct`) when relevant.

Auto-update behavior (no manual edit required):
- When you create, update, or delete a Model asset via Admin → Add Asset (or the `POST/PUT/DELETE /admin/assets` APIs), the gateway now keeps `registry.json` in sync:
  - Create/Update (class = `model`): writes or updates `aliases[logicalId]`.
  - Delete (class = `model`): removes the alias.
  - If `metadata.providers` is supplied on the asset, it is used verbatim. Otherwise a minimal mapping is derived (defaults to `{"ollama": logicalId}`) so the model appears in the catalog immediately.
- The unified catalog (`GET /catalog`) uses the in-memory registry; changes appear right after a successful save.

Tip for UI-driven adds:
- In the Add Asset form, set Class = `Model` and optionally provide `metadata.providers` as a JSON object, for example:

```json
{
  "providers": { "ollama": "llama4:scout", "openai": "llama4-scout" }
}
```

This ensures the model is routable across providers without any manual registry edits.

Edit `c:\ABS\core\gateway\registry.json`:

```json
{
  "aliases": {
    "llama3-8b-instruct": { "openai": "llama3-8b-instruct", "ollama": "llama3:8b-instruct-q4_K_M" },
    "llama3.2:3b": { "openai": "llama3.2:3b", "ollama": "llama3.2:3b" },
    "llama3.2:7b": { "openai": "llama3.2:7b", "ollama": "llama3.2:7b" },
    "llama3.2:latest": { "openai": "llama3.2:latest", "ollama": "llama3.2:latest" },
    
    // Add your new model here
    "your-new-model": { 
      "openai": "your-new-model-openai-name", 
      "ollama": "your-new-model:ollama-tag",
      "huggingface": "organization/model-name" 
    },
    
    "bge-small-en-v1.5": { "openai": "bge-small-en-v1.5", "ollama": "bge-small" },
    "all-minilm": { "openai": "all-minilm", "ollama": "all-minilm" },
    "legal-bert": { "openai": "legal-bert", "ollama": "legal-bert", "huggingface": "nlpaueb/legal-bert-base-uncased" }
  }
}
```

**Registry Entry Format:**
- **Logical Name**: The name apps will use (e.g., `"your-new-model"`)
- **Provider Mappings**: How each provider identifies the model
- **Consistent Naming**: Use descriptive, version-specific names

### 2.1 Model status verification (pulled vs not) and pull flow

**How “pulled” is verified**

- **Source of truth:** Ollama’s `GET /api/tags` lists only models that are **pulled** (downloaded) on the host.
- **Gateway:** The Hub Gateway exposes this via:
  - `GET /v1/models` — returns each model with `status`: `"running"` (loaded in memory), `"available"` (pulled, in api/tags), or `"unavailable"` (in catalog/registry but not in api/tags).
  - `GET /v1/admin/models/list` — returns the raw Ollama `api/tags` list (pulled models only).
- **Admin > Models:** The Admin Models page uses `/v1/admin/models/list` and the catalog to show “INSTALLED” (pulled) vs “AVAILABLE TO PULL” (in catalog but not pulled).

**How pull is triggered**

- **Admin > Models:** Use “Pull” on a model that is “AVAILABLE TO PULL”. The gateway calls Ollama `POST /api/pull` (or `POST /v1/admin/models/pull` / `POST /v1/admin/models/pull/stream` for streaming progress).
- **Live Playground:** Selecting a model does **not** trigger a pull. It calls the **load** endpoint (`POST /v1/admin/models/{model}/load`), which asks Ollama to load the model into memory. If the model is **not** pulled, Ollama returns an error and the gateway returns a non-2xx response. The Workstation Console then shows: *“Model not installed. Pull it from Admin > Models first.”* and does not show “Ready” until the model is actually loaded.

**Summary**

| Action | Verification | If not pulled |
|--------|---------------|----------------|
| List models | Gateway merges `api/tags` (pulled) with catalog/registry | Model appears as “unavailable” or “AVAILABLE TO PULL” |
| Load model (Live Playground) | Gateway calls Ollama load/generate | Load fails; UI shows “Model not installed. Pull from Admin > Models first.” |
| Pull model | Admin > Models > Pull → gateway `POST /api/pull` | User must pull from Admin; no auto-pull from Live Playground |

### 3. Update Asset Catalog

Edit `c:\ABS\core\gateway\catalog.json` to add the model to specific apps:

#### 3.1 Add to App Policies
```json
{
  "id": "contract-reviewer",
  "class": "app",
  "name": "Contract Reviewer",
  "description": "Analyze contracts, extract key clauses, flag risks, and produce citation-backed reports",
  "policy": {
    "allowed_models": ["llama3.2:latest", "llama3.2:7b", "your-new-model"],
    "allowed_embeddings": ["legal-bert", "bge-small-en-v1.5"],
    "defaults": {
      "embed_model": "legal-bert",
      "chat_model": "your-new-model",  // Set as default if desired
      "provider": "huggingface",
      "dim": 768
    }
  }
}
```

#### 3.2 Policy Configuration Options

**Model Access Control:**
```json
"policy": {
  "allowed_models": ["model1", "model2", "your-new-model"],
  "allowed_embeddings": ["embedding1", "embedding2"],
  "defaults": {
    "chat_model": "your-new-model",
    "embed_model": "embedding1",
    "provider": "auto",  // or specific provider
    "dim": 384
  }
}
```

**Provider-Specific Settings:**
- `"provider": "auto"` - Gateway chooses best available provider
- `"provider": "ollama"` - Force Ollama provider
- `"provider": "huggingface"` - Force HuggingFace provider
- `"provider": "openai"` - Force OpenAI/vLLM provider

### 4. Update Gateway Configuration

Edit `c:\ABS\core\gateway\app.py`:

#### 4.1 Add to Supported Models List
```python
# Supported default LLM models (logical names as seen by Ollama)
SUPPORTED_DEFAULT_MODELS = [
    "llama3.2:3b",
    "llama3.2:latest", 
    "llama3:8b",
    "your-new-model"  # Add your model here
]
```

#### 4.2 Provider Detection Logic (if needed)
If your model requires special provider detection logic, update the `detect_provider()` function:

```python
async def detect_provider() -> str:
    """Detect which provider is available and working"""
    # Check vLLM/OpenAI first
    try:
        r = await HTTP.get(f"{OPENAI_BASE}/models", timeout=5)
        if r.is_success:
            return "openai"
    except:
        pass
    
    # Check Ollama
    try:
        r = await HTTP.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        if r.is_success:
            return "ollama"
    except:
        pass
    
    # Check HuggingFace (if configured)
    try:
        # Add HuggingFace detection logic here
        return "huggingface"
    except:
        pass
    
    return "ollama"  # Default fallback
```

### 5. Provider-Specific Configuration

#### 5.1 Ollama Configuration

**For Ollama Provider:**
- Models are auto-pulled on first use
- No additional configuration needed if model is in Ollama registry
- For custom models, create a Modelfile

**Custom Modelfile Example:**
```dockerfile
FROM your-base-model:latest

# Add custom configuration
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

# Set system prompt
SYSTEM """You are a helpful AI assistant."""
```

#### 5.2 HuggingFace Configuration

**Environment Variables:**
```bash
# Add to your .env file or docker-compose.yml
HUGGINGFACE_API_KEY=your_api_key_here
HUGGINGFACE_BASE_URL=https://api-inference.huggingface.co
```

**Model Configuration:**
```json
{
  "your-new-model": {
    "huggingface": "organization/model-name",
    "config": {
      "max_length": 2048,
      "temperature": 0.7,
      "top_p": 0.9
    }
  }
}
```

#### 5.3 vLLM Configuration

**Update `c:\ABS\core\core.yml`:**
```yaml
# Uncomment and configure vLLM service
vllm:
  image: vllm/vllm-openai:0.5.4
  container_name: abs-vllm
  restart: unless-stopped
  runtime: nvidia
  environment:
    TZ: ${TZ}
    MODEL_NAME: your-new-model
    GPU_MEMORY_UTILIZATION: 0.9
  command: >
    --model ${MODEL_NAME}
    --gpu-memory-utilization 0.90
    --dtype float16
    --max-model-len 8192
    --trust-remote-code
  ports:
    - "${VLLM_PORT}:8000"
  networks: [abs-net]
```

### 6. Resource Management

#### 6.1 GPU Memory Considerations

**Memory Estimation:**
- **FP32**: ~4 bytes per parameter
- **FP16**: ~2 bytes per parameter  
- **4-bit Quantized**: ~0.5 bytes per parameter
- **8-bit Quantized**: ~1 byte per parameter

**Example for 7B model:**
- FP32: ~28GB VRAM
- FP16: ~14GB VRAM
- 4-bit: ~3.5GB VRAM

#### 6.2 Docker Configuration Updates

**Update `c:\ABS\core\core.yml` for memory management:**
```yaml
ollama:
  image: ollama/ollama:0.3.8
  container_name: abs-ollama
  restart: unless-stopped
  runtime: nvidia
  environment:
    TZ: ${TZ}
    OLLAMA_KEEP_ALIVE: "24h"
    OLLAMA_GPU_MEMORY_FRACTION: "0.9"  # Adjust based on your GPU
    OLLAMA_MAX_LOADED_MODELS: "2"      # Limit concurrent models
  volumes:
    - ollama_models:/root/.ollama
  ports:
    - "${OLLAMA_PORT}:11434"
  networks: [abs-net]
```

### 7. Testing & Validation

#### 7.1 Model Availability Test
```bash
# Test via Hub Gateway API
curl -X GET "http://localhost:8081/admin/models?app_id=onyx-assistant"

# Expected response should include your new model
{
  "models": [
    {
      "name": "your-new-model",
      "available": true,
      "running": false,
      "allowed": true
    }
  ]
}
```

#### 7.2 Model Loading Test
```bash
# Test model loading
curl -X POST "http://localhost:8081/admin/models/your-new-model/load"

# Expected response
{
  "status": "loaded",
  "model": "your-new-model"
}
```

#### 7.3 Chat Completion Test
```bash
# Test chat completion
curl -X POST "http://localhost:8081/v1/chat/completions" \
  -H "X-ABS-App-Id: onyx-assistant" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-new-model",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

#### 7.4 App Integration Test
Test each app that should have access to the new model:

```bash
# Test Contract Reviewer
curl -X POST "http://localhost:8081/v1/chat/completions" \
  -H "X-ABS-App-Id: contract-reviewer" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-new-model",
    "messages": [{"role": "user", "content": "Test message"}]
  }'

# Test Onyx Assistant
curl -X POST "http://localhost:8000/chat" \
  -H "X-ABS-App-Id: onyx-assistant" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-new-model",
    "messages": [{"role": "user", "content": "Test message"}]
  }'
```

### 8. Deployment Process

#### 8.1 Pre-Deployment Checklist
- [ ] Model availability verified
- [ ] Resource requirements assessed
- [ ] Registry entries added
- [ ] Catalog policies updated
- [ ] Gateway configuration updated
- [ ] Provider-specific config completed
- [ ] Tests written and validated

#### 8.2 Deployment Steps

**1. Backup Current Configuration:**
```bash
cd c:\ABS\core\gateway
cp catalog.json catalog.json.backup
cp registry.json registry.json.backup
cp app.py app.py.backup
```

**2. Apply Configuration Changes:**
- Update `registry.json` with new model aliases
- Update `catalog.json` with app policies
- Update `app.py` with supported models list
- Update `core.yml` if needed for provider config

**3. Restart Core Services:**
```bash
cd c:\ABS\core
.\stop-core.ps1
.\start-core.ps1
```

**4. Verify Deployment:**
```bash
# Check service status
curl http://localhost:8081/admin/services/status

# Check model availability
curl http://localhost:8081/admin/models

# Test model loading
curl -X POST http://localhost:8081/admin/models/your-new-model/load
```

#### 8.3 Rollback Procedure
If issues occur:

```bash
# Restore backups
cd c:\ABS\core\gateway
cp catalog.json.backup catalog.json
cp registry.json.backup registry.json
cp app.py.backup app.py

# Restart services
cd c:\ABS\core
.\stop-core.ps1
.\start-core.ps1
```

### 9. Monitoring & Maintenance

#### 9.1 Model Lifecycle Management

**Auto-Wake System:**
- Models are automatically loaded when first requested
- Auto-unload after idle timeout (configurable)
- Manual control via admin endpoints

**Manual Model Management:**
```bash
# Load model
curl -X POST http://localhost:8081/admin/models/your-new-model/load

# Unload model
curl -X DELETE http://localhost:8081/admin/models/your-new-model

# Check model status
curl http://localhost:8081/admin/idle-status
```

#### 9.2 Performance Monitoring

**Key Metrics to Monitor:**
- Model response times
- GPU memory utilization
- Model loading/unloading frequency
- Error rates by model/provider

**Monitoring Commands:**
```bash
# Check service logs
curl http://localhost:8081/admin/logs/ollama

# Check idle status
curl http://localhost:8081/admin/idle-status

# Check model registry
curl http://localhost:8081/admin/models
```

#### 9.3 Troubleshooting

**Common Issues:**

1. **Model Not Found:**
   - Check registry.json aliases
   - Verify provider-specific model names
   - Check model availability in provider

2. **Memory Issues:**
   - Reduce GPU memory fraction
   - Use quantized models
   - Limit concurrent models

3. **Provider Routing Issues:**
   - Check provider detection logic
   - Verify service health checks
   - Check network connectivity

4. **Policy Enforcement Errors:**
   - Verify catalog.json policies
   - Check app_id headers
   - Validate allowed_models lists

**Debug Commands:**
```bash
# Check service health
curl http://localhost:8081/admin/services/status

# Check provider detection
curl http://localhost:8081/admin/providers/status

# Check model policies
curl http://localhost:8081/catalog
```

## Best Practices

### 1. Model Naming
- Use descriptive, version-specific names
- Follow consistent naming conventions
- Include model size/variant in name when relevant

### 2. Resource Management
- Start with smaller models for testing
- Use quantization for memory efficiency
- Monitor GPU utilization regularly

### 3. Policy Design
- Grant minimal necessary model access
- Use app-specific defaults when appropriate
- Document model capabilities and use cases

### 4. Testing Strategy
- Test with multiple apps
- Verify provider fallback behavior
- Test model loading/unloading cycles

### 5. Documentation
- Document model capabilities and limitations
- Update app-specific documentation
- Maintain model compatibility matrix

## Example: Adding Llama 4 Scout

Here's a complete example of adding Llama 4 Scout (17B parameters):

### 1. Registry Entry
```json
"llama4-scout": { 
  "openai": "llama4-scout", 
  "ollama": "llama4:scout",
  "huggingface": "meta-llama/Llama-4-Scout-17B-Instruct" 
}
```

### 2. Catalog Policy
```json
{
  "id": "onyx-assistant",
  "policy": {
    "allowed_models": ["llama3.2:3b", "llama3.2:7b", "llama3.2:latest", "llama3:8b", "llama4-scout"],
    "allowed_embeddings": ["bge-small-en-v1.5", "all-minilm"]
  }
}
```

### 3. Gateway Configuration
```python
SUPPORTED_DEFAULT_MODELS = [
    "llama3.2:3b",
    "llama3.2:latest", 
    "llama3:8b",
    "llama4-scout"
]
```

### 4. Resource Considerations
- **Memory**: ~35GB VRAM (FP16)
- **Quantization**: Consider 4-bit for ~9GB VRAM
- **Provider**: HuggingFace for immediate availability

This completes the comprehensive guide for adding new models to your ABS AI Hub architecture. The process ensures proper integration while maintaining the benefits of centralized management, policy enforcement, and resource efficiency.
