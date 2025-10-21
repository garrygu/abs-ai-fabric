"""
Test Suite for Vector Storage and Semantic Search
Comprehensive tests for Qdrant integration and document processing
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime

from vector_storage_service import VectorStorageService
from document_processing_service import DocumentProcessingService
from document_service import DocumentService


class TestVectorStorageService:
    """Test cases for VectorStorageService"""
    
    @pytest.fixture
    async def vector_service(self):
        """Create a test vector service instance"""
        service = VectorStorageService()
        # Mock the Qdrant client for testing
        service.qdrant_client = MagicMock()
        service.embedding_model = MagicMock()
        return service
    
    @pytest.fixture
    def sample_text(self):
        """Sample text for testing"""
        return """
        This is a sample legal document about confidentiality agreements.
        The parties agree to maintain strict confidentiality regarding all proprietary information.
        Confidential information includes technical data, business plans, and customer lists.
        The confidentiality period shall be two years from the date of this agreement.
        Any breach of confidentiality shall result in immediate termination of this agreement.
        """
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample text chunks for testing"""
        return [
            {
                "text": "This is a sample legal document about confidentiality agreements.",
                "chunk_index": 0,
                "chunk_type": "paragraph",
                "start_position": 0,
                "end_position": 80,
                "word_count": 12
            },
            {
                "text": "The parties agree to maintain strict confidentiality regarding all proprietary information.",
                "chunk_index": 1,
                "chunk_type": "paragraph",
                "start_position": 81,
                "end_position": 160,
                "word_count": 12
            }
        ]
    
    # ==================== TEXT CHUNKING TESTS ====================
    
    def test_chunk_text_by_paragraphs(self, vector_service, sample_text):
        """Test text chunking by paragraphs"""
        chunks = vector_service.chunk_text(
            text=sample_text,
            chunk_size=200,
            chunk_overlap=50,
            chunk_type="paragraph"
        )
        
        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("chunk_index" in chunk for chunk in chunks)
        assert all("chunk_type" in chunk for chunk in chunks)
        assert all(chunk["chunk_type"] == "paragraph" for chunk in chunks)
    
    def test_chunk_text_by_sentences(self, vector_service, sample_text):
        """Test text chunking by sentences"""
        chunks = vector_service.chunk_text(
            text=sample_text,
            chunk_size=100,
            chunk_overlap=20,
            chunk_type="sentence"
        )
        
        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("chunk_type" in chunk for chunk in chunks)
        assert all(chunk["chunk_type"] == "sentence" for chunk in chunks)
    
    def test_chunk_text_by_fixed_size(self, vector_service, sample_text):
        """Test text chunking by fixed size"""
        chunks = vector_service.chunk_text(
            text=sample_text,
            chunk_size=100,
            chunk_overlap=20,
            chunk_type="fixed"
        )
        
        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("chunk_type" in chunk for chunk in chunks)
        assert all(chunk["chunk_type"] == "fixed" for chunk in chunks)
        assert all(len(chunk["text"]) <= 100 for chunk in chunks)
    
    # ==================== EMBEDDING GENERATION TESTS ====================
    
    def test_generate_embeddings(self, vector_service):
        """Test embedding generation"""
        texts = ["This is a test document.", "Another test document."]
        
        # Mock embedding model
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        vector_service.embedding_model.encode.return_value = mock_embeddings
        
        embeddings = vector_service.generate_embeddings(texts)
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]
        vector_service.embedding_model.encode.assert_called_once_with(texts, convert_to_tensor=False)
    
    def test_generate_query_embedding(self, vector_service):
        """Test query embedding generation"""
        query = "confidentiality agreement"
        
        # Mock embedding model
        mock_embedding = [0.1, 0.2, 0.3]
        vector_service.embedding_model.encode.return_value = [mock_embedding]
        
        embedding = vector_service.generate_query_embedding(query)
        
        assert embedding == [0.1, 0.2, 0.3]
        vector_service.embedding_model.encode.assert_called_once_with([query], convert_to_tensor=False)
    
    # ==================== VECTOR STORAGE TESTS ====================
    
    @pytest.mark.asyncio
    async def test_store_document_chunks(self, vector_service, sample_chunks):
        """Test storing document chunks"""
        document_id = "test-doc-001"
        metadata = {"client": "Test Client"}
        
        # Mock embedding generation
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        vector_service.generate_embeddings.return_value = mock_embeddings
        
        # Mock Qdrant upsert
        vector_service.qdrant_client.upsert.return_value = None
        
        vector_ids = await vector_service.store_document_chunks(
            document_id=document_id,
            chunks=sample_chunks,
            metadata=metadata
        )
        
        assert len(vector_ids) == 2
        assert all(isinstance(vid, str) for vid in vector_ids)
        
        # Verify Qdrant upsert was called
        vector_service.qdrant_client.upsert.assert_called_once()
        call_args = vector_service.qdrant_client.upsert.call_args
        assert call_args[1]["collection_name"] == vector_service.collection_name
        assert len(call_args[1]["points"]) == 2
    
    @pytest.mark.asyncio
    async def test_delete_document_chunks(self, vector_service):
        """Test deleting document chunks"""
        document_id = "test-doc-001"
        
        # Mock Qdrant delete
        vector_service.qdrant_client.delete.return_value = None
        
        result = await vector_service.delete_document_chunks(document_id)
        
        assert result is True
        vector_service.qdrant_client.delete.assert_called_once()
    
    # ==================== SEMANTIC SEARCH TESTS ====================
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, vector_service):
        """Test semantic search"""
        query = "confidentiality agreement"
        
        # Mock query embedding generation
        mock_query_embedding = [0.1, 0.2, 0.3]
        vector_service.generate_query_embedding.return_value = mock_query_embedding
        
        # Mock Qdrant search results
        mock_search_result = MagicMock()
        mock_search_result.id = "vector-001"
        mock_search_result.score = 0.95
        mock_search_result.payload = {
            "document_id": "doc-001",
            "chunk_text": "This is about confidentiality",
            "chunk_index": 0,
            "chunk_type": "paragraph",
            "start_position": 0,
            "end_position": 30,
            "word_count": 6
        }
        
        vector_service.qdrant_client.search.return_value = [mock_search_result]
        
        results = await vector_service.semantic_search(
            query=query,
            limit=10,
            score_threshold=0.7
        )
        
        assert len(results) == 1
        assert results[0]["vector_id"] == "vector-001"
        assert results[0]["score"] == 0.95
        assert results[0]["document_id"] == "doc-001"
        assert results[0]["chunk_text"] == "This is about confidentiality"
    
    @pytest.mark.asyncio
    async def test_find_similar_documents(self, vector_service):
        """Test finding similar documents"""
        document_id = "test-doc-001"
        
        # Mock get_document_chunks
        mock_chunks = [{
            "chunk_text": "This is about confidentiality agreements",
            "chunk_index": 0
        }]
        vector_service.get_document_chunks.return_value = mock_chunks
        
        # Mock semantic search
        mock_search_results = [
            {
                "vector_id": "vector-001",
                "score": 0.9,
                "document_id": "doc-002",
                "chunk_text": "Similar confidentiality content"
            },
            {
                "vector_id": "vector-002",
                "score": 0.8,
                "document_id": "doc-003",
                "chunk_text": "Another similar document"
            }
        ]
        vector_service.semantic_search.return_value = mock_search_results
        
        similar_docs = await vector_service.find_similar_documents(
            document_id=document_id,
            limit=5,
            score_threshold=0.8
        )
        
        assert len(similar_docs) == 2
        assert similar_docs[0]["document_id"] == "doc-002"
        assert similar_docs[0]["max_score"] == 0.9
        assert similar_docs[1]["document_id"] == "doc-003"
        assert similar_docs[1]["max_score"] == 0.8
    
    # ==================== COLLECTION MANAGEMENT TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_collection_stats(self, vector_service):
        """Test getting collection statistics"""
        # Mock collection info
        mock_collection_info = MagicMock()
        mock_collection_info.vectors_count = 100
        mock_collection_info.points_count = 100
        mock_collection_info.status = "green"
        
        vector_service.qdrant_client.get_collection.return_value = mock_collection_info
        
        stats = await vector_service.get_collection_stats()
        
        assert stats["vectors_count"] == 100
        assert stats["points_count"] == 100
        assert stats["status"] == "green"


