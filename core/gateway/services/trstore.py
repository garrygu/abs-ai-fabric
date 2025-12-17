import json
import hashlib
import httpx
from typing import Dict, Any, Optional
import redis as redislib

# Imports from config/models
try:
    from models import StoreSnapshot
    from config import REDIS_URL
except ImportError:
    from models import StoreSnapshot
    from config import REDIS_URL

# Redis connection
rds = None
try:
    rds = redislib.from_url(REDIS_URL)
    rds.ping()
except Exception:
    rds = None

def compute_checksum(data: Dict[str, Any]) -> str:
    """Compute stable checksum for data comparison"""
    sorted_data = {k: data[k] for k in sorted(data.keys())}
    json_str = json.dumps(sorted_data, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]

def compute_canonical_checksum(data: Dict[str, Any], store_type: str) -> str:
    """Compute checksum for canonical fields that should be consistent across stores"""
    canonical_fields = {
        'postgres': ['id', 'filename', 'file_size', 'file_type', 'status'],
        'redis': ['document_id', 'filename', 'file_size', 'file_type', 'status'],
        'qdrant': ['document_id', 'total_chunks']
    }
    
    canonical_data = {}
    for field in canonical_fields.get(store_type, []):
        if field in data:
            canonical_data[field] = data[field]
    
    if store_type == 'qdrant' and 'chunks' in data:
        canonical_data['chunk_count'] = len(data['chunks'])
    
    return compute_checksum(canonical_data)

async def fetch_postgres_doc(doc_id: str) -> Optional[StoreSnapshot]:
    """Fetch document from PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='document-hub-postgres',
            port=5432,
            database='document_hub',
            user='hub_user',
            password='secure_password',
            connect_timeout=5
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, filename, original_filename, file_path, file_size,
                   file_type, mime_type, upload_timestamp, analysis_timestamp,
                   status, metadata, created_at, updated_at
            FROM document_hub.documents 
            WHERE id = %s
        """, (doc_id,))
        
        row = cursor.fetchone()
        if not row:
            return StoreSnapshot(found=False, store_type='postgres', key=doc_id)
        
        payload = {
            'id': row[0],
            'filename': row[1],
            'original_filename': row[2],
            'file_path': row[3],
            'file_size': row[4],
            'file_type': row[5],
            'mime_type': row[6],
            'upload_timestamp': row[7].isoformat() if row[7] else None,
            'analysis_timestamp': row[8].isoformat() if row[8] else None,
            'status': row[9],
            'metadata': row[10],
            'created_at': row[11].isoformat() if row[11] else None,
            'updated_at': row[12].isoformat() if row[12] else None
        }
        
        checksum = compute_canonical_checksum(payload, 'postgres')
        
        cursor.close()
        conn.close()
        
        return StoreSnapshot(
            found=True,
            store_type='postgres',
            key=doc_id,
            payload=payload,
            checksum=checksum,
            updated_at=payload['updated_at']
        )
        
    except Exception as e:
        print(f"PostgreSQL fetch error: {e}")
        return StoreSnapshot(found=False, store_type='postgres', key=doc_id)

async def fetch_redis_doc(doc_id: str) -> Optional[StoreSnapshot]:
    """Fetch document from Redis"""
    try:
        if rds is None:
            return StoreSnapshot(found=False, store_type='redis', key=f"document:{doc_id}")
        
        analysis_data = None
        analysis_id = None
        
        analysis_id_key = f"document_analysis:{doc_id}"
        analysis_id = rds.get(analysis_id_key)
        if analysis_id:
            analysis_id = analysis_id.decode('utf-8')
            analysis_key = f"analysis:{analysis_id}"
            analysis_data = rds.get(analysis_key)
            if analysis_data:
                analysis_data = json.loads(analysis_data.decode('utf-8'))
        
        if not analysis_data:
            analysis_keys = rds.keys("analysis:*")
            for key in analysis_keys:
                key_str = key.decode('utf-8')
                analysis_content = rds.get(key_str)
                if analysis_content:
                    try:
                        analysis_json = json.loads(analysis_content.decode('utf-8'))
                        if analysis_json.get('document_id') == doc_id:
                            analysis_data = analysis_json
                            analysis_id = analysis_json.get('id')
                            break
                    except json.JSONDecodeError:
                        continue
        
        if analysis_data:
            ttl = rds.ttl(f"analysis:{analysis_id}")
            checksum = compute_canonical_checksum(analysis_data, 'redis')
            return StoreSnapshot(
                found=True,
                store_type='redis',
                key=f"analysis:{analysis_id}",
                payload=analysis_data,
                checksum=checksum,
                ttl_seconds=ttl,
                updated_at=analysis_data.get('created_at')
            )
            
        key = f"document:{doc_id}"
        ttl = rds.ttl(key)
        if ttl != -2:
            fields = rds.hgetall(key)
            if fields:
                payload = {k.decode(): v.decode() for k, v in fields.items()}
                checksum = compute_canonical_checksum(payload, 'redis')
                return StoreSnapshot(
                    found=True,
                    store_type='redis',
                    key=key,
                    payload=payload,
                    checksum=checksum,
                    ttl_seconds=ttl,
                    updated_at=payload.get('updated_at')
                )
        
        return StoreSnapshot(found=False, store_type='redis', key=f"document:{doc_id}")
    
    except Exception as e:
        print(f"Redis fetch error: {e}")
        return StoreSnapshot(found=False, store_type='redis', key=f"document:{doc_id}")

