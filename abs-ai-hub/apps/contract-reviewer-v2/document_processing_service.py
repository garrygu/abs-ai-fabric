"""
Document Processing Service
Integrates text extraction, chunking, and vector storage for documents
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import fitz  # PyMuPDF
from docx import Document as DocxDocument
import logging

from vector_storage_service import VectorStorageService
from document_service import DocumentService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Service for processing documents and storing them in vector database"""
    
    def __init__(
        self,
        vector_service: VectorStorageService,
        doc_service: DocumentService,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunk_type: str = "paragraph"
    ):
        self.vector_service = vector_service
        self.doc_service = doc_service
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunk_type = chunk_type
    
    async def initialize(self):
        """Initialize the document processing service"""
        try:
            await self.vector_service.initialize()
            logger.info("✅ Document processing service initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize document processing service: {e}")
            raise
    
    # ==================== TEXT EXTRACTION ====================
    
    def extract_text_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from various file formats
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            file_path_obj = Path(file_path)
            file_extension = file_path_obj.suffix.lower()
            
            logger.info(f"Extracting text from {file_path} (type: {file_extension})")
            
            if file_extension == '.pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_text_from_docx(file_path)
            elif file_extension == '.txt':
                return self._extract_text_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
                
        except Exception as e:
            logger.error(f"❌ Error extracting text from {file_path}: {e}")
            raise
    
    def _extract_text_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF file"""
        try:
            doc = fitz.open(file_path)
            text_content = ""
            page_texts = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                text_content += page_text + "\n"
                page_texts.append({
                    "page_number": page_num + 1,
                    "text": page_text,
                    "word_count": len(page_text.split())
                })
            
            doc.close()
            
            return {
                "text": text_content.strip(),
                "page_count": doc.page_count,
                "page_texts": page_texts,
                "word_count": len(text_content.split()),
                "character_count": len(text_content),
                "extraction_method": "pymupdf"
            }
            
        except Exception as e:
            logger.error(f"❌ Error extracting text from PDF {file_path}: {e}")
            raise
    
    def _extract_text_from_docx(self, file_path: str) -> Dict[str, Any]:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(file_path)
            text_content = ""
            paragraph_texts = []
            
            for para_num, paragraph in enumerate(doc.paragraphs):
                para_text = paragraph.text
                if para_text.strip():  # Skip empty paragraphs
                    text_content += para_text + "\n"
                    paragraph_texts.append({
                        "paragraph_number": para_num + 1,
                        "text": para_text,
                        "word_count": len(para_text.split())
                    })
            
            return {
                "text": text_content.strip(),
                "paragraph_count": len(paragraph_texts),
                "paragraph_texts": paragraph_texts,
                "word_count": len(text_content.split()),
                "character_count": len(text_content),
                "extraction_method": "python-docx"
            }
            
        except Exception as e:
            logger.error(f"❌ Error extracting text from DOCX {file_path}: {e}")
            raise
    
    def _extract_text_from_txt(self, file_path: str) -> Dict[str, Any]:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text_content = file.read()
            
            # Split into lines for basic structure
            lines = text_content.split('\n')
            line_texts = []
            
            for line_num, line in enumerate(lines):
                if line.strip():  # Skip empty lines
                    line_texts.append({
                        "line_number": line_num + 1,
                        "text": line,
                        "word_count": len(line.split())
                    })
            
            return {
                "text": text_content.strip(),
                "line_count": len(line_texts),
                "line_texts": line_texts,
                "word_count": len(text_content.split()),
                "character_count": len(text_content),
                "extraction_method": "plain_text"
            }
            
        except Exception as e:
            logger.error(f"❌ Error extracting text from TXT {file_path}: {e}")
            raise
    
    # ==================== DOCUMENT PROCESSING ====================
    
    async def process_document(
        self,
        document_id: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a document: extract text, chunk, and store in vector database
        
        Args:
            document_id: ID of the document
            file_path: Path to the document file
            metadata: Additional metadata
            
        Returns:
            Processing results
        """
        try:
            logger.info(f"Processing document {document_id}: {file_path}")
            
            # Extract text from file
            extraction_result = self.extract_text_from_file(file_path)
            
            # Chunk the text
            chunks = self.vector_service.chunk_text(
                text=extraction_result["text"],
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                chunk_type=self.chunk_type
            )
            
            # Prepare metadata for vector storage
            vector_metadata = {
                "filename": Path(file_path).name,
                "file_path": file_path,
                "extraction_method": extraction_result["extraction_method"],
                "word_count": extraction_result["word_count"],
                "character_count": extraction_result["character_count"],
                "chunk_count": len(chunks),
                "processed_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Store chunks in vector database
            vector_ids = await self.vector_service.store_document_chunks(
                document_id=document_id,
                chunks=chunks,
                metadata=vector_metadata
            )
            
            # Update document metadata in PostgreSQL
            await self.doc_service.update_document(
                document_id=document_id,
                updates={
                    "metadata": {
                        **vector_metadata,
                        "vector_ids": vector_ids,
                        "processing_status": "completed"
                    }
                }
            )
            
            processing_result = {
                "document_id": document_id,
                "file_path": file_path,
                "extraction_result": extraction_result,
                "chunks_created": len(chunks),
                "vector_ids": vector_ids,
                "processing_status": "completed",
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Processed document {document_id}: {len(chunks)} chunks stored")
            return processing_result
            
        except Exception as e:
            logger.error(f"❌ Error processing document {document_id}: {e}")
            
            # Update document status to failed
            try:
                await self.doc_service.update_document(
                    document_id=document_id,
                    updates={
                        "metadata": {
                            "processing_status": "failed",
                            "error": str(e),
                            "failed_at": datetime.now().isoformat()
                        }
                    }
                )
            except:
                pass
            
            raise
    
    async def reprocess_document(
        self,
        document_id: str,
        file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Reprocess a document (update existing chunks)
        
        Args:
            document_id: ID of the document
            file_path: Path to the document file (if None, get from database)
            metadata: Additional metadata
            
        Returns:
            Processing results
        """
        try:
            logger.info(f"Reprocessing document {document_id}")
            
            # Get document info if file_path not provided
            if not file_path:
                document = await self.doc_service.get_document_by_id(document_id)
                if not document:
                    raise ValueError(f"Document {document_id} not found")
                file_path = document["file_path"]
            
            # Extract text from file
            extraction_result = self.extract_text_from_file(file_path)
            
            # Chunk the text
            chunks = self.vector_service.chunk_text(
                text=extraction_result["text"],
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                chunk_type=self.chunk_type
            )
            
            # Prepare metadata for vector storage
            vector_metadata = {
                "filename": Path(file_path).name,
                "file_path": file_path,
                "extraction_method": extraction_result["extraction_method"],
                "word_count": extraction_result["word_count"],
                "character_count": extraction_result["character_count"],
                "chunk_count": len(chunks),
                "reprocessed_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Update chunks in vector database
            vector_ids = await self.vector_service.update_document_chunks(
                document_id=document_id,
                chunks=chunks,
                metadata=vector_metadata
            )
            
            # Update document metadata in PostgreSQL
            await self.doc_service.update_document(
                document_id=document_id,
                updates={
                    "metadata": {
                        **vector_metadata,
                        "vector_ids": vector_ids,
                        "processing_status": "reprocessed"
                    }
                }
            )
            
            processing_result = {
                "document_id": document_id,
                "file_path": file_path,
                "extraction_result": extraction_result,
                "chunks_updated": len(chunks),
                "vector_ids": vector_ids,
                "processing_status": "reprocessed",
                "reprocessed_at": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Reprocessed document {document_id}: {len(chunks)} chunks updated")
            return processing_result
            
        except Exception as e:
            logger.error(f"❌ Error reprocessing document {document_id}: {e}")
            raise
    
    async def delete_document_vectors(self, document_id: str) -> bool:
        """
        Delete all vectors for a document
        
        Args:
            document_id: ID of the document
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting vectors for document {document_id}")
            
            # Delete from vector database
            await self.vector_service.delete_document_chunks(document_id)
            
            # Update document metadata in PostgreSQL
            await self.doc_service.update_document(
                document_id=document_id,
                updates={
                    "metadata": {
                        "processing_status": "deleted",
                        "deleted_at": datetime.now().isoformat()
                    }
                }
            )
            
            logger.info(f"✅ Deleted vectors for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting vectors for document {document_id}: {e}")
            raise
    
    # ==================== BATCH PROCESSING ====================
    
    async def process_multiple_documents(
        self,
        document_files: List[Tuple[str, str]],  # (document_id, file_path)
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents in batch
        
        Args:
            document_files: List of (document_id, file_path) tuples
            metadata: Additional metadata for all documents
            
        Returns:
            List of processing results
        """
        try:
            logger.info(f"Processing {len(document_files)} documents in batch")
            
            results = []
            for document_id, file_path in document_files:
                try:
                    result = await self.process_document(
                        document_id=document_id,
                        file_path=file_path,
                        metadata=metadata
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"❌ Error processing document {document_id}: {e}")
                    results.append({
                        "document_id": document_id,
                        "file_path": file_path,
                        "processing_status": "failed",
                        "error": str(e)
                    })
            
            successful = len([r for r in results if r.get("processing_status") == "completed"])
            logger.info(f"✅ Batch processing complete: {successful}/{len(document_files)} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in batch processing: {e}")
            raise
    
    # ==================== SEARCH AND SIMILARITY ====================
    
    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents using semantic search
        
        Args:
            query: Search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Additional filters
            
        Returns:
            List of search results
        """
        try:
            logger.info(f"Searching documents with query: {query}")
            
            # Perform semantic search
            search_results = await self.vector_service.semantic_search(
                query=query,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters
            )
            
            # Enhance results with document metadata
            enhanced_results = []
            for result in search_results:
                try:
                    # Get document metadata from PostgreSQL
                    document = await self.doc_service.get_document_by_id(result["document_id"])
                    
                    enhanced_result = {
                        **result,
                        "document_metadata": document,
                        "filename": document.get("original_filename", "Unknown"),
                        "upload_timestamp": document.get("upload_timestamp"),
                        "file_size": document.get("file_size"),
                        "file_type": document.get("file_type")
                    }
                    
                    enhanced_results.append(enhanced_result)
                    
                except Exception as e:
                    logger.warning(f"Could not enhance result for document {result['document_id']}: {e}")
                    enhanced_results.append(result)
            
            logger.info(f"✅ Found {len(enhanced_results)} search results")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"❌ Error searching documents: {e}")
            raise
    
    async def find_similar_documents(
        self,
        document_id: str,
        limit: int = 5,
        score_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Find documents similar to a given document
        
        Args:
            document_id: ID of the reference document
            limit: Maximum number of similar documents
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar documents
        """
        try:
            logger.info(f"Finding documents similar to {document_id}")
            
            # Find similar documents using vector service
            similar_docs = await self.vector_service.find_similar_documents(
                document_id=document_id,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Enhance results with document metadata
            enhanced_results = []
            for doc in similar_docs:
                try:
                    # Get document metadata from PostgreSQL
                    document = await self.doc_service.get_document_by_id(doc["document_id"])
                    
                    enhanced_result = {
                        **doc,
                        "document_metadata": document,
                        "filename": document.get("original_filename", "Unknown"),
                        "upload_timestamp": document.get("upload_timestamp"),
                        "file_size": document.get("file_size"),
                        "file_type": document.get("file_type")
                    }
                    
                    enhanced_results.append(enhanced_result)
                    
                except Exception as e:
                    logger.warning(f"Could not enhance similar document {doc['document_id']}: {e}")
                    enhanced_results.append(doc)
            
            logger.info(f"✅ Found {len(enhanced_results)} similar documents")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"❌ Error finding similar documents: {e}")
            raise
    
    # ==================== STATISTICS ====================
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            # Get vector database stats
            vector_stats = await self.vector_service.get_collection_stats()
            
            # Get document stats from PostgreSQL
            doc_stats = await self.doc_service.get_document_statistics()
            
            return {
                "vector_database": vector_stats,
                "documents": doc_stats,
                "processing_config": {
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "chunk_type": self.chunk_type
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting processing stats: {e}")
            raise
    
    async def close(self):
        """Close the document processing service"""
        try:
            await self.vector_service.close()
            logger.info("✅ Document processing service closed")
        except Exception as e:
            logger.error(f"⚠️ Error closing document processing service: {e}")


# ==================== EXAMPLE USAGE ====================

async def example_usage():
    """Example of how to use the DocumentProcessingService"""
    
    # Initialize services
    from document_service import DocumentService
    
    vector_service = VectorStorageService()
    doc_service = DocumentService()
    processing_service = DocumentProcessingService(vector_service, doc_service)
    
    await processing_service.initialize()
    
    try:
        # Process a sample document
        document_id = "sample-doc-001"
        file_path = "/path/to/sample.pdf"
        
        result = await processing_service.process_document(
            document_id=document_id,
            file_path=file_path,
            metadata={"client": "Sample Client", "document_type": "Contract"}
        )
        
        print(f"Processed document: {result['chunks_created']} chunks created")
        
        # Search documents
        search_results = await processing_service.search_documents(
            query="confidentiality agreement",
            limit=5
        )
        
        print(f"Found {len(search_results)} search results")
        
        # Find similar documents
        similar_docs = await processing_service.find_similar_documents(
            document_id=document_id,
            limit=3
        )
        
        print(f"Found {len(similar_docs)} similar documents")
        
    finally:
        await processing_service.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
