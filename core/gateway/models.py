from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatReq(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = None

class EmbedReq(BaseModel):
    input: List[str]
    override_model: Optional[str] = None

# ---- Tri-Store Inspector Schemas ----
class StoreSnapshot(BaseModel):
    found: bool
    store_type: str  # 'postgres' | 'redis' | 'qdrant'
    key: str
    payload: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None
    updated_at: Optional[str] = None
    ttl_seconds: Optional[int] = None  # Redis only

class TriStoreSnapshot(BaseModel):
    doc_id: str
    requested_at: str
    env: str = 'prod'
    postgres: Optional[StoreSnapshot] = None
    redis: Optional[StoreSnapshot] = None
    qdrant: Optional[StoreSnapshot] = None
    consistency: Dict[str, Any]

class ConsistencyReport(BaseModel):
    status: str  # 'OK' | 'WARNING' | 'ERROR'
    problems: List[Dict[str, str]]
    field_diff: List[Dict[str, Any]]
    embeddings_diff: List[Dict[str, Any]]

class BatchInspectRequest(BaseModel):
    doc_ids: List[str]
    env: str = 'prod'
