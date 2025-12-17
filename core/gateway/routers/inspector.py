from fastapi import APIRouter, Query
from models import TriStoreSnapshot, BatchInspectRequest
from services.trstore import fetch_postgres_doc, fetch_redis_doc, fetch_qdrant_doc, analyze_consistency
import asyncio
from datetime import datetime

router = APIRouter()

@router.get("/v1/inspector/{doc_id}", response_model=TriStoreSnapshot)
async def inspect_document(doc_id: str, env: str = Query('prod')):
    postgres, redis, qdrant = await asyncio.gather(
        fetch_postgres_doc(doc_id),
        fetch_redis_doc(doc_id),
        fetch_qdrant_doc(doc_id)
    )
    consistency = analyze_consistency(postgres, redis, qdrant)
    
    return TriStoreSnapshot(
        doc_id=doc_id,
        requested_at=datetime.utcnow().isoformat() + "Z",
        env=env,
        postgres=postgres,
        redis=redis,
        qdrant=qdrant,
        consistency=consistency
    )
