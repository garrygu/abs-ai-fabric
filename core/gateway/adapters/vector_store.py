"""
Vector Store Adapter

Provides a unified interface for vector database operations, translating between
the Gateway's API and backend implementations (Qdrant, Milvus, etc.).

Usage:
    adapter = VectorStoreAdapter()
    await adapter.initialize()
    
    await adapter.upsert(collection, vectors, payloads)
    results = await adapter.search(collection, query_vector, top_k=10)
"""

import httpx
import time
from typing import List, Dict, Any, Optional

from services.asset_manager import get_asset_manager, Asset


class VectorStoreAdapter:
    """
    Adapter for vector-store interface.
    
    Automatically selects the bound implementation and provides
    a consistent API regardless of backend.
    """
    
    def __init__(self):
        self._asset: Optional[Asset] = None
        self._http: Optional[httpx.AsyncClient] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the adapter with the bound vector store asset."""
        try:
            manager = await get_asset_manager()
            self._asset = manager.get_bound_asset("vector-store")
            
            if not self._asset:
                print("VectorStoreAdapter: No vector-store binding found")
                return False
            
            self._http = httpx.AsyncClient(timeout=30.0)
            self._initialized = True
            print(f"VectorStoreAdapter initialized with: {self._asset.asset_id}")
            return True
        except Exception as e:
            print(f"VectorStoreAdapter initialization failed: {e}")
            return False
    
    def is_initialized(self) -> bool:
        return self._initialized
    
    def get_asset(self) -> Optional[Asset]:
        return self._asset
    
    def _get_base_url(self) -> str:
        """Get the base URL for the vector store."""
        if self._asset:
            return self._asset.get_endpoint("api_base") or "http://qdrant:6333"
        return "http://qdrant:6333"
    
    # --- Collections ---
    
    async def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            r = await self._http.get(f"{self._get_base_url()}/collections")
            if r.is_success:
                data = r.json()
                return [c.get("name") for c in data.get("result", {}).get("collections", [])]
        except Exception as e:
            print(f"Error listing collections: {e}")
        return []
    
    async def create_collection(
        self,
        name: str,
        vector_size: int,
        distance: str = "Cosine"
    ) -> bool:
        """Create a new collection."""
        try:
            payload = {
                "vectors": {
                    "size": vector_size,
                    "distance": distance
                }
            }
            r = await self._http.put(
                f"{self._get_base_url()}/collections/{name}",
                json=payload
            )
            return r.is_success
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    async def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            r = await self._http.delete(f"{self._get_base_url()}/collections/{name}")
            return r.is_success
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
    
    async def collection_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get collection information."""
        try:
            r = await self._http.get(f"{self._get_base_url()}/collections/{name}")
            if r.is_success:
                return r.json().get("result", {})
        except Exception as e:
            print(f"Error getting collection info: {e}")
        return None
    
    # --- Points ---
    
    async def upsert(
        self,
        collection: str,
        points: List[Dict[str, Any]]
    ) -> bool:
        """
        Upsert vectors with payloads.
        
        points format: [{"id": str/int, "vector": [...], "payload": {...}}, ...]
        """
        try:
            r = await self._http.put(
                f"{self._get_base_url()}/collections/{collection}/points",
                json={"points": points}
            )
            return r.is_success
        except Exception as e:
            print(f"Error upserting points: {e}")
            return False
    
    async def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        with_payload: bool = True,
        with_vector: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Returns list of matches with score, id, and optionally payload/vector.
        """
        try:
            payload = {
                "vector": query_vector,
                "limit": top_k,
                "with_payload": with_payload,
                "with_vector": with_vector
            }
            if filter:
                payload["filter"] = filter
            
            r = await self._http.post(
                f"{self._get_base_url()}/collections/{collection}/points/search",
                json=payload
            )
            
            if r.is_success:
                return r.json().get("result", [])
        except Exception as e:
            print(f"Error searching: {e}")
        return []
    
    async def get_points(
        self,
        collection: str,
        ids: List[Any],
        with_payload: bool = True,
        with_vector: bool = False
    ) -> List[Dict[str, Any]]:
        """Get points by IDs."""
        try:
            r = await self._http.post(
                f"{self._get_base_url()}/collections/{collection}/points",
                json={
                    "ids": ids,
                    "with_payload": with_payload,
                    "with_vector": with_vector
                }
            )
            if r.is_success:
                return r.json().get("result", [])
        except Exception as e:
            print(f"Error getting points: {e}")
        return []
    
    async def delete_points(
        self,
        collection: str,
        ids: List[Any]
    ) -> bool:
        """Delete points by IDs."""
        try:
            r = await self._http.post(
                f"{self._get_base_url()}/collections/{collection}/points/delete",
                json={"points": ids}
            )
            return r.is_success
        except Exception as e:
            print(f"Error deleting points: {e}")
            return False
    
    # --- Health ---
    
    async def health_check(self) -> bool:
        """Check if vector store is healthy."""
        try:
            r = await self._http.get(f"{self._get_base_url()}/collections")
            return r.is_success
        except:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        if self._http:
            await self._http.aclose()


# Singleton instance
_adapter: Optional[VectorStoreAdapter] = None


async def get_vector_store_adapter() -> VectorStoreAdapter:
    """Get or create the singleton VectorStoreAdapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = VectorStoreAdapter()
        await _adapter.initialize()
    return _adapter
