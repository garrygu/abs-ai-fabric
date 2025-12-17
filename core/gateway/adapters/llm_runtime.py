"""
LLM Runtime Adapter

Provides a unified interface for LLM operations, translating between
the Gateway's OpenAI-compatible API and backend implementations (Ollama, vLLM, etc.).

Usage:
    adapter = LLMRuntimeAdapter()
    await adapter.initialize()
    
    response = await adapter.chat_completion(messages, model="llama3.2:3b")
    embeddings = await adapter.embeddings(texts, model="bge-small")
"""

import httpx
import time
import json
from typing import List, Dict, Any, Optional, AsyncGenerator

from services.asset_manager import get_asset_manager, Asset


class LLMRuntimeAdapter:
    """
    Adapter for LLM runtime interface.
    
    Automatically selects the bound implementation and translates
    API calls to the appropriate backend format.
    """
    
    def __init__(self):
        self._asset: Optional[Asset] = None
        self._http: Optional[httpx.AsyncClient] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the adapter with the bound LLM runtime asset."""
        try:
            manager = await get_asset_manager()
            self._asset = manager.get_bound_asset("llm-runtime")
            
            if not self._asset:
                print("LLMRuntimeAdapter: No llm-runtime binding found")
                return False
            
            self._http = httpx.AsyncClient(timeout=120.0)
            self._initialized = True
            print(f"LLMRuntimeAdapter initialized with: {self._asset.asset_id}")
            return True
        except Exception as e:
            print(f"LLMRuntimeAdapter initialization failed: {e}")
            return False
    
    def is_initialized(self) -> bool:
        return self._initialized
    
    def get_asset(self) -> Optional[Asset]:
        return self._asset
    
    def _get_base_url(self) -> str:
        """Get the base URL for the LLM runtime."""
        if self._asset:
            # Try to get from endpoints
            chat_endpoint = self._asset.get_endpoint("chat")
            if chat_endpoint:
                # Extract base URL (remove /api/chat or similar)
                return chat_endpoint.rsplit("/", 2)[0]
        return "http://ollama:11434"
    
    def _requires_translation(self) -> bool:
        """Check if this implementation requires API translation."""
        if self._asset:
            return self._asset.adapter_required
        return True  # Default to translation for safety
    
    # --- Chat Completion ---
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a chat completion.
        
        Always returns OpenAI-compatible format, regardless of backend.
        """
        if not self._initialized:
            raise RuntimeError("Adapter not initialized")
        
        t0 = time.time()
        
        if self._requires_translation():
            # Ollama backend - translate format
            result = await self._chat_ollama(messages, model, temperature, stream)
        else:
            # OpenAI-compatible backend - pass through
            result = await self._chat_openai(messages, model, temperature, max_tokens, stream)
        
        result["_latency_ms"] = int((time.time() - t0) * 1000)
        return result
    
    async def _chat_ollama(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        stream: bool
    ) -> Dict[str, Any]:
        """Handle chat completion via Ollama API."""
        endpoint = self._asset.get_endpoint("chat") or f"{self._get_base_url()}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature}
        }
        
        try:
            r = await self._http.post(endpoint, json=payload)
            
            if not r.is_success:
                return {
                    "error": True,
                    "status_code": r.status_code,
                    "message": r.text
                }
            
            data = r.json()
            
            # Translate to OpenAI format
            content = data.get("message", {}).get("content", data.get("response", ""))
            
            return {
                "id": f"chatcmpl_{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                },
                "_provider": "ollama"
            }
        except Exception as e:
            return {
                "error": True,
                "message": str(e)
            }
    
    async def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        stream: bool
    ) -> Dict[str, Any]:
        """Handle chat completion via OpenAI-compatible API."""
        endpoint = f"{self._get_base_url()}/v1/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            r = await self._http.post(endpoint, json=payload)
            
            if not r.is_success:
                return {
                    "error": True,
                    "status_code": r.status_code,
                    "message": r.text
                }
            
            result = r.json()
            result["_provider"] = "openai"
            return result
        except Exception as e:
            return {
                "error": True,
                "message": str(e)
            }
    
    # --- Embeddings ---
    
    async def embeddings(
        self,
        texts: List[str],
        model: str
    ) -> Dict[str, Any]:
        """
        Generate embeddings for a list of texts.
        
        Always returns OpenAI-compatible format.
        """
        if not self._initialized:
            raise RuntimeError("Adapter not initialized")
        
        t0 = time.time()
        
        if self._requires_translation():
            result = await self._embeddings_ollama(texts, model)
        else:
            result = await self._embeddings_openai(texts, model)
        
        result["_latency_ms"] = int((time.time() - t0) * 1000)
        return result
    
    async def _embeddings_ollama(
        self,
        texts: List[str],
        model: str
    ) -> Dict[str, Any]:
        """Handle embeddings via Ollama API."""
        endpoint = self._asset.get_endpoint("embeddings") or f"{self._get_base_url()}/api/embeddings"
        
        data = []
        for i, text in enumerate(texts):
            try:
                r = await self._http.post(endpoint, json={"model": model, "prompt": text})
                if r.is_success:
                    emb = r.json().get("embedding", [])
                    data.append({"index": i, "embedding": emb, "object": "embedding"})
            except Exception as e:
                print(f"Embedding error for text {i}: {e}")
        
        return {
            "object": "list",
            "data": data,
            "model": model,
            "_provider": "ollama"
        }
    
    async def _embeddings_openai(
        self,
        texts: List[str],
        model: str
    ) -> Dict[str, Any]:
        """Handle embeddings via OpenAI-compatible API."""
        endpoint = f"{self._get_base_url()}/v1/embeddings"
        
        try:
            r = await self._http.post(endpoint, json={"model": model, "input": texts})
            if r.is_success:
                result = r.json()
                result["_provider"] = "openai"
                return result
            return {
                "error": True,
                "status_code": r.status_code,
                "message": r.text
            }
        except Exception as e:
            return {
                "error": True,
                "message": str(e)
            }
    
    # --- Model Management ---
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from the runtime."""
        if not self._initialized:
            return []
        
        try:
            if self._requires_translation():
                # Ollama
                endpoint = f"{self._get_base_url()}/api/tags"
                r = await self._http.get(endpoint)
                if r.is_success:
                    models = r.json().get("models", [])
                    return [{"id": m.get("name"), "object": "model", "owned_by": "ollama"} for m in models]
            else:
                # OpenAI-compatible
                endpoint = f"{self._get_base_url()}/v1/models"
                r = await self._http.get(endpoint)
                if r.is_success:
                    return r.json().get("data", [])
        except Exception as e:
            print(f"Error listing models: {e}")
        
        return []
    
    async def close(self):
        """Close the HTTP client."""
        if self._http:
            await self._http.aclose()


# Singleton instance
_adapter: Optional[LLMRuntimeAdapter] = None


async def get_llm_adapter() -> LLMRuntimeAdapter:
    """Get or create the singleton LLMRuntimeAdapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = LLMRuntimeAdapter()
        await _adapter.initialize()
    return _adapter