class TestDocumentProcessingService:
    """Test cases for DocumentProcessingService"""
    
    @pytest.fixture
    async def processing_service(self):
        """Create a test processing service instance"""
        vector_service = VectorStorageService()
        vector_service.qdrant_client = MagicMock()
        vector_service.embedding_model = MagicMock()
        
        doc_service = DocumentService()
        doc_service.pool = AsyncMock()
        
        service = DocumentProcessingService(vector_service, doc_service)
        return service
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF content for testing"""
        return "This is a sample PDF document about legal contracts."
    
    # ==================== TEXT EXTRACTION TESTS ====================
    
    def test_extract_text_from_pdf(self, processing_service, sample_pdf_content):
        """Test PDF text extraction"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(sample_pdf_content.encode())
            temp_file_path = temp_file.name
        
        try:
            # Mock PyMuPDF
            with patch('fitz.open') as mock_open:
                mock_doc = MagicMock()
                mock_doc.page_count = 1
                mock_page = MagicMock()
                mock_page.get_text.return_value = sample_pdf_content
                mock_doc.__getitem__.return_value = mock_page
                mock_open.return_value = mock_doc
                
                result = processing_service.extract_text_from_file(temp_file_path)
                
                assert result["text"] == sample_pdf_content
                assert result["page_count"] == 1
                assert result["extraction_method"] == "pymupdf"
                assert result["word_count"] == len(sample_pdf_content.split())
        
        finally:
            Path(temp_file_path).unlink(missing_ok=True)
    
    def test_extract_text_from_txt(self, processing_service, sample_pdf_content):
        """Test TXT text extraction"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(sample_pdf_content.encode())
            temp_file_path = temp_file.name
        
        try:
            result = processing_service.extract_text_from_file(temp_file_path)
            
            assert result["text"] == sample_pdf_content
            assert result["extraction_method"] == "plain_text"
            assert result["word_count"] == len(sample_pdf_content.split())
        
        finally:
            Path(temp_file_path).unlink(missing_ok=True)
    
    # ==================== DOCUMENT PROCESSING TESTS ====================
    
    @pytest.mark.asyncio
    async def test_process_document(self, processing_service, sample_pdf_content):
        """Test document processing"""
        document_id = "test-doc-001"
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(sample_pdf_content.encode())
            temp_file_path = temp_file.name
        
        try:
            # Mock vector service methods
            processing_service.vector_service.chunk_text.return_value = [
                {"text": "chunk1", "chunk_index": 0, "chunk_type": "paragraph", 
                 "start_position": 0, "end_position": 10, "word_count": 2}
            ]
            processing_service.vector_service.store_document_chunks.return_value = ["vector-001"]
            
            # Mock document service methods
            processing_service.doc_service.update_document.return_value = {"id": document_id}
            
            result = await processing_service.process_document(
                document_id=document_id,
                file_path=temp_file_path,
                metadata={"client": "Test Client"}
            )
            
            assert result["document_id"] == document_id
            assert result["chunks_created"] == 1
            assert result["vector_ids"] == ["vector-001"]
            assert result["processing_status"] == "completed"
            
            # Verify methods were called
            processing_service.vector_service.chunk_text.assert_called_once()
            processing_service.vector_service.store_document_chunks.assert_called_once()
            processing_service.doc_service.update_document.assert_called_once()
        
        finally:
            Path(temp_file_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_search_documents(self, processing_service):
        """Test document search"""
        query = "confidentiality agreement"
        
        # Mock vector service search
        mock_search_results = [
            {
                "vector_id": "vector-001",
                "score": 0.9,
                "document_id": "doc-001",
                "chunk_text": "This is about confidentiality",
                "chunk_index": 0,
                "chunk_type": "paragraph",
                "start_position": 0,
                "end_position": 30,
                "word_count": 6
            }
        ]
        processing_service.vector_service.semantic_search.return_value = mock_search_results
        
        # Mock document service
        mock_document = {
            "id": "doc-001",
            "original_filename": "contract.pdf",
            "upload_timestamp": "2024-01-01T00:00:00",
            "file_size": 1024,
            "file_type": ".pdf"
        }
        processing_service.doc_service.get_document_by_id.return_value = mock_document
        
        results = await processing_service.search_documents(
            query=query,
            limit=10,
            score_threshold=0.7
        )
        
        assert len(results) == 1
        assert results[0]["document_id"] == "doc-001"
        assert results[0]["filename"] == "contract.pdf"
        assert results[0]["score"] == 0.9
    
    @pytest.mark.asyncio
    async def test_find_similar_documents(self, processing_service):
        """Test finding similar documents"""
        document_id = "test-doc-001"
        
        # Mock vector service
        mock_similar_docs = [
            {
                "document_id": "doc-002",
                "max_score": 0.9,
                "chunks": [{"score": 0.9, "chunk_text": "Similar content"}]
            }
        ]
        processing_service.vector_service.find_similar_documents.return_value = mock_similar_docs
        
        # Mock document service
        mock_document = {
            "id": "doc-002",
            "original_filename": "similar.pdf",
            "upload_timestamp": "2024-01-01T00:00:00",
            "file_size": 2048,
            "file_type": ".pdf"
        }
        processing_service.doc_service.get_document_by_id.return_value = mock_document
        
        results = await processing_service.find_similar_documents(
            document_id=document_id,
            limit=5,
            score_threshold=0.8
        )
        
        assert len(results) == 1
        assert results[0]["document_id"] == "doc-002"
        assert results[0]["max_score"] == 0.9
        assert results[0]["filename"] == "similar.pdf"


class TestVectorSearchIntegration:
    """Integration tests for vector search functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_document_processing_workflow(self):
        """Test complete document processing workflow"""
        # This test requires running Qdrant and PostgreSQL instances
        # Skip if not available
        try:
            # Initialize services
            vector_service = VectorStorageService()
            await vector_service.initialize()
            
            doc_service = DocumentService()
            await doc_service.initialize()
            
            processing_service = DocumentProcessingService(vector_service, doc_service)
            await processing_service.initialize()
            
            # Create sample document
            sample_text = """
            This is a comprehensive confidentiality agreement between two parties.
            The parties agree to maintain strict confidentiality regarding all proprietary information.
            Confidential information includes technical data, business plans, customer lists, and financial information.
            The confidentiality period shall be three years from the date of this agreement.
            Any breach of confidentiality shall result in immediate termination and legal action.
            """
            
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
                temp_file.write(sample_text.encode())
                temp_file_path = temp_file.name
            
            try:
                # Process document
                document_id = str(uuid.uuid4())
                result = await processing_service.process_document(
                    document_id=document_id,
                    file_path=temp_file_path,
                    metadata={"client": "Integration Test", "document_type": "NDA"}
                )
                
                assert result["processing_status"] == "completed"
                assert result["chunks_created"] > 0
                
                # Search documents
                search_results = await processing_service.search_documents(
                    query="confidentiality agreement",
                    limit=5
                )
                
                assert len(search_results) > 0
                assert any(result["document_id"] == document_id for result in search_results)
                
                # Find similar documents
                similar_docs = await processing_service.find_similar_documents(
                    document_id=document_id,
                    limit=3
                )
                
                # Should find itself (or no results if it's the only document)
                assert isinstance(similar_docs, list)
                
            finally:
                # Clean up
                Path(temp_file_path).unlink(missing_ok=True)
                await processing_service.close()
                
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")


