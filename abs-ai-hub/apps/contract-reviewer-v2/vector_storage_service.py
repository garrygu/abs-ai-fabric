"""
Qdrant Vector Storage Service
Comprehensive vector database integration for semantic search and document analysis
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStorageService:
    """Service for managing vector storage in Qdrant"""
    
    def __init__(
        self,
        qdrant_host: str = "qdrant",
        qdrant_port: int = 6333,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "legal_documents"
    ):
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.embedding_model = SentenceTransformer(embedding_model)
        self.collection_name = collection_name
        self.embedding_dimension = 384  # Dimension for all-MiniLM-L6-v2
        
    async def initialize(self):
        """Initialize the vector storage service"""
        try:
            # Test Qdrant connection
            collections = self.qdrant_client.get_collections()
            logger.info(f"✅ Connected to Qdrant. Found {len(collections.collections)} collections")
            
            # Create collection if it doesn't exist
            await self.create_collection()
            
            logger.info("✅ Vector storage service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector storage service: {e}")
            raise
    
    async def create_collection(self):
        """Create Qdrant collection for legal documents"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)
            
            if not collection_exists:
                logger.info(f"Creating collection: {self.collection_name}")
                
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                
                logger.info(f"✅ Created collection: {self.collection_name}")
            else:
                logger.info(f"✅ Collection already exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Error creating collection: {e}")
            raise
    
    # ==================== TEXT CHUNKING ====================
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunk_type: str = "paragraph"
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks for vector storage
        
        Args:
            text: Input text to chunk
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
            chunk_type: Type of chunking (paragraph, sentence, fixed)
            
        Returns:
            List of text chunks with metadata
        """
        try:
            chunks = []
            
            if chunk_type == "paragraph":
                chunks = self._chunk_by_paragraphs(text, chunk_size, chunk_overlap)
            elif chunk_type == "sentence":
                chunks = self._chunk_by_sentences(text, chunk_size, chunk_overlap)
            elif chunk_type == "fixed":
                chunks = self._chunk_by_fixed_size(text, chunk_size, chunk_overlap)
            else:
                raise ValueError(f"Unknown chunk type: {chunk_type}")
            
            logger.info(f"Created {len(chunks)} chunks from text")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error chunking text: {e}")
            raise
    
    def _chunk_by_paragraphs(self, text: str, chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
        """Chunk text by paragraphs"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) <= chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "chunk_index": chunk_index,
                        "chunk_type": "paragraph",
                        "start_position": len(text) - len(current_chunk),
                        "end_position": len(text),
                        "word_count": len(current_chunk.split())
                    })
                    chunk_index += 1
                
                current_chunk = paragraph + "\n\n"
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "chunk_index": chunk_index,
                "chunk_type": "paragraph",
                "start_position": len(text) - len(current_chunk),
                "end_position": len(text),
                "word_count": len(current_chunk.split())
            })
        
        return chunks
    
    def _chunk_by_sentences(self, text: str, chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
        """Chunk text by sentences"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "chunk_index": chunk_index,
                        "chunk_type": "sentence",
                        "start_position": len(text) - len(current_chunk),
                        "end_position": len(text),
                        "word_count": len(current_chunk.split())
                    })
                    chunk_index += 1
                
                current_chunk = sentence + ". "
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "chunk_index": chunk_index,
                "chunk_type": "sentence",
                "start_position": len(text) - len(current_chunk),
                "end_position": len(text),
                "word_count": len(current_chunk.split())
            })
        
        return chunks
    
    def _chunk_by_fixed_size(self, text: str, chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
        """Chunk text by fixed size"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]
            
            chunks.append({
                "text": chunk_text,
                "chunk_index": len(chunks),
                "chunk_type": "fixed",
                "start_position": start,
                "end_position": end,
                "word_count": len(chunk_text.split())
            })
            
            start = end - chunk_overlap
        
        return chunks
    
    # ==================== EMBEDDING GENERATION ====================
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            
            # Convert to list of lists
            embeddings_list = [embedding.tolist() for embedding in embeddings]
            
            logger.info(f"✅ Generated {len(embeddings_list)} embeddings")
            return embeddings_list
            
        except Exception as e:
            logger.error(f"❌ Error generating embeddings: {e}")
            raise
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector
        """
        try:
            embedding = self.embedding_model.encode([query], convert_to_tensor=False)
            return embedding[0].tolist()
            
        except Exception as e:
            logger.error(f"❌ Error generating query embedding: {e}")
            raise
    
    # ==================== VECTOR STORAGE ====================
    
    async def store_document_chunks(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Store document chunks as vectors in Qdrant
        
        Args:
            document_id: ID of the document
            chunks: List of text chunks
            metadata: Additional metadata
            
        Returns:
            List of vector IDs
        """
        try:
            logger.info(f"Storing {len(chunks)} chunks for document {document_id}")
            
            # Extract texts for embedding generation
            texts = [chunk["text"] for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Prepare points for Qdrant
            points = []
            vector_ids = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = str(uuid.uuid4())
                vector_ids.append(vector_id)
                
                # Prepare payload
                payload = {
                    "document_id": document_id,
                    "chunk_index": chunk["chunk_index"],
                    "chunk_type": chunk["chunk_type"],
                    "chunk_text": chunk["text"],
                    "start_position": chunk["start_position"],
                    "end_position": chunk["end_position"],
                    "word_count": chunk["word_count"],
                    "created_at": datetime.now().isoformat(),
                    **(metadata or {})
                }
                
                # Ensure embedding is a proper list of floats (Qdrant requirement)
                embedding_vector = list(embedding) if isinstance(embedding, (list, tuple)) else embedding
                
                # Create point
                point = PointStruct(
                    id=vector_id,
                    vector=embedding_vector,
                    payload=payload
                )
                
                points.append(point)
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"✅ Stored {len(points)} vectors for document {document_id}")
            return vector_ids
            
        except Exception as e:
            logger.error(f"❌ Error storing document chunks: {e}")
            raise
    
    async def update_document_chunks(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Update document chunks (delete old, store new)
        
        Args:
            document_id: ID of the document
            chunks: List of new text chunks
            metadata: Additional metadata
            
        Returns:
            List of new vector IDs
        """
        try:
            logger.info(f"Updating chunks for document {document_id}")
            
            # Delete existing chunks for this document
            await self.delete_document_chunks(document_id)
            
            # Store new chunks
            vector_ids = await self.store_document_chunks(document_id, chunks, metadata)
            
            logger.info(f"✅ Updated chunks for document {document_id}")
            return vector_ids
            
        except Exception as e:
            logger.error(f"❌ Error updating document chunks: {e}")
            raise
    
    async def delete_document_chunks(self, document_id: str) -> bool:
        """
        Delete all chunks for a document
        
        Args:
            document_id: ID of the document
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Deleting chunks for document {document_id}")
            
            # Delete points with matching document_id
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
            )
            
            logger.info(f"✅ Deleted chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting document chunks: {e}")
            raise
    
    # ==================== SEMANTIC SEARCH ====================
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search
        
        Args:
            query: Search query text
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Additional filters
            
        Returns:
            List of search results
        """
        try:
            logger.info(f"Performing semantic search for: {query}")
            
            # Generate query embedding
            query_embedding = self.generate_query_embedding(query)
            
            # Prepare search filter
            search_filter = None
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                
                if filter_conditions:
                    search_filter = models.Filter(must=filter_conditions)
            
            # Perform search
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "vector_id": result.id,
                    "score": result.score,
                    "document_id": result.payload.get("document_id"),
                    "chunk_text": result.payload.get("chunk_text"),
                    "chunk_index": result.payload.get("chunk_index"),
                    "chunk_type": result.payload.get("chunk_type"),
                    "start_position": result.payload.get("start_position"),
                    "end_position": result.payload.get("end_position"),
                    "word_count": result.payload.get("word_count"),
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["document_id", "chunk_text", "chunk_index", 
                                          "chunk_type", "start_position", "end_position", "word_count"]}
                })
            
            logger.info(f"✅ Found {len(results)} semantic search results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error performing semantic search: {e}")
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
            
            # Get a representative chunk from the document
            document_chunks = await self.get_document_chunks(document_id, limit=1)
            
            if not document_chunks:
                logger.warning(f"No chunks found for document {document_id}")
                return []
            
            # Use the first chunk as query
            query_text = document_chunks[0]["chunk_text"]
            
            # Perform semantic search
            search_results = await self.semantic_search(
                query=query_text,
                limit=limit * 2,  # Get more results to filter
                score_threshold=score_threshold
            )
            
            # Filter out the same document and group by document
            similar_docs = {}
            for result in search_results:
                doc_id = result["document_id"]
                if doc_id != document_id:
                    if doc_id not in similar_docs:
                        similar_docs[doc_id] = {
                            "document_id": doc_id,
                            "max_score": result["score"],
                            "chunks": []
                        }
                    similar_docs[doc_id]["chunks"].append(result)
            
            # Sort by max score and limit results
            similar_docs_list = sorted(
                similar_docs.values(),
                key=lambda x: x["max_score"],
                reverse=True
            )[:limit]
            
            logger.info(f"✅ Found {len(similar_docs_list)} similar documents")
            return similar_docs_list
            
        except Exception as e:
            logger.error(f"❌ Error finding similar documents: {e}")
            raise
    
    # ==================== DOCUMENT MANAGEMENT ====================
    
    async def get_document_chunks(
        self,
        document_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document
        
        Args:
            document_id: ID of the document
            limit: Maximum number of chunks to return
            
        Returns:
            List of document chunks
        """
        try:
            logger.info(f"Getting chunks for document {document_id}")
            
            # Search for chunks with matching document_id
            search_results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=limit or 1000
            )
            
            # Format results
            chunks = []
            for point in search_results[0]:
                chunks.append({
                    "vector_id": point.id,
                    "document_id": point.payload.get("document_id"),
                    "chunk_text": point.payload.get("chunk_text"),
                    "chunk_index": point.payload.get("chunk_index"),
                    "chunk_type": point.payload.get("chunk_type"),
                    "start_position": point.payload.get("start_position"),
                    "end_position": point.payload.get("end_position"),
                    "word_count": point.payload.get("word_count"),
                    "metadata": {k: v for k, v in point.payload.items() 
                               if k not in ["document_id", "chunk_text", "chunk_index", 
                                          "chunk_type", "start_position", "end_position", "word_count"]}
                })
            
            # Sort by chunk index
            chunks.sort(key=lambda x: x["chunk_index"])
            
            logger.info(f"✅ Retrieved {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error getting document chunks: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            
            stats = {
                "collection_name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "status": collection_info.status,
                "optimizer_status": collection_info.optimizer_status,
                "payload_schema": collection_info.payload_schema
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting collection stats: {e}")
            raise
    
    # ==================== UTILITY METHODS ====================
    
    async def close(self):
        """Close the vector storage service"""
        try:
            # Qdrant client doesn't need explicit closing
            logger.info("✅ Vector storage service closed")
        except Exception as e:
            logger.error(f"⚠️ Error closing vector storage service: {e}")


# ==================== EXAMPLE USAGE ====================

async def example_usage():
    """Example of how to use the VectorStorageService"""
    
    # Initialize service
    vector_service = VectorStorageService()
    await vector_service.initialize()
    
    try:
        # Sample document text
        sample_text = """
        This is a sample legal document about confidentiality agreements.
        The parties agree to maintain strict confidentiality regarding all proprietary information.
        Confidential information includes technical data, business plans, and customer lists.
        The confidentiality period shall be two years from the date of this agreement.
        """
        
        # Chunk the text
        chunks = vector_service.chunk_text(sample_text, chunk_size=200, chunk_overlap=50)
        
        # Store chunks
        document_id = "sample-doc-001"
        vector_ids = await vector_service.store_document_chunks(
            document_id=document_id,
            chunks=chunks,
            metadata={"client": "Sample Client", "document_type": "NDA"}
        )
        
        print(f"Stored {len(vector_ids)} chunks for document {document_id}")
        
        # Perform semantic search
        search_results = await vector_service.semantic_search(
            query="confidentiality agreement terms",
            limit=5
        )
        
        print(f"Found {len(search_results)} search results")
        for result in search_results:
            print(f"Score: {result['score']:.3f} - {result['chunk_text'][:100]}...")
        
        # Find similar documents
        similar_docs = await vector_service.find_similar_documents(
            document_id=document_id,
            limit=3
        )
        
        print(f"Found {len(similar_docs)} similar documents")
        
    finally:
        await vector_service.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
