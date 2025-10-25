"""
Document History Service
Manages audit trail for all document handling events
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncpg
import logging

logger = logging.getLogger(__name__)


class DocumentHistoryService:
    """Service for managing document history/audit trail"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def log_event(
        self,
        document_id: str,
        event_type: str,
        event_status: str = "success",
        event_description: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a document handling event"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Insert the event
                    event_id = await conn.fetchval("""
                        INSERT INTO document_hub.document_history
                        (document_id, event_type, event_status, event_description, 
                         event_data, user_id, session_id, processing_time_ms, 
                         error_message, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        RETURNING id
                    """, 
                    document_id, event_type, event_status, event_description,
                    json.dumps(event_data) if event_data else None,
                    user_id, session_id, processing_time_ms, error_message,
                    json.dumps(metadata) if metadata else None)
                    
                    logger.info(f"📝 Logged event: {event_type} for document {document_id} (ID: {event_id})")
                    return str(event_id)
                    
        except Exception as e:
            logger.error(f"❌ Error logging event for document {document_id}: {e}")
            raise
    
    async def get_document_history(
        self,
        document_id: str,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get history for a specific document"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT id, document_id, event_type, event_status, event_description,
                           event_data, user_id, session_id, processing_time_ms, 
                           error_message, metadata, created_at
                    FROM document_hub.document_history
                    WHERE document_id = $1
                """
                params = [document_id]
                
                if event_type:
                    query += " AND event_type = $2"
                    params.append(event_type)
                
                query += " ORDER BY created_at DESC LIMIT $2 OFFSET $3"
                if event_type:
                    params.extend([limit, offset])
                else:
                    params.extend([limit, offset])
                
                rows = await conn.fetch(query, *params)
                
                history = []
                for row in rows:
                    history.append({
                        "id": str(row['id']),
                        "document_id": str(row['document_id']),
                        "event_type": row['event_type'],
                        "event_status": row['event_status'],
                        "event_description": row['event_description'],
                        "event_data": json.loads(row['event_data']) if row['event_data'] else None,
                        "user_id": row['user_id'],
                        "session_id": row['session_id'],
                        "processing_time_ms": row['processing_time_ms'],
                        "error_message": row['error_message'],
                        "metadata": json.loads(row['metadata']) if row['metadata'] else None,
                        "created_at": row['created_at'].isoformat()
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"❌ Error getting history for document {document_id}: {e}")
            raise
    
    async def get_recent_events(
        self,
        limit: int = 50,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent events across all documents"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT h.id, h.document_id, h.event_type, h.event_status, 
                           h.event_description, h.event_data, h.user_id, h.session_id,
                           h.processing_time_ms, h.error_message, h.metadata, h.created_at,
                           d.original_filename
                    FROM document_hub.document_history h
                    LEFT JOIN document_hub.documents d ON h.document_id = d.id
                """
                params = []
                
                if event_type:
                    query += " WHERE h.event_type = $1"
                    params.append(event_type)
                
                query += " ORDER BY h.created_at DESC LIMIT $1"
                if event_type:
                    params.append(limit)
                else:
                    params.append(limit)
                
                rows = await conn.fetch(query, *params)
                
                events = []
                for row in rows:
                    events.append({
                        "id": str(row['id']),
                        "document_id": str(row['document_id']),
                        "document_name": row['original_filename'],
                        "event_type": row['event_type'],
                        "event_status": row['event_status'],
                        "event_description": row['event_description'],
                        "event_data": json.loads(row['event_data']) if row['event_data'] else None,
                        "user_id": row['user_id'],
                        "session_id": row['session_id'],
                        "processing_time_ms": row['processing_time_ms'],
                        "error_message": row['error_message'],
                        "metadata": json.loads(row['metadata']) if row['metadata'] else None,
                        "created_at": row['created_at'].isoformat()
                    })
                
                return events
                
        except Exception as e:
            logger.error(f"❌ Error getting recent events: {e}")
            raise
    
    # Convenience methods for common events
    async def log_upload(
        self,
        document_id: str,
        filename: str,
        file_size: int,
        user_id: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> str:
        """Log document upload event"""
        return await self.log_event(
            document_id=document_id,
            event_type="upload",
            event_description=f"Document uploaded: {filename}",
            event_data={
                "filename": filename,
                "file_size": file_size
            },
            user_id=user_id,
            processing_time_ms=processing_time_ms
        )
    
    async def log_analysis_start(
        self,
        document_id: str,
        analysis_type: str,
        user_id: Optional[str] = None
    ) -> str:
        """Log analysis start event"""
        return await self.log_event(
            document_id=document_id,
            event_type="analysis_start",
            event_description=f"Analysis started: {analysis_type}",
            event_data={
                "analysis_type": analysis_type
            },
            user_id=user_id
        )
    
    async def log_analysis_complete(
        self,
        document_id: str,
        analysis_id: str,
        analysis_type: str,
        confidence_score: float,
        processing_time_ms: int,
        user_id: Optional[str] = None
    ) -> str:
        """Log analysis completion event"""
        return await self.log_event(
            document_id=document_id,
            event_type="analysis_complete",
            event_description=f"Analysis completed: {analysis_type}",
            event_data={
                "analysis_id": analysis_id,
                "analysis_type": analysis_type,
                "confidence_score": confidence_score
            },
            user_id=user_id,
            processing_time_ms=processing_time_ms
        )
    
    async def log_analysis_error(
        self,
        document_id: str,
        analysis_type: str,
        error_message: str,
        user_id: Optional[str] = None
    ) -> str:
        """Log analysis error event"""
        return await self.log_event(
            document_id=document_id,
            event_type="analysis_error",
            event_status="error",
            event_description=f"Analysis failed: {analysis_type}",
            event_data={
                "analysis_type": analysis_type
            },
            user_id=user_id,
            error_message=error_message
        )
    
    async def log_vector_processing(
        self,
        document_id: str,
        chunk_count: int,
        vector_count: int,
        processing_time_ms: int,
        user_id: Optional[str] = None
    ) -> str:
        """Log vector processing event"""
        return await self.log_event(
            document_id=document_id,
            event_type="vector_processing",
            event_description=f"Vector processing completed: {chunk_count} chunks, {vector_count} vectors",
            event_data={
                "chunk_count": chunk_count,
                "vector_count": vector_count
            },
            user_id=user_id,
            processing_time_ms=processing_time_ms
        )
    
    async def log_document_delete(
        self,
        document_id: str,
        filename: str,
        user_id: Optional[str] = None
    ) -> str:
        """Log document deletion event"""
        return await self.log_event(
            document_id=document_id,
            event_type="delete",
            event_description=f"Document deleted: {filename}",
            event_data={
                "filename": filename
            },
            user_id=user_id
        )

