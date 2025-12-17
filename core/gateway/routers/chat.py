from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional, List
import time
import json
import httpx
import hashlib
from sentence_transformers import SentenceTransformer

from models import ChatReq, EmbedReq
from config import OLLAMA_BASE, OPENAI_BASE, OPENAI_KEY, AUTO_WAKE_SETTINGS
from services.autowake import ensure_service_ready
from .common import get_catalog, get_registry
from adapters.llm_runtime import get_llm_adapter

router = APIRouter()
HTTP = httpx.AsyncClient(timeout=60)
MODEL_CACHE = {}

# Helpers (simplified for brevity, should be shared if complex)
async def detect_provider():
    try:
        r = await HTTP.get(f"{OPENAI_BASE.rstrip('/')}/models")
        if r.is_success: return "openai"
    except: pass
    try:
        r = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
        if r.is_success: return "ollama"
    except: pass
    raise HTTPException(503, "No LLM provider reachable")

def pick_app_cfg(app_id: Optional[str]):
    CATALOG = get_catalog()
    REG = get_registry()
    for asset in CATALOG.get("assets", []):
        if asset.get("class") == "app" and asset.get("id") == (app_id or ""):
            return asset.get("policy", {}).get("defaults", {})
    return CATALOG.get("defaults", REG.get("defaults", {}))

def logical_to_provider_id(logical: str, provider: str) -> str:
    REG = get_registry()
    return REG.get("aliases", {}).get(logical, {}).get(provider, logical)

async def preload_model_if_needed(model_name: str, provider: str):
    if provider != "ollama": return
    # ... (simplified preload logic from app.py) ...
    # ideally moved to a service, but inline for now
    pass

@router.get("/v1/models")
async def list_models(app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """List available models (OpenAI compatible)"""
    try:
        # 1. Get running models from Ollama
        running = set()
        running_models_data = []
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{OLLAMA_BASE.rstrip('/')}/api/ps")
                if r.status_code == 200:
                    running_models_data = r.json().get("models", [])
                    for m in running_models_data:
                        n = m.get("name")
                        if n:
                            running.add(n)
                            if n.endswith(":latest"):
                                running.add(n[:-7])
                            else:
                                running.add(f"{n}:latest")
        except Exception:
            pass

        # 2. Get available models (tags) from Ollama
        available = set()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
                if r.status_code == 200:
                    for m in r.json().get("models", []):
                        n = m.get("name")
                        if n:
                            available.add(n)
                            if n.endswith(":latest"):
                                available.add(n[:-7])
                            else:
                                available.add(f"{n}:latest")
        except Exception:
            pass

        # 3. Merge with Catalog and Registry
        CATALOG = get_catalog()
        REG = get_registry()
        
        all_models = set()
        all_models.update(available)
        
        # Add from Catalog assets (apps)
        for asset in CATALOG.get("assets", []):
            if asset.get("class") == "app":
                policy = asset.get("policy", {})
                all_models.update(policy.get("allowed_models", []))
                all_models.update(policy.get("allowed_embeddings", []))
        
        # Add from Registry aliases
        aliases = REG.get("aliases", {})
        all_models.update(aliases.keys())
        
        # Add defaults
        defaults = CATALOG.get("defaults", {})
        if defaults.get("chat_model"): all_models.add(defaults["chat_model"])
        if defaults.get("embed_model"): all_models.add(defaults["embed_model"])

        # Filter by App Policy if app_id present
        allowed_models = None
        if app_id:
            for asset in CATALOG.get("assets", []):
                if asset.get("id") == app_id:
                    policy = asset.get("policy", {})
                    allowed_models = policy.get("allowed_models", []) + policy.get("allowed_embeddings", [])
                    break
        
        # Build response objects
        models_out = []
        seen = set()
        
        # Normalize helper
        def _base(name):
            return name[:-7] if name.endswith(":latest") else name

        for model_name in sorted(all_models):
            logical_name = _base(model_name)
            if logical_name in seen: continue
            seen.add(logical_name)
            
            # Filter if policy active
            if allowed_models is not None and logical_name not in allowed_models:
                continue
                
            # Determine status/type
            ollama_name = aliases.get(logical_name, {}).get("ollama", logical_name)
            is_running = ollama_name in running
            is_available = ollama_name in available
            
            is_embedding = "embed" in logical_name or "bert" in logical_name
            
            models_out.append({
                "id": logical_name,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "organization-owner",
                "permission": [],
                "root": logical_name,
                "parent": None,
                "status": "running" if is_running else ("available" if is_available else "unavailable")
            })
            
        return {"object": "list", "data": models_out}

    except Exception as e:
        raise HTTPException(500, f"Error listing models: {str(e)}")

@router.post("/v1/chat/completions")
async def chat(req: ChatReq, request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Chat completion using LLM adapter."""
    cfg = pick_app_cfg(app_id)
    model_logical = req.model or cfg.get("chat_model", "contract-default")
    
    # Use adapter for unified API handling
    adapter = await get_llm_adapter()
    if not adapter.is_initialized():
        raise HTTPException(503, "LLM runtime not available")
    
    # Ensure service is running (auto-wake)
    asset = adapter.get_asset()
    if asset and asset.asset_id == "ollama":
        if not await ensure_service_ready("ollama"):
            raise HTTPException(503, "Ollama service unavailable")
    
    # Convert messages to dict format
    messages = [m.model_dump() for m in req.messages]
    
    result = await adapter.chat_completion(
        messages=messages,
        model=model_logical,
        temperature=req.temperature,
        stream=False
    )
    
    if result.get("error"):
        raise HTTPException(result.get("status_code", 500), result.get("message", "Unknown error"))
    
    return result

@router.post("/v1/embeddings")
async def embeddings(req: EmbedReq, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Generate embeddings using LLM adapter."""
    cfg = pick_app_cfg(app_id)
    model = req.override_model or cfg.get("embed_model", "bge-small-en-v1.5")
    
    # Use adapter for unified API handling
    adapter = await get_llm_adapter()
    if not adapter.is_initialized():
        raise HTTPException(503, "LLM runtime not available")
    
    # Ensure service is running (auto-wake)
    asset = adapter.get_asset()
    if asset and asset.asset_id == "ollama":
        if not await ensure_service_ready("ollama"):
            raise HTTPException(503, "Ollama service unavailable")
    
    result = await adapter.embeddings(
        texts=req.input,
        model=model
    )
    
    if result.get("error"):
        raise HTTPException(result.get("status_code", 500), result.get("message", "Unknown error"))
    
    return result
