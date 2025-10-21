"""
Test Suite for Contract Reviewer v2 - Integrated Application
Comprehensive tests for the complete integrated workflow
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime
import io

# Import the integrated app
from app_integrated import (
    app, initialize_services, DocumentUploadRequest, AnalysisRequest,
    DocumentResponse, AnalysisResponse, SearchRequest, SearchResponse
)


class TestIntegratedContractReviewer:
    """Test cases for the integrated Contract Reviewer v2 application"""
    
    @pytest.fixture
    async def test_app(self):
        """Create a test app instance"""
        # Mock all external services
        with patch('app_integrated.doc_service') as mock_doc_service, \
             patch('app_integrated.vector_service') as mock_vector_service, \
             patch('app_integrated.processing_service') as mock_processing_service, \
             patch('app_integrated.storage_service') as mock_storage_service, \
             patch('app_integrated.report_service') as mock_report_service, \
             patch('app_integrated.redis_client') as mock_redis_client:
            
            # Configure mocks
            mock_doc_service.create_document.return_value = {
                "id": "test-doc-001",
                "original_filename": "test_contract.pdf",
                "file_size": 102400,
                "file_path": "/tmp/test_contract.pdf",
                "metadata": {"client_id": "Test_Client"}
            }
            
            mock_doc_service.get_document_by_id.return_value = {
                "id": "test-doc-001",
                "original_filename": "test_contract.pdf",
                "file_size": 102400,
                "file_path": "/tmp/test_contract.pdf",
                "metadata": {"client_id": "Test_Client"}
            }
            
            mock_doc_service.get_analysis_results_by_document.return_value = []
            
            mock_doc_service.create_analysis_result.return_value = {
                "id": "test-analysis-001",
                "document_id": "test-doc-001",
                "analysis_data": {"summary": "Test analysis"},
                "model_used": "llama3.2:3b",
                "processing_time_ms": 1000
            }
            
            mock_processing_service.process_document.return_value = {
                "chunks_created": 5,
                "vector_ids": ["vec-001", "vec-002"],
                "processing_status": "completed",
                "processed_at": datetime.now().isoformat()
            }
            
            mock_processing_service.search_documents.return_value = [
                {
                    "vector_id": "vec-001",
                    "score": 0.95,
                    "document_id": "test-doc-001",
                    "chunk_text": "This is about confidentiality",
                    "chunk_index": 0,
                    "chunk_type": "paragraph",
                    "start_position": 0,
                    "end_position": 30,
                    "word_count": 6,
                    "filename": "test_contract.pdf"
                }
            ]
            
            mock_storage_service.store_file.return_value = MagicMock(
                file_id="file-001",
                file_path="/data/file_storage/test_contract.pdf",
                file_size=102400,
                checksum="abc123",
                created_at=datetime.now()
            )
            
            mock_storage_service.store_analysis_result.return_value = MagicMock(
                file_id="analysis-file-001",
                file_path="/data/file_storage/analysis.json",
                file_size=2048,
                created_at=datetime.now()
            )
            
            mock_report_service.generate_report.return_value = MagicMock(
                file_id="report-001",
                file_size=51200,
                created_at=datetime.now()
            )
            
            mock_redis_client.get.return_value = None
            mock_redis_client.setex.return_value = True
            mock_redis_client.ping.return_value = True
            
            yield app
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF content for testing"""
        return b"PDF content for testing contract analysis"
    
    # ==================== DOCUMENT UPLOAD TESTS ====================
    
    @pytest.mark.asyncio
    async def test_upload_document_basic(self, test_app, sample_pdf_content):
        """Test basic document upload"""
        with patch('app_integrated.Path') as mock_path:
            mock_path.return_value.parent.mkdir = MagicMock()
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.unlink = MagicMock()
            
            # Create test file
            test_file = io.BytesIO(sample_pdf_content)
            test_file.name = "test_contract.pdf"
            
            # Test upload
            response = await test_app.post(
                "/api/documents/upload",
                files={"file": test_file},
                params={
                    "client_id": "Test_Client",
                    "document_type": "contract",
                    "process_for_search": True,
                    "generate_report": False
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["document_id"] == "test-doc-001"
            assert data["filename"] == "test_contract.pdf"
            assert data["status"] == "uploaded"
            assert "vector_processing" in data
            assert "file_storage" in data
    
    @pytest.mark.asyncio
    async def test_upload_document_with_report(self, test_app, sample_pdf_content):
        """Test document upload with report generation"""
        with patch('app_integrated.Path') as mock_path:
            mock_path.return_value.parent.mkdir = MagicMock()
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.unlink = MagicMock()
            
            # Create test file
            test_file = io.BytesIO(sample_pdf_content)
            test_file.name = "test_contract.pdf"
            
            # Test upload with report generation
            response = await test_app.post(
                "/api/documents/upload",
                files={"file": test_file},
                params={
                    "client_id": "Test_Client",
                    "document_type": "contract",
                    "process_for_search": True,
                    "generate_report": True,
                    "report_format": "pdf"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["document_id"] == "test-doc-001"
            assert data["status"] == "uploaded"
            assert "vector_processing" in data
            assert "file_storage" in data
    
    @pytest.mark.asyncio
    async def test_upload_document_invalid_metadata(self, test_app, sample_pdf_content):
        """Test document upload with invalid metadata"""
        with patch('app_integrated.Path') as mock_path:
            mock_path.return_value.parent.mkdir = MagicMock()
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.unlink = MagicMock()
            
            # Create test file
            test_file = io.BytesIO(sample_pdf_content)
            test_file.name = "test_contract.pdf"
            
            # Test upload with invalid metadata
            response = await test_app.post(
                "/api/documents/upload",
                files={"file": test_file},
                params={
                    "client_id": "Test_Client",
                    "metadata": "invalid json"
                }
            )
            
            assert response.status_code == 400
            assert "Invalid metadata JSON" in response.json()["detail"]
    
    # ==================== DOCUMENT LISTING TESTS ====================
    
    @pytest.mark.asyncio
    async def test_list_documents_basic(self, test_app):
        """Test basic document listing"""
        with patch('app_integrated.doc_service') as mock_doc_service:
            mock_doc_service.get_documents.return_value = (
                [
                    {
                        "id": "doc-001",
                        "original_filename": "contract1.pdf",
                        "file_size": 102400,
                        "upload_timestamp": datetime.now().isoformat(),
                        "metadata": {"client_id": "Test_Client"}
                    },
                    {
                        "id": "doc-002", 
                        "original_filename": "contract2.pdf",
                        "file_size": 204800,
                        "upload_timestamp": datetime.now().isoformat(),
                        "metadata": {"client_id": "Test_Client"}
                    }
                ],
                2
            )
            
            response = await test_app.get("/api/documents?limit=10&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["documents"]) == 2
            assert data["total_count"] == 2
            assert data["limit"] == 10
            assert data["offset"] == 0
            assert data["has_more"] is False
    
    @pytest.mark.asyncio
    async def test_list_documents_with_vectors(self, test_app):
        """Test document listing with vector information"""
        with patch('app_integrated.doc_service') as mock_doc_service, \
             patch('app_integrated.processing_service') as mock_processing_service:
            
            mock_doc_service.get_documents.return_value = (
                [{"id": "doc-001", "original_filename": "contract1.pdf"}],
                1
            )
            
            mock_processing_service.vector_service.get_document_chunks.return_value = [
                {"chunk_text": "test chunk"}
            ]
            
            response = await test_app.get("/api/documents?include_vectors=true")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "vector_info" in data["documents"][0]
            assert data["documents"][0]["vector_info"]["has_vectors"] is True
            assert data["documents"][0]["vector_info"]["chunk_count"] == 1
    
    @pytest.mark.asyncio
    async def test_list_documents_with_reports(self, test_app):
        """Test document listing with report information"""
        with patch('app_integrated.doc_service') as mock_doc_service, \
             patch('app_integrated.storage_service') as mock_storage_service:
            
            mock_doc_service.get_documents.return_value = (
                [{"id": "doc-001", "original_filename": "contract1.pdf"}],
                1
            )
            
            mock_storage_service._find_files_by_document_id.return_value = [
                MagicMock(
                    file_id="report-001",
                    file_type=MagicMock(value="report_pdf"),
                    created_at=datetime.now(),
                    file_size=51200
                )
            ]
            
            response = await test_app.get("/api/documents?include_reports=true")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "report_info" in data["documents"][0]
            assert data["documents"][0]["report_info"]["has_reports"] is True
            assert data["documents"][0]["report_info"]["report_count"] == 1
    
    # ==================== ANALYSIS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_analyze_document_basic(self, test_app):
        """Test basic document analysis"""
        with patch('app_integrated.doc_service') as mock_doc_service, \
             patch('app_integrated.processing_service') as mock_processing_service, \
             patch('app_integrated.storage_service') as mock_storage_service:
            
            mock_doc_service.get_document_by_id.return_value = {
                "id": "test-doc-001",
                "original_filename": "test_contract.pdf",
                "file_size": 102400,
                "file_path": "/tmp/test_contract.pdf",
                "metadata": {"client_id": "Test_Client"}
            }
            
            mock_doc_service.get_analysis_results_by_document.return_value = []
            
            mock_doc_service.create_analysis_result.return_value = {
                "id": "test-analysis-001",
                "document_id": "test-doc-001",
                "analysis_data": {
                    "summary": {"summary": "Test analysis summary"},
                    "risks": [{"level": "low", "description": "Low risk"}],
                    "recommendations": ["Test recommendation"]
                },
                "model_used": "llama3.2:3b",
                "processing_time_ms": 1000
            }
            
            mock_processing_service.process_document.return_value = {
                "chunks_created": 5,
                "vector_ids": ["vec-001"],
                "processing_status": "completed",
                "processed_at": datetime.now().isoformat()
            }
            
            mock_storage_service.store_analysis_result.return_value = MagicMock(
                file_id="analysis-file-001"
            )
            
            request_data = {
                "analysis_type": "comprehensive",
                "include_risks": True,
                "include_recommendations": True,
                "include_citations": True,
                "process_for_search": True,
                "generate_report": False
            }
            
            response = await test_app.post(
                "/api/analyze/test-doc-001",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["analysis_id"] == "test-analysis-001"
            assert data["document_id"] == "test-doc-001"
            assert data["status"] == "completed"
            assert data["model_used"] == "llama3.2:3b"
            assert "vector_processing" in data
    
    @pytest.mark.asyncio
    async def test_analyze_document_with_report(self, test_app):
        """Test document analysis with report generation"""
        with patch('app_integrated.doc_service') as mock_doc_service, \
             patch('app_integrated.processing_service') as mock_processing_service, \
             patch('app_integrated.storage_service') as mock_storage_service, \
             patch('app_integrated.report_service') as mock_report_service:
            
            mock_doc_service.get_document_by_id.return_value = {
                "id": "test-doc-001",
                "original_filename": "test_contract.pdf",
                "file_size": 102400,
                "file_path": "/tmp/test_contract.pdf",
                "metadata": {"client_id": "Test_Client"}
            }
            
            mock_doc_service.get_analysis_results_by_document.return_value = []
            
            mock_doc_service.create_analysis_result.return_value = {
                "id": "test-analysis-001",
                "document_id": "test-doc-001",
                "analysis_data": {
                    "summary": {"summary": "Test analysis summary"},
                    "risks": [{"level": "low", "description": "Low risk"}],
                    "recommendations": ["Test recommendation"]
                },
                "model_used": "llama3.2:3b",
                "processing_time_ms": 1000
            }
            
            mock_processing_service.process_document.return_value = {
                "chunks_created": 5,
                "vector_ids": ["vec-001"],
                "processing_status": "completed",
                "processed_at": datetime.now().isoformat()
            }
            
            mock_storage_service.store_analysis_result.return_value = MagicMock(
                file_id="analysis-file-001"
            )
            
            mock_report_service.generate_report.return_value = MagicMock(
                file_id="report-001",
                file_size=51200,
                created_at=datetime.now()
            )
            
            request_data = {
                "analysis_type": "comprehensive",
                "include_risks": True,
                "include_recommendations": True,
                "include_citations": True,
                "process_for_search": True,
                "generate_report": True,
                "report_format": "pdf"
            }
            
            response = await test_app.post(
                "/api/analyze/test-doc-001",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["analysis_id"] == "test-analysis-001"
            assert data["status"] == "completed"
            assert "vector_processing" in data
            assert "report_generation" in data
    
    @pytest.mark.asyncio
    async def test_analyze_document_not_found(self, test_app):
        """Test analysis of non-existent document"""
        with patch('app_integrated.doc_service') as mock_doc_service:
            mock_doc_service.get_document_by_id.return_value = None
            
            request_data = {
                "analysis_type": "comprehensive",
                "process_for_search": True,
                "generate_report": False
            }
            
            response = await test_app.post(
                "/api/analyze/non-existent-doc",
                json=request_data
            )
            
            assert response.status_code == 404
            assert "Document not found" in response.json()["detail"]
    
    # ==================== SEARCH TESTS ====================
    
    @pytest.mark.asyncio
    async def test_search_documents_basic(self, test_app):
        """Test basic semantic search"""
        with patch('app_integrated.processing_service') as mock_processing_service:
            mock_processing_service.search_documents.return_value = [
                {
                    "vector_id": "vec-001",
                    "score": 0.95,
                    "document_id": "test-doc-001",
                    "chunk_text": "This is about confidentiality",
                    "chunk_index": 0,
                    "chunk_type": "paragraph",
                    "start_position": 0,
                    "end_position": 30,
                    "word_count": 6,
                    "filename": "test_contract.pdf"
                }
            ]
            
            request_data = {
                "query": "confidentiality agreement",
                "limit": 10,
                "score_threshold": 0.7,
                "include_analysis": False,
                "include_reports": False
            }
            
            response = await test_app.post("/api/search", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["results"]) == 1
            assert data["total_results"] == 1
            assert data["query"] == "confidentiality agreement"
            assert data["results"][0]["score"] == 0.95
            assert data["results"][0]["document_id"] == "test-doc-001"
    
    @pytest.mark.asyncio
    async def test_search_documents_with_analysis(self, test_app):
        """Test semantic search with analysis data"""
        with patch('app_integrated.processing_service') as mock_processing_service, \
             patch('app_integrated.doc_service') as mock_doc_service:
            
            mock_processing_service.search_documents.return_value = [
                {
                    "vector_id": "vec-001",
                    "score": 0.95,
                    "document_id": "test-doc-001",
                    "chunk_text": "This is about confidentiality",
                    "chunk_index": 0,
                    "chunk_type": "paragraph",
                    "start_position": 0,
                    "end_position": 30,
                    "word_count": 6,
                    "filename": "test_contract.pdf"
                }
            ]
            
            mock_doc_service.get_analysis_results_by_document.return_value = [
                {
                    "id": "analysis-001",
                    "analysis_data": {"summary": "Test analysis"},
                    "model_used": "llama3.2:3b"
                }
            ]
            
            request_data = {
                "query": "confidentiality agreement",
                "limit": 10,
                "score_threshold": 0.7,
                "include_analysis": True,
                "include_reports": False
            }
            
            response = await test_app.post("/api/search", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["results"]) == 1
            assert "analysis" in data["results"][0]
            assert data["results"][0]["analysis"]["id"] == "analysis-001"
    
    # ==================== STATISTICS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, test_app):
        """Test getting system statistics"""
        with patch('app_integrated.doc_service') as mock_doc_service, \
             patch('app_integrated.processing_service') as mock_processing_service, \
             patch('app_integrated.storage_service') as mock_storage_service, \
             patch('app_integrated.report_service') as mock_report_service, \
             patch('app_integrated.redis_client') as mock_redis_client:
            
            mock_doc_service.get_document_statistics.return_value = {
                "total_documents": 10,
                "total_size_bytes": 1024000
            }
            
            mock_doc_service.get_analysis_statistics.return_value = {
                "total_analyses": 5,
                "average_processing_time_ms": 2000
            }
            
            mock_processing_service.get_processing_stats.return_value = {
                "vectors_count": 100,
                "points_count": 100
            }
            
            mock_storage_service.get_storage_stats.return_value = {
                "total_files": 20,
                "total_size_bytes": 2048000
            }
            
            mock_report_service.get_report_stats.return_value = {
                "total_templates": 3,
                "total_reports": 8
            }
            
            mock_redis_client.info.return_value = {
                "connected_clients": 5,
                "used_memory_human": "1MB",
                "keyspace_hits": 1000,
                "keyspace_misses": 100
            }
            
            response = await test_app.get("/api/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "timestamp" in data
            assert "services" in data
            assert "postgresql" in data["services"]
            assert "qdrant" in data["services"]
            assert "redis" in data["services"]
            assert "file_storage" in data["services"]
            assert "reports" in data["services"]
    
    # ==================== HEALTH CHECK TESTS ====================
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, test_app):
        """Test health check when all services are healthy"""
        with patch('app_integrated.doc_service') as mock_doc_service, \
             patch('app_integrated.vector_service') as mock_vector_service, \
             patch('app_integrated.storage_service') as mock_storage_service, \
             patch('app_integrated.report_service') as mock_report_service, \
             patch('app_integrated.redis_client') as mock_redis_client:
            
            mock_doc_service.get_documents.return_value = ([], 0)
            mock_vector_service.get_collection_stats.return_value = {"status": "green"}
            mock_storage_service.get_storage_stats.return_value = {"total_files": 0}
            mock_report_service.get_report_stats.return_value = {"total_templates": 0}
            mock_redis_client.ping.return_value = True
            
            response = await test_app.get("/api/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["services"]["postgresql"] == "healthy"
            assert data["services"]["qdrant"] == "healthy"
            assert data["services"]["redis"] == "healthy"
            assert data["services"]["file_storage"] == "healthy"
            assert data["services"]["reports"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self, test_app):
        """Test health check when some services are unhealthy"""
        with patch('app_integrated.doc_service') as mock_doc_service, \
             patch('app_integrated.vector_service') as mock_vector_service, \
             patch('app_integrated.storage_service') as mock_storage_service, \
             patch('app_integrated.report_service') as mock_report_service, \
             patch('app_integrated.redis_client') as mock_redis_client:
            
            mock_doc_service.get_documents.side_effect = Exception("Database error")
            mock_vector_service.get_collection_stats.return_value = {"status": "green"}
            mock_storage_service.get_storage_stats.return_value = {"total_files": 0}
            mock_report_service.get_report_stats.return_value = {"total_templates": 0}
            mock_redis_client.ping.side_effect = Exception("Redis error")
            
            response = await test_app.get("/api/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["services"]["postgresql"] == "unhealthy"
            assert data["services"]["qdrant"] == "healthy"
            assert data["services"]["redis"] == "unhealthy"
            assert "unhealthy_services" in data
            assert "postgresql" in data["unhealthy_services"]
            assert "redis" in data["unhealthy_services"]


class TestIntegratedWorkflow:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_document_workflow(self):
        """Test complete document workflow: upload -> analyze -> search -> report"""
        try:
            # This test would require real services running
            # For now, we'll test the workflow logic
            
            # 1. Upload document
            # 2. Analyze document
            # 3. Search documents
            # 4. Generate report
            
            # This is a placeholder for integration testing
            # In practice, you'd start real services and test the complete flow
            assert True
            
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