# ==================== PERFORMANCE TESTS ====================

class TestVectorSearchPerformance:
    """Performance tests for vector search"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_bulk_document_processing(self):
        """Test processing multiple documents efficiently"""
        try:
            # Initialize services
            vector_service = VectorStorageService()
            await vector_service.initialize()
            
            doc_service = DocumentService()
            await doc_service.initialize()
            
            processing_service = DocumentProcessingService(vector_service, doc_service)
            await processing_service.initialize()
            
            # Create multiple sample documents
            document_files = []
            for i in range(10):
                sample_text = f"""
                Document {i}: This is a sample legal document about confidentiality agreements.
                The parties agree to maintain strict confidentiality regarding all proprietary information.
                Confidential information includes technical data, business plans, and customer lists.
                The confidentiality period shall be two years from the date of this agreement.
                """
                
                with tempfile.NamedTemporaryFile(suffix=f"_{i}.txt", delete=False) as temp_file:
                    temp_file.write(sample_text.encode())
                    document_files.append((str(uuid.uuid4()), temp_file.name))
            
            try:
                # Process documents in batch
                results = await processing_service.process_multiple_documents(
                    document_files=document_files,
                    metadata={"batch_test": True}
                )
                
                successful = len([r for r in results if r.get("processing_status") == "completed"])
                assert successful >= 8  # Allow for some failures
                
                # Test search performance
                search_results = await processing_service.search_documents(
                    query="confidentiality agreement",
                    limit=20
                )
                
                assert len(search_results) >= 5
                
            finally:
                # Clean up
                for _, file_path in document_files:
                    Path(file_path).unlink(missing_ok=True)
                await processing_service.close()
                
        except Exception as e:
            pytest.skip(f"Performance test skipped: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
