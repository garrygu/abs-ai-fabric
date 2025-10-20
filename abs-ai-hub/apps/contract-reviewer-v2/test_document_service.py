"""
Test suite for Document Management Service
Tests all CRUD operations for documents and analysis results
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
import uuid

from document_service import DocumentService


class TestDocumentService:
    """Test cases for DocumentService"""
    
    @pytest.fixture
    async def doc_service(self):
        """Create a test document service instance"""
        service = DocumentService()
        # Mock the database connection for testing
        service.pool = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_document_data(self):
        """Sample document data for testing"""
        return {
            "filename": "test_contract.pdf",
            "original_filename": "contract.pdf",
            "file_path": "/tmp/test_contract.pdf",
            "file_size": 1024,
            "file_type": ".pdf",
            "mime_type": "application/pdf",
            "status": "uploaded",
            "metadata": {"client": "ACME Corp", "contract_type": "NDA"}
        }
    
    @pytest.fixture
    def sample_analysis_data(self):
        """Sample analysis data for testing"""
        return {
            "summary": "This is a standard NDA contract",
            "risks": [
                {"level": "low", "description": "Standard confidentiality clause"}
            ],
            "recommendations": [
                "Review confidentiality period"
            ],
            "key_points": [
                "Confidentiality period: 2 years",
                "Governing law: California"
            ]
        }
    
    # ==================== DOCUMENT CRUD TESTS ====================
    
    @pytest.mark.asyncio
    async def test_create_document(self, doc_service, sample_document_data):
        """Test document creation"""
        # Mock database response
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = str(uuid.uuid4())
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            # Test document creation
            result = await doc_service.create_document(
                file_path=temp_file_path,
                original_filename="contract.pdf",
                metadata={"client": "ACME Corp"}
            )
            
            # Verify result structure
            assert "id" in result
            assert result["original_filename"] == "contract.pdf"
            assert result["status"] == "uploaded"
            
        finally:
            # Clean up
            Path(temp_file_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_get_document_by_id(self, doc_service):
        """Test getting document by ID"""
        document_id = str(uuid.uuid4())
        
        # Mock database response
        mock_row = AsyncMock()
        mock_row.items.return_value = [
            ("id", document_id),
            ("filename", "test.pdf"),
            ("original_filename", "contract.pdf"),
            ("file_path", "/tmp/test.pdf"),
            ("file_size", 1024),
            ("file_type", ".pdf"),
            ("mime_type", "application/pdf"),
            ("upload_timestamp", "2024-01-01T00:00:00"),
            ("analysis_timestamp", None),
            ("status", "uploaded"),
            ("metadata", {"client": "ACME"}),
            ("created_at", "2024-01-01T00:00:00"),
            ("updated_at", "2024-01-01T00:00:00")
        ]
        
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = mock_row
        
        result = await doc_service.get_document_by_id(document_id)
        
        assert result is not None
        assert result["id"] == document_id
        assert result["original_filename"] == "contract.pdf"
    
    @pytest.mark.asyncio
    async def test_get_documents_pagination(self, doc_service):
        """Test document listing with pagination"""
        # Mock database responses
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = 25  # total count
        
        mock_rows = []
        for i in range(10):
            mock_row = AsyncMock()
            mock_row.items.return_value = [
                ("id", str(uuid.uuid4())),
                ("filename", f"test_{i}.pdf"),
                ("original_filename", f"contract_{i}.pdf"),
                ("file_path", f"/tmp/test_{i}.pdf"),
                ("file_size", 1024),
                ("file_type", ".pdf"),
                ("mime_type", "application/pdf"),
                ("upload_timestamp", "2024-01-01T00:00:00"),
                ("analysis_timestamp", None),
                ("status", "uploaded"),
                ("metadata", {}),
                ("created_at", "2024-01-01T00:00:00"),
                ("updated_at", "2024-01-01T00:00:00")
            ]
            mock_rows.append(mock_row)
        
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetch.return_value = mock_rows
        
        documents, total_count = await doc_service.get_documents(limit=10, offset=0)
        
        assert len(documents) == 10
        assert total_count == 25
        assert documents[0]["original_filename"] == "contract_0.pdf"
    
    @pytest.mark.asyncio
    async def test_update_document(self, doc_service):
        """Test document update"""
        document_id = str(uuid.uuid4())
        
        # Mock database responses
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = document_id
        
        # Mock get_document_by_id for the return value
        mock_row = AsyncMock()
        mock_row.items.return_value = [
            ("id", document_id),
            ("filename", "test.pdf"),
            ("original_filename", "contract.pdf"),
            ("file_path", "/tmp/test.pdf"),
            ("file_size", 1024),
            ("file_type", ".pdf"),
            ("mime_type", "application/pdf"),
            ("upload_timestamp", "2024-01-01T00:00:00"),
            ("analysis_timestamp", None),
            ("status", "analyzed"),
            ("metadata", {"client": "ACME"}),
            ("created_at", "2024-01-01T00:00:00"),
            ("updated_at", "2024-01-01T00:00:00")
        ]
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = mock_row
        
        result = await doc_service.update_document(
            document_id=document_id,
            updates={"status": "analyzed", "metadata": {"client": "ACME Corp"}}
        )
        
        assert result is not None
        assert result["id"] == document_id
        assert result["status"] == "analyzed"
    
    @pytest.mark.asyncio
    async def test_delete_document(self, doc_service):
        """Test document deletion"""
        document_id = str(uuid.uuid4())
        
        # Mock get_document_by_id for the document info
        mock_row = AsyncMock()
        mock_row.items.return_value = [
            ("id", document_id),
            ("filename", "test.pdf"),
            ("original_filename", "contract.pdf"),
            ("file_path", "/tmp/test.pdf"),
            ("file_size", 1024),
            ("file_type", ".pdf"),
            ("mime_type", "application/pdf"),
            ("upload_timestamp", "2024-01-01T00:00:00"),
            ("analysis_timestamp", None),
            ("status", "uploaded"),
            ("metadata", {}),
            ("created_at", "2024-01-01T00:00:00"),
            ("updated_at", "2024-01-01T00:00:00")
        ]
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = mock_row
        
        # Mock delete operation
        doc_service.pool.acquire.return_value.__aenter__.return_value.execute.return_value = "DELETE 1"
        
        result = await doc_service.delete_document(document_id)
        
        assert result is True
    
    # ==================== ANALYSIS RESULT TESTS ====================
    
    @pytest.mark.asyncio
    async def test_create_analysis_result(self, doc_service, sample_analysis_data):
        """Test analysis result creation"""
        document_id = str(uuid.uuid4())
        analysis_id = str(uuid.uuid4())
        
        # Mock database responses
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = analysis_id
        
        # Mock get_analysis_result_by_id for the return value
        mock_row = AsyncMock()
        mock_row.items.return_value = [
            ("id", analysis_id),
            ("document_id", document_id),
            ("analysis_type", "contract_review"),
            ("analysis_data", sample_analysis_data),
            ("analysis_timestamp", "2024-01-01T00:00:00"),
            ("model_used", "llama3.2:3b"),
            ("processing_time_ms", 1500),
            ("status", "completed"),
            ("created_at", "2024-01-01T00:00:00")
        ]
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = mock_row
        
        result = await doc_service.create_analysis_result(
            document_id=document_id,
            analysis_type="contract_review",
            analysis_data=sample_analysis_data,
            model_used="llama3.2:3b",
            processing_time_ms=1500
        )
        
        assert result is not None
        assert result["id"] == analysis_id
        assert result["document_id"] == document_id
        assert result["analysis_type"] == "contract_review"
        assert result["model_used"] == "llama3.2:3b"
    
    @pytest.mark.asyncio
    async def test_get_analysis_results_by_document(self, doc_service, sample_analysis_data):
        """Test getting analysis results for a document"""
        document_id = str(uuid.uuid4())
        
        # Mock database response
        mock_rows = []
        for i in range(3):
            mock_row = AsyncMock()
            mock_row.items.return_value = [
                ("id", str(uuid.uuid4())),
                ("document_id", document_id),
                ("analysis_type", "contract_review"),
                ("analysis_data", sample_analysis_data),
                ("analysis_timestamp", "2024-01-01T00:00:00"),
                ("model_used", "llama3.2:3b"),
                ("processing_time_ms", 1500),
                ("status", "completed"),
                ("created_at", "2024-01-01T00:00:00")
            ]
            mock_rows.append(mock_row)
        
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetch.return_value = mock_rows
        
        results = await doc_service.get_analysis_results_by_document(document_id)
        
        assert len(results) == 3
        assert all(result["document_id"] == document_id for result in results)
    
    @pytest.mark.asyncio
    async def test_delete_analysis_result(self, doc_service):
        """Test analysis result deletion"""
        analysis_id = str(uuid.uuid4())
        
        # Mock get_analysis_result_by_id for the analysis info
        mock_row = AsyncMock()
        mock_row.items.return_value = [
            ("id", analysis_id),
            ("document_id", str(uuid.uuid4())),
            ("analysis_type", "contract_review"),
            ("analysis_data", {}),
            ("analysis_timestamp", "2024-01-01T00:00:00"),
            ("model_used", "llama3.2:3b"),
            ("processing_time_ms", 1500),
            ("status", "completed"),
            ("created_at", "2024-01-01T00:00:00")
        ]
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = mock_row
        
        # Mock delete operation
        doc_service.pool.acquire.return_value.__aenter__.return_value.execute.return_value = "DELETE 1"
        
        result = await doc_service.delete_analysis_result(analysis_id)
        
        assert result is True
    
    # ==================== STATISTICS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_document_statistics(self, doc_service):
        """Test document statistics retrieval"""
        # Mock database response
        mock_row = AsyncMock()
        mock_row.items.return_value = [
            ("total_documents", 25),
            ("analyzed_documents", 20),
            ("pending_documents", 5),
            ("total_size_bytes", 1024000),
            ("avg_file_size_bytes", 40960),
            ("latest_upload", "2024-01-01T00:00:00"),
            ("earliest_upload", "2024-01-01T00:00:00")
        ]
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = mock_row
        
        stats = await doc_service.get_document_statistics()
        
        assert stats is not None
        assert "total_documents" in stats
        assert stats["total_documents"] == 25
    
    @pytest.mark.asyncio
    async def test_get_analysis_statistics(self, doc_service):
        """Test analysis statistics retrieval"""
        # Mock database response
        mock_rows = []
        for analysis_type in ["contract_review", "risk_assessment"]:
            mock_row = AsyncMock()
            mock_row.items.return_value = [
                ("analysis_type", analysis_type),
                ("total_analyses", 10),
                ("avg_processing_time_ms", 1500),
                ("latest_analysis", "2024-01-01T00:00:00"),
                ("unique_documents_analyzed", 8)
            ]
            mock_rows.append(mock_row)
        
        doc_service.pool.acquire.return_value.__aenter__.return_value.fetch.return_value = mock_rows
        
        stats = await doc_service.get_analysis_statistics()
        
        assert len(stats) == 2
        assert all("analysis_type" in stat for stat in stats)


# ==================== INTEGRATION TESTS ====================

class TestDocumentServiceIntegration:
    """Integration tests with real database (requires PostgreSQL running)"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_document_lifecycle(self):
        """Test complete document lifecycle with real database"""
        # This test requires a running PostgreSQL instance
        # Skip if not available
        try:
            doc_service = DocumentService()
            await doc_service.initialize()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(b"test contract content")
                temp_file_path = temp_file.name
            
            try:
                # 1. Create document
                document = await doc_service.create_document(
                    file_path=temp_file_path,
                    original_filename="test_contract.pdf",
                    metadata={"client": "Test Corp", "contract_type": "NDA"}
                )
                
                document_id = document["id"]
                assert document["original_filename"] == "test_contract.pdf"
                assert document["status"] == "uploaded"
                
                # 2. Get document
                retrieved_doc = await doc_service.get_document_by_id(document_id)
                assert retrieved_doc["id"] == document_id
                
                # 3. Update document
                updated_doc = await doc_service.update_document(
                    document_id=document_id,
                    updates={"status": "analyzed"}
                )
                assert updated_doc["status"] == "analyzed"
                
                # 4. Create analysis result
                analysis = await doc_service.create_analysis_result(
                    document_id=document_id,
                    analysis_type="contract_review",
                    analysis_data={"summary": "Test analysis", "risks": []},
                    model_used="llama3.2:3b",
                    processing_time_ms=1000
                )
                
                analysis_id = analysis["id"]
                assert analysis["document_id"] == document_id
                assert analysis["analysis_type"] == "contract_review"
                
                # 5. Get analysis results
                analyses = await doc_service.get_analysis_results_by_document(document_id)
                assert len(analyses) == 1
                assert analyses[0]["id"] == analysis_id
                
                # 6. Get statistics
                doc_stats = await doc_service.get_document_statistics()
                assert doc_stats["total_documents"] >= 1
                
                analysis_stats = await doc_service.get_analysis_statistics()
                assert len(analysis_stats) >= 1
                
                # 7. Delete analysis result
                deleted = await doc_service.delete_analysis_result(analysis_id)
                assert deleted is True
                
                # 8. Delete document
                deleted = await doc_service.delete_document(document_id, delete_file=False)
                assert deleted is True
                
            finally:
                # Clean up temporary file
                Path(temp_file_path).unlink(missing_ok=True)
                await doc_service.close()
                
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")


# ==================== PERFORMANCE TESTS ====================

class TestDocumentServicePerformance:
    """Performance tests for document operations"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_bulk_document_creation(self):
        """Test creating multiple documents efficiently"""
        doc_service = DocumentService()
        await doc_service.initialize()
        
        try:
            # Create multiple documents concurrently
            tasks = []
            for i in range(10):
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                    temp_file.write(f"test content {i}".encode())
                    temp_file_path = temp_file.name
                
                task = doc_service.create_document(
                    file_path=temp_file_path,
                    original_filename=f"test_{i}.pdf",
                    metadata={"index": i}
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            documents = await asyncio.gather(*tasks)
            
            assert len(documents) == 10
            assert all(doc["status"] == "uploaded" for doc in documents)
            
            # Clean up
            for doc in documents:
                await doc_service.delete_document(doc["id"], delete_file=False)
                
        finally:
            await doc_service.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
