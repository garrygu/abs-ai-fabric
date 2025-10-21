"""
Document Management Service for PostgreSQL
Provides CRUD operations for documents and analysis results
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import asyncpg
import hashlib
import mimetypes
import os


class DocumentService:
    """Service for managing documents and analysis results in PostgreSQL"""
    
    def __init__(self, database_url: str = "postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub"):
        self.database_url = database_url
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            print("✅ Document service connected to PostgreSQL")
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    # ==================== DOCUMENT CRUD OPERATIONS ====================
    
    async def create_document(
        self,
        file_path: str,
        original_filename: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new document record
        
        Args:
            file_path: Path to the uploaded file
            original_filename: Original filename from upload
            metadata: Optional metadata dictionary
            user_id: Optional user ID who uploaded the document
            
        Returns:
            Document record with generated ID
        """
        try:
            file_path_obj = Path(file_path)
            
            # Get file information
            file_size = file_path_obj.stat().st_size
            file_type = file_path_obj.suffix.lower()
            mime_type = mimetypes.guess_type(str(file_path_obj))[0]
            
            # Generate unique filename
            file_hash = hashlib.sha256(file_path_obj.read_bytes()).hexdigest()
            unique_filename = f"{file_hash[:16]}_{original_filename}"
            
            # Prepare metadata
            doc_metadata = {
                "file_hash": file_hash,
                "original_filename": original_filename,
                "upload_source": "contract-reviewer-v2",
                **(metadata or {})
            }
            
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Insert document record
                    document_id = await conn.fetchval("""
                        INSERT INTO document_hub.documents 
                        (filename, original_filename, file_path, file_size, file_type, 
                         mime_type, metadata, status)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        RETURNING id
                    """, unique_filename, original_filename, str(file_path), 
                    file_size, file_type, mime_type, json.dumps(doc_metadata), 'uploaded')
                    
                    # Log the creation
                    await conn.execute("""
                        INSERT INTO document_hub.audit_logs 
                        (user_id, action, resource_type, resource_id, details)
                        VALUES ($1, $2, $3, $4, $5)
                    """, user_id, 'document_created', 'document', str(document_id), 
                    json.dumps({"filename": original_filename, "file_size": file_size}))
                    
                    # Retrieve the created document within the same transaction
                    row = await conn.fetchrow("""
                        SELECT id, filename, original_filename, file_path, file_size,
                               file_type, mime_type, upload_timestamp, analysis_timestamp,
                               status, metadata, created_at, updated_at
                        FROM document_hub.documents
                        WHERE id = $1
                    """, document_id)
                    
                    if row:
                        return self._row_to_dict(row)
                    else:
                        return None
                    
        except Exception as e:
            print(f"❌ Error creating document: {e}")
            raise
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by its ID"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, filename, original_filename, file_path, file_size,
                           file_type, mime_type, upload_timestamp, analysis_timestamp,
                           status, metadata, created_at, updated_at
                    FROM document_hub.documents
                    WHERE id = $1
                """, document_id)
                
                if row:
                    return self._row_to_dict(row)
                return None
                
        except Exception as e:
            print(f"❌ Error getting document {document_id}: {e}")
            raise
    
    async def get_documents(
        self,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        order_by: str = "upload_timestamp",
        order_direction: str = "DESC"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get a list of documents with pagination
        
        Returns:
            Tuple of (documents_list, total_count)
        """
        try:
            async with self.pool.acquire() as conn:
                # Build WHERE clause
                where_conditions = []
                params = []
                param_count = 0
                
                if status:
                    param_count += 1
                    where_conditions.append(f"status = ${param_count}")
                    params.append(status)
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM document_hub.documents {where_clause}"
                total_count = await conn.fetchval(count_query, *params)
                
                # Get documents with pagination
                param_count += 1
                order_clause = f"ORDER BY {order_by} {order_direction}"
                limit_clause = f"LIMIT ${param_count}"
                params.append(limit)
                
                param_count += 1
                offset_clause = f"OFFSET ${param_count}"
                params.append(offset)
                
                query = f"""
                    SELECT id, filename, original_filename, file_path, file_size,
                           file_type, mime_type, upload_timestamp, analysis_timestamp,
                           status, metadata, created_at, updated_at
                    FROM document_hub.documents
                    {where_clause}
                    {order_clause}
                    {limit_clause}
                    {offset_clause}
                """
                
                rows = await conn.fetch(query, *params)
                documents = [self._row_to_dict(row) for row in rows]
                
                return documents, total_count
                
        except Exception as e:
            print(f"❌ Error getting documents: {e}")
            raise
    
    async def update_document(
        self,
        document_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a document record
        
        Args:
            document_id: ID of document to update
            updates: Dictionary of fields to update
            user_id: Optional user ID making the update
            
        Returns:
            Updated document record or None if not found
        """
        try:
            # Validate allowed update fields
            allowed_fields = {
                'status', 'metadata', 'analysis_timestamp'
            }
            
            update_fields = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not update_fields:
                raise ValueError("No valid fields to update")
            
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Build SET clause
                    set_clauses = []
                    params = []
                    param_count = 0
                    
                    for field, value in update_fields.items():
                        param_count += 1
                        if field == 'metadata' and isinstance(value, dict):
                            set_clauses.append(f"{field} = ${param_count}")
                            params.append(json.dumps(value))
                        else:
                            set_clauses.append(f"{field} = ${param_count}")
                            params.append(value)
                    
                    param_count += 1
                    params.append(document_id)
                    
                    # Update the document
                    set_clause = ", ".join(set_clauses)
                    update_query = f"""
                        UPDATE document_hub.documents
                        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ${param_count}
                        RETURNING id
                    """
                    
                    updated_id = await conn.fetchval(update_query, *params)
                    
                    if updated_id:
                        # Log the update
                        await conn.execute("""
                            INSERT INTO document_hub.audit_logs 
                            (user_id, action, resource_type, resource_id, details)
                            VALUES ($1, $2, $3, $4, $5)
                        """, user_id, 'document_updated', 'document', str(document_id), 
                        json.dumps({"updated_fields": list(update_fields.keys())}))
                        
                        return await self.get_document_by_id(document_id)
                    
                    return None
                    
        except Exception as e:
            print(f"❌ Error updating document {document_id}: {e}")
            raise
    
    async def delete_document(
        self,
        document_id: str,
        user_id: Optional[str] = None,
        delete_file: bool = True
    ) -> bool:
        """
        Delete a document and optionally its file
        
        Args:
            document_id: ID of document to delete
            user_id: Optional user ID making the deletion
            delete_file: Whether to delete the physical file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Get document info before deletion
                    document = await self.get_document_by_id(document_id)
                    if not document:
                        return False
                    
                    # Delete the document (cascade will handle related records)
                    deleted_count = await conn.execute("""
                        DELETE FROM document_hub.documents WHERE id = $1
                    """, document_id)
                    
                    if deleted_count == "DELETE 1":
                        # Log the deletion
                        await conn.execute("""
                            INSERT INTO document_hub.audit_logs 
                            (user_id, action, resource_type, resource_id, details)
                            VALUES ($1, $2, $3, $4, $5)
                        """, user_id, 'document_deleted', 'document', str(document_id), 
                        json.dumps({"filename": document['original_filename']}))
                        
                        # Delete physical file if requested
                        if delete_file and document['file_path']:
                            try:
                                file_path = Path(document['file_path'])
                                if file_path.exists():
                                    file_path.unlink()
                                    print(f"🗑️ Deleted file: {file_path}")
                            except Exception as e:
                                print(f"⚠️ Could not delete file {document['file_path']}: {e}")
                        
                        return True
                    
                    return False
                    
        except Exception as e:
            print(f"❌ Error deleting document {document_id}: {e}")
            raise
    
    # ==================== ANALYSIS RESULTS CRUD OPERATIONS ====================
    
    async def create_analysis_result(
        self,
        document_id: str,
        analysis_type: str,
        analysis_data: Dict[str, Any],
        model_used: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new analysis result"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Insert analysis result and get the full record
                    analysis_row = await conn.fetchrow("""
                        INSERT INTO document_hub.analysis_results
                        (document_id, analysis_type, analysis_data, model_used, processing_time_ms)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING id, document_id, analysis_type, analysis_data,
                                 analysis_timestamp, model_used, processing_time_ms,
                                 status, metadata, created_at, updated_at
                    """, document_id, analysis_type, json.dumps(analysis_data), 
                    model_used, processing_time_ms)
                    
                    if not analysis_row:
                        print(f"❌ Failed to insert analysis result for document {document_id}")
                        return None
                    
                    analysis_id = analysis_row['id']
                    
                    # Update document status and analysis timestamp
                    await conn.execute("""
                        UPDATE document_hub.documents
                        SET status = 'analyzed', analysis_timestamp = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """, document_id)
                    
                    # Log the analysis
                    await conn.execute("""
                        INSERT INTO document_hub.audit_logs 
                        (user_id, action, resource_type, resource_id, details)
                        VALUES ($1, $2, $3, $4, $5)
                    """, user_id, 'analysis_created', 'analysis_result', str(analysis_id), 
                    json.dumps({"analysis_type": analysis_type, "model_used": model_used}))
                    
                    # Return the analysis result directly from the INSERT
                    return self._row_to_dict(analysis_row)
                    
        except Exception as e:
            print(f"❌ Error creating analysis result: {e}")
            raise
    
    async def get_analysis_result_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get an analysis result by its ID"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT id, document_id, analysis_type, analysis_data,
                           analysis_timestamp, model_used, processing_time_ms,
                           status, metadata, created_at, updated_at
                    FROM document_hub.analysis_results
                    WHERE id = $1
                """, analysis_id)
                
                if row:
                    return self._row_to_dict(row)
                return None
                
        except Exception as e:
            print(f"❌ Error getting analysis result {analysis_id}: {e}")
            raise
    
    async def get_analysis_results_by_document(
        self,
        document_id: str,
        analysis_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all analysis results for a document"""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT id, document_id, analysis_type, analysis_data,
                           analysis_timestamp, model_used, processing_time_ms,
                           status, metadata, created_at, updated_at
                    FROM document_hub.analysis_results
                    WHERE document_id = $1
                """
                params = [document_id]
                
                if analysis_type:
                    query += " AND analysis_type = $2"
                    params.append(analysis_type)
                
                query += " ORDER BY analysis_timestamp DESC"
                
                rows = await conn.fetch(query, *params)
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            print(f"❌ Error getting analysis results for document {document_id}: {e}")
            raise
    
    async def delete_analysis_result(
        self,
        analysis_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Delete an analysis result"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Get analysis info before deletion
                    analysis = await self.get_analysis_result_by_id(analysis_id)
                    if not analysis:
                        return False
                    
                    # Delete the analysis result
                    deleted_count = await conn.execute("""
                        DELETE FROM document_hub.analysis_results WHERE id = $1
                    """, analysis_id)
                    
                    if deleted_count == "DELETE 1":
                        # Log the deletion
                        await conn.execute("""
                            INSERT INTO document_hub.audit_logs 
                            (user_id, action, resource_type, resource_id, details)
                            VALUES ($1, $2, $3, $4, $5)
                        """, user_id, 'analysis_deleted', 'analysis_result', str(analysis_id), 
                        json.dumps({"analysis_type": analysis['analysis_type']}))
                        
                        return True
                    
                    return False
                    
        except Exception as e:
            print(f"❌ Error deleting analysis result {analysis_id}: {e}")
            raise
    
    async def update_analysis_result(
        self,
        analysis_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an analysis result"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Get current analysis
                    current_analysis = await self.get_analysis_result_by_id(analysis_id)
                    if not current_analysis:
                        return None
                    
                    # Build update query dynamically
                    set_clauses = []
                    values = []
                    param_count = 1
                    
                    for key, value in updates.items():
                        if key == "analysis_data":
                            set_clauses.append(f"analysis_data = ${param_count}")
                            values.append(json.dumps(value))
                        elif key == "metadata":
                            set_clauses.append(f"metadata = ${param_count}")
                            values.append(json.dumps(value))
                        elif key == "status":
                            set_clauses.append(f"status = ${param_count}")
                            values.append(value)
                        elif key == "processing_time_ms":
                            set_clauses.append(f"processing_time_ms = ${param_count}")
                            values.append(value)
                        elif key == "model_used":
                            set_clauses.append(f"model_used = ${param_count}")
                            values.append(value)
                        param_count += 1
                    
                    if not set_clauses:
                        return current_analysis
                    
                    # Add updated_at timestamp
                    set_clauses.append(f"updated_at = ${param_count}")
                    values.append(datetime.now())
                    param_count += 1
                    
                    # Add analysis_id for WHERE clause
                    values.append(analysis_id)
                    
                    # Execute update
                    query = f"""
                        UPDATE document_hub.analysis_results 
                        SET {', '.join(set_clauses)}
                        WHERE id = ${param_count}
                        RETURNING *
                    """
                    
                    row = await conn.fetchrow(query, *values)
                    
                    if row:
                        # Log the update
                        await conn.execute("""
                            INSERT INTO document_hub.audit_logs 
                            (user_id, action, resource_type, resource_id, details)
                            VALUES ($1, $2, $3, $4, $5)
                        """, user_id, 'analysis_updated', 'analysis_result', str(analysis_id), 
                        json.dumps({"updated_fields": list(updates.keys())}))
                        
                        return self._row_to_dict(row)
                    
                    return None
                    
        except Exception as e:
            print(f"❌ Error updating analysis result {analysis_id}: {e}")
            raise
    
    # ==================== UTILITY METHODS ====================
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """Get document statistics"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM document_hub.document_stats")
                return self._row_to_dict(row) if row else {}
        except Exception as e:
            print(f"❌ Error getting document statistics: {e}")
            return {}
    
    async def get_analysis_statistics(self) -> List[Dict[str, Any]]:
        """Get analysis statistics by type"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM document_hub.analysis_stats")
                return [self._row_to_dict(row) for row in rows]
        except Exception as e:
            print(f"❌ Error getting analysis statistics: {e}")
            return []
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary"""
        if not row:
            return {}
        
        result = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[key] = str(value)
            elif key in ['metadata', 'details', 'analysis_data'] and isinstance(value, str):
                # Parse JSON fields
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value
            else:
                result[key] = value
        
        return result


# ==================== EXAMPLE USAGE ====================

async def example_usage():
    """Example of how to use the DocumentService"""
    
    # Initialize service
    doc_service = DocumentService()
    await doc_service.initialize()
    
    try:
        # Create a document
        document = await doc_service.create_document(
            file_path="/path/to/contract.pdf",
            original_filename="contract.pdf",
            metadata={"client": "ACME Corp", "contract_type": "NDA"}
        )
        print(f"Created document: {document['id']}")
        
        # Get documents with pagination
        documents, total = await doc_service.get_documents(limit=10, offset=0)
        print(f"Found {total} documents")
        
        # Create analysis result
        analysis = await doc_service.create_analysis_result(
            document_id=document['id'],
            analysis_type="contract_review",
            analysis_data={"summary": "Contract analysis complete", "risks": []},
            model_used="llama3.2:3b",
            processing_time_ms=1500
        )
        print(f"Created analysis: {analysis['id']}")
        
        # Get analysis results for document
        analyses = await doc_service.get_analysis_results_by_document(document['id'])
        print(f"Found {len(analyses)} analyses for document")
        
    finally:
        await doc_service.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