async def fetch_qdrant_doc(doc_id: str) -> Optional[StoreSnapshot]:
    """Fetch document from Qdrant"""
    try:
        async with httpx.AsyncClient() as client:
            search_response = await client.post(
                f"http://qdrant:6333/collections/legal_documents/points/scroll",
                json={
                    "filter": {
                        "must": [
                            {
                                "key": "document_id",
                                "match": {"value": doc_id}
                            }
                        ]
                    },
                    "limit": 10,
                    "with_payload": True,
                    "with_vector": False
                },
                timeout=5.0
            )
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                search_points = search_data.get('result', {}).get('points', [])
                
                if search_points:
                    combined_payload = {
                        "document_id": doc_id,
                        "chunks": [],
                        "total_chunks": len(search_points),
                        "chunk_summary": {}
                    }
                    
                    for point in search_points:
                        payload = point.get('payload', {})
                        chunk_info = {
                            "point_id": point.get('id'),
                            "chunk_index": payload.get('chunk_index'),
                            "chunk_type": payload.get('chunk_type'),
                            "chunk_text": payload.get('chunk_text', '')[:200],
                            "word_count": payload.get('word_count'),
                            "start_position": payload.get('start_position'),
                            "end_position": payload.get('end_position'),
                            "created_at": payload.get('created_at')
                        }
                        combined_payload["chunks"].append(chunk_info)
                        
                        chunk_type = payload.get('chunk_type', 'unknown')
                        if chunk_type not in combined_payload["chunk_summary"]:
                            combined_payload["chunk_summary"][chunk_type] = 0
                        combined_payload["chunk_summary"][chunk_type] += 1
                    
                    combined_payload["chunks"].sort(key=lambda x: x.get('chunk_index', 0))
                    checksum = compute_canonical_checksum(combined_payload, 'qdrant')
                    
                    return StoreSnapshot(
                        found=True,
                        store_type='qdrant',
                        key=doc_id,
                        payload=combined_payload,
                        checksum=checksum,
                        updated_at=search_points[0].get('payload', {}).get('created_at')
                    )
            
            return StoreSnapshot(found=False, store_type='qdrant', key=doc_id)
            
    except Exception as e:
        print(f"Qdrant fetch error: {e}")
        return StoreSnapshot(found=False, store_type='qdrant', key=doc_id)

def analyze_consistency(postgres: StoreSnapshot, redis: StoreSnapshot, qdrant: StoreSnapshot) -> Dict[str, Any]:
    """Analyze consistency across all three stores"""
    problems = []
    field_diff = []
    
    stores = {
        'postgres': postgres,
        'redis': redis, 
        'qdrant': qdrant
    }
    
    found_stores = [name for name, store in stores.items() if store and store.found]
    
    if len(found_stores) == 0:
        problems.append({'code': 'MISSING_ALL', 'message': 'Document not found in any store', 'severity': 'ERROR'})
    elif len(found_stores) < 3:
        missing = [name for name, store in stores.items() if not store or not store.found]
        problems.append({'code': 'MISSING_STORES', 'message': f'Document missing from: {", ".join(missing)}', 'severity': 'WARNING'})
    
    canonical_checksums = {}
    for name, store in stores.items():
        if store and store.found and store.payload:
            canonical_checksums[name] = compute_canonical_checksum(store.payload, name)
    
    if len(set(canonical_checksums.values())) > 1:
        problems.append({'code': 'CANONICAL_CHECKSUM_MISMATCH', 'message': 'Canonical data differs across stores', 'severity': 'WARNING'})
    
    consistent_fields = ['filename', 'file_size', 'file_type', 'status']
    for field in consistent_fields:
        values = {}
        for name, store in stores.items():
            if store and store.found and store.payload:
                if name == 'redis' and field == 'filename':
                    values[name] = store.payload.get('filename') or store.payload.get('original_filename')
                elif name == 'qdrant':
                    values[name] = 'N/A'
                else:
                    values[name] = store.payload.get(field)
        
        non_null_values = {k: v for k, v in values.items() if v is not None and v != 'N/A'}
        if len(set(str(v) for v in non_null_values.values())) > 1:
            field_diff.append({'field': field, 'values': values})
    
    updated_at_values = {}
    for name, store in stores.items():
        if store and store.found and store.payload:
            if name == 'qdrant':
                updated_at_values[name] = store.payload.get('created_at', 'N/A')
            else:
                updated_at_values[name] = store.payload.get('updated_at')
    
    non_null_updated_at = {k: v for k, v in updated_at_values.items() if v is not None and v != 'N/A'}
    if len(non_null_updated_at) > 1:
        timestamps = []
        for v in non_null_updated_at.values():
            try:
                from datetime import datetime
                ts = datetime.fromisoformat(v.replace('Z', '+00:00'))
                timestamps.append(ts)
            except:
                continue
        
        if timestamps:
            max_diff = max(timestamps) - min(timestamps)
            if max_diff.total_seconds() > 60:
                field_diff.append({'field': 'updated_at', 'values': updated_at_values, 'note': 'Significant timestamp difference detected'})
    
    if len(found_stores) == 0:
        status = 'ERROR'
    elif len(found_stores) < 3 or problems:
        status = 'WARNING'
    else:
        status = 'OK'
    
    return {
        'status': status,
        'problems': problems,
        'field_diff': field_diff,
        'found_stores': found_stores,
        'checksums': canonical_checksums
    }
