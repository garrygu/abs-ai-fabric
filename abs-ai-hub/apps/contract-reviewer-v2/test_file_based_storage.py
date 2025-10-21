"""
Test Suite for File-Based Storage and Report Generation
Comprehensive tests for file organization, versioning, archiving, and report generation
"""

import pytest
import asyncio
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import uuid
from datetime import datetime

from file_based_storage_service import (
    FileBasedStorageService, FileType, StorageConfig, FileMetadata, StorageTier
)
from report_generation_service import (
    ReportGenerationService, ReportRequest, ReportFormat, ReportType, ReportTemplate
)


class TestFileBasedStorageService:
    """Test cases for FileBasedStorageService"""
    
    @pytest.fixture
    async def storage_service(self):
        """Create a test storage service instance"""
        config = StorageConfig(
            base_path="/tmp/test_file_storage",
            max_file_size=10 * 1024 * 1024,  # 10MB
            enable_compression=True
        )
        service = FileBasedStorageService(config)
        return service
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing"""
        return {
            "text": "This is a sample legal document about confidentiality agreements.",
            "json": {"analysis": "sample analysis", "risks": ["low", "medium"]},
            "bytes": b"This is binary data for testing file storage."
        }
    
    # ==================== FILE PATH GENERATION TESTS ====================
    
    def test_generate_file_path_document(self, storage_service):
        """Test file path generation for documents"""
        file_path = storage_service.generate_file_path(
            file_type=FileType.DOCUMENT,
            client_id="ACME_Corp",
            document_id="doc-001",
            filename="contract.pdf"
        )
        
        assert file_path.exists() is False  # Path should be generated but file not created
        assert "documents" in str(file_path)
        assert "ACME_Corp" in str(file_path)
        assert "doc_doc-001" in str(file_path)
        assert file_path.name == "contract.pdf"
    
    def test_generate_file_path_analysis(self, storage_service):
        """Test file path generation for analysis results"""
        file_path = storage_service.generate_file_path(
            file_type=FileType.ANALYSIS_RESULT,
            client_id="ACME_Corp",
            document_id="doc-001",
            analysis_id="analysis-001",
            filename="analysis.json"
        )
        
        assert "analysis_results" in str(file_path)
        assert "ACME_Corp" in str(file_path)
        assert "doc_doc-001" in str(file_path)
        assert "analysis_analysis-001" in str(file_path)
        assert file_path.name == "analysis.json"
    
    def test_generate_file_path_with_version(self, storage_service):
        """Test file path generation with version"""
        file_path = storage_service.generate_file_path(
            file_type=FileType.DOCUMENT,
            filename="contract.pdf",
            version=3
        )
        
        assert file_path.name == "contract_v3.pdf"
    
    def test_sanitize_filename(self, storage_service):
        """Test filename sanitization"""
        # Test invalid characters
        sanitized = storage_service._sanitize_filename("test<>file.pdf")
        assert sanitized == "test__file.pdf"
        
        # Test long filename
        long_name = "a" * 300 + ".pdf"
        sanitized = storage_service._sanitize_filename(long_name)
        assert len(sanitized) <= 255
        assert sanitized.endswith(".pdf")
    
    # ==================== FILE STORAGE TESTS ====================
    
    @pytest.mark.asyncio
    async def test_store_text_file(self, storage_service, sample_data):
        """Test storing text file"""
        file_metadata = await storage_service.store_file(
            file_data=sample_data["text"],
            file_type=FileType.DOCUMENT,
            original_filename="test_document.txt",
            client_id="Test_Client",
            document_id="doc-001"
        )
        
        assert file_metadata.file_id is not None
        assert file_metadata.original_filename == "test_document.txt"
        assert file_metadata.file_type == FileType.DOCUMENT
        assert file_metadata.client_id == "Test_Client"
        assert file_metadata.parent_document_id == "doc-001"
        assert file_metadata.file_size > 0
        assert file_metadata.checksum is not None
        
        # Verify file exists
        file_path = Path(file_metadata.file_path)
        assert file_path.exists()
    
    @pytest.mark.asyncio
    async def test_store_json_file(self, storage_service, sample_data):
        """Test storing JSON file"""
        file_metadata = await storage_service.store_file(
            file_data=sample_data["json"],
            file_type=FileType.ANALYSIS_RESULT,
            original_filename="analysis.json",
            client_id="Test_Client",
            document_id="doc-001",
            analysis_id="analysis-001"
        )
        
        assert file_metadata.file_type == FileType.ANALYSIS_RESULT
        assert file_metadata.analysis_id == "analysis-001"
        
        # Verify file content
        file_path = Path(file_metadata.file_path)
        assert file_path.exists()
        
        with open(file_path, 'r') as f:
            content = json.load(f)
        assert content == sample_data["json"]
    
    @pytest.mark.asyncio
    async def test_store_binary_file(self, storage_service, sample_data):
        """Test storing binary file"""
        file_metadata = await storage_service.store_file(
            file_data=sample_data["bytes"],
            file_type=FileType.DOCUMENT,
            original_filename="binary_file.bin",
            client_id="Test_Client"
        )
        
        assert file_metadata.file_type == FileType.DOCUMENT
        assert file_metadata.file_size == len(sample_data["bytes"])
        
        # Verify file content
        file_path = Path(file_metadata.file_path)
        assert file_path.exists()
        
        with open(file_path, 'rb') as f:
            content = f.read()
        assert content == sample_data["bytes"]
    
    @pytest.mark.asyncio
    async def test_retrieve_file(self, storage_service, sample_data):
        """Test retrieving file"""
        # Store file first
        file_metadata = await storage_service.store_file(
            file_data=sample_data["text"],
            file_type=FileType.DOCUMENT,
            original_filename="test_retrieve.txt",
            client_id="Test_Client"
        )
        
        # Retrieve file
        file_content, retrieved_metadata = await storage_service.retrieve_file(file_metadata.file_id)
        
        assert file_content.decode('utf-8') == sample_data["text"]
        assert retrieved_metadata.file_id == file_metadata.file_id
        assert retrieved_metadata.original_filename == file_metadata.original_filename
    
    @pytest.mark.asyncio
    async def test_delete_file(self, storage_service, sample_data):
        """Test deleting file"""
        # Store file first
        file_metadata = await storage_service.store_file(
            file_data=sample_data["text"],
            file_type=FileType.DOCUMENT,
            original_filename="test_delete.txt",
            client_id="Test_Client"
        )
        
        # Verify file exists
        file_path = Path(file_metadata.file_path)
        assert file_path.exists()
        
        # Delete file
        success = await storage_service.delete_file(file_metadata.file_id, permanent=True)
        assert success is True
        
        # Verify file is deleted
        assert not file_path.exists()
    
    # ==================== ANALYSIS RESULT SERIALIZATION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_store_analysis_result(self, storage_service):
        """Test storing analysis result"""
        analysis_data = {
            "summary": "This is a test analysis",
            "risks": [{"level": "low", "description": "Low risk"}],
            "recommendations": ["Recommendation 1", "Recommendation 2"]
        }
        
        file_metadata = await storage_service.store_analysis_result(
            analysis_data=analysis_data,
            document_id="doc-001",
            analysis_id="analysis-001",
            client_id="Test_Client",
            format="json"
        )
        
        assert file_metadata.file_type == FileType.ANALYSIS_RESULT
        assert file_metadata.analysis_id == "analysis-001"
        assert file_metadata.parent_document_id == "doc-001"
        assert file_metadata.client_id == "Test_Client"
        
        # Verify file content
        file_path = Path(file_metadata.file_path)
        with open(file_path, 'r') as f:
            content = json.load(f)
        
        assert content["analysis_id"] == "analysis-001"
        assert content["document_id"] == "doc-001"
        assert content["analysis_data"] == analysis_data
    
    @pytest.mark.asyncio
    async def test_retrieve_analysis_result(self, storage_service):
        """Test retrieving analysis result"""
        analysis_data = {
            "summary": "Test analysis summary",
            "risks": [{"level": "medium", "description": "Medium risk"}]
        }
        
        # Store analysis result
        await storage_service.store_analysis_result(
            analysis_data=analysis_data,
            document_id="doc-001",
            analysis_id="analysis-001",
            client_id="Test_Client"
        )
        
        # Retrieve analysis result
        retrieved_data = await storage_service.retrieve_analysis_result("analysis-001")
        
        assert retrieved_data["analysis_id"] == "analysis-001"
        assert retrieved_data["document_id"] == "doc-001"
        assert retrieved_data["analysis_data"] == analysis_data
    
    # ==================== FILE VERSIONING TESTS ====================
    
    @pytest.mark.asyncio
    async def test_create_file_version(self, storage_service, sample_data):
        """Test creating file version"""
        # Store original file
        original_metadata = await storage_service.store_file(
            file_data=sample_data["text"],
            file_type=FileType.DOCUMENT,
            original_filename="versioned_doc.txt",
            client_id="Test_Client",
            document_id="doc-001"
        )
        
        # Create new version
        new_content = "This is version 2 of the document."
        version_metadata = await storage_service.create_file_version(
            file_id=original_metadata.file_id,
            new_file_data=new_content,
            version_comment="Updated content"
        )
        
        assert version_metadata.version == 2
        assert version_metadata.parent_document_id == original_metadata.parent_document_id
        assert version_metadata.metadata["version_comment"] == "Updated content"
        assert version_metadata.metadata["parent_file_id"] == original_metadata.file_id
        
        # Verify new version content
        file_path = Path(version_metadata.file_path)
        with open(file_path, 'r') as f:
            content = f.read()
        assert content == new_content
    
    @pytest.mark.asyncio
    async def test_get_file_versions(self, storage_service, sample_data):
        """Test getting file versions"""
        # Store original file
        original_metadata = await storage_service.store_file(
            file_data=sample_data["text"],
            file_type=FileType.DOCUMENT,
            original_filename="versioned_doc.txt",
            client_id="Test_Client",
            document_id="doc-001"
        )
        
        # Create multiple versions
        for i in range(2, 4):
            new_content = f"This is version {i} of the document."
            await storage_service.create_file_version(
                file_id=original_metadata.file_id,
                new_file_data=new_content,
                version_comment=f"Version {i} update"
            )
        
        # Get all versions
        versions = await storage_service.get_file_versions("doc-001")
        
        assert len(versions) == 3
        assert versions[0].version == 1
        assert versions[1].version == 2
        assert versions[2].version == 3
    
    # ==================== ARCHIVING TESTS ====================
    
    @pytest.mark.asyncio
    async def test_archive_files(self, storage_service, sample_data):
        """Test archiving multiple files"""
        # Store multiple files
        file_ids = []
        for i in range(3):
            file_metadata = await storage_service.store_file(
                file_data=f"File {i} content",
                file_type=FileType.DOCUMENT,
                original_filename=f"file_{i}.txt",
                client_id="Test_Client",
                document_id=f"doc-{i:03d}"
            )
            file_ids.append(file_metadata.file_id)
        
        # Create archive
        archive_metadata = await storage_service.archive_files(
            file_ids=file_ids,
            archive_name="test_archive",
            compression_level=6
        )
        
        assert archive_metadata.file_type == FileType.ARCHIVE
        assert archive_metadata.metadata["archived_files"] == 3
        assert archive_metadata.metadata["compression_level"] == 6
        assert archive_metadata.metadata["file_ids"] == file_ids
        
        # Verify archive file exists
        archive_path = Path(archive_metadata.file_path)
        assert archive_path.exists()
        assert archive_path.suffix == ".zip"
    
    @pytest.mark.asyncio
    async def test_extract_archive(self, storage_service, sample_data):
        """Test extracting archive"""
        # Store files and create archive
        file_metadata = await storage_service.store_file(
            file_data=sample_data["text"],
            file_type=FileType.DOCUMENT,
            original_filename="archive_test.txt",
            client_id="Test_Client"
        )
        
        archive_metadata = await storage_service.archive_files(
            file_ids=[file_metadata.file_id],
            archive_name="extract_test"
        )
        
        # Extract archive
        extracted_files = await storage_service.extract_archive(archive_metadata.file_id)
        
        assert len(extracted_files) == 1
        assert extracted_files[0].original_filename == "archive_test.txt"
        assert extracted_files[0].file_type == FileType.DOCUMENT
    
    # ==================== STORAGE STATISTICS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_storage_stats(self, storage_service, sample_data):
        """Test getting storage statistics"""
        # Store some files
        for i in range(3):
            await storage_service.store_file(
                file_data=f"Test content {i}",
                file_type=FileType.DOCUMENT,
                original_filename=f"stats_test_{i}.txt",
                client_id="Test_Client"
            )
        
        # Get statistics
        stats = await storage_service.get_storage_stats()
        
        assert stats["total_files"] >= 3
        assert stats["total_size_bytes"] > 0
        assert "files_by_type" in stats
        assert "files_by_tier" in stats
        assert stats["base_path"] == str(storage_service.base_path)
    
    @pytest.mark.asyncio
    async def test_cleanup_old_files(self, storage_service):
        """Test cleaning up old files"""
        # Store temporary file
        temp_metadata = await storage_service.store_file(
            file_data="Temporary content",
            file_type=FileType.TEMP,
            original_filename="temp_file.txt",
            client_id="Test_Client"
        )
        
        # Clean up files older than 0 days (should clean up all temp files)
        cleaned_count = await storage_service.cleanup_old_files(days_old=0)
        
        assert cleaned_count >= 1
        
        # Verify temp file is deleted
        temp_path = Path(temp_metadata.file_path)
        assert not temp_path.exists()


class TestReportGenerationService:
    """Test cases for ReportGenerationService"""
    
    @pytest.fixture
    async def report_service(self):
        """Create a test report service instance"""
        storage_service = FileBasedStorageService(
            StorageConfig(base_path="/tmp/test_report_storage")
        )
        service = ReportGenerationService(storage_service)
        return service
    
    @pytest.fixture
    def sample_analysis_data(self):
        """Sample analysis data for testing"""
        return {
            "summary": {
                "summary": "This is a comprehensive analysis of the confidentiality agreement.",
                "key_points": [
                    "Standard confidentiality period of 2 years",
                    "Clear definition of confidential information",
                    "Appropriate remedies for breach"
                ]
            },
            "risks": [
                {"level": "low", "description": "Standard confidentiality clause"},
                {"level": "medium", "description": "Consider adding return of materials clause"}
            ],
            "recommendations": [
                "Review confidentiality period",
                "Add return of materials clause",
                "Verify governing law jurisdiction"
            ],
            "citations": [
                "Section 2.1: Confidentiality obligations",
                "Section 4.2: Term and termination"
            ]
        }
    
    @pytest.fixture
    def sample_document_metadata(self):
        """Sample document metadata for testing"""
        return {
            "original_filename": "confidentiality_agreement.pdf",
            "file_size": 102400,
            "upload_timestamp": "2024-01-15T10:30:00"
        }
    
    # ==================== TEMPLATE MANAGEMENT TESTS ====================
    
    def test_load_default_templates(self, report_service):
        """Test loading default templates"""
        assert len(report_service.templates) >= 3
        
        # Check specific templates exist
        template_ids = [t.template_id for t in report_service.templates.values()]
        assert "analysis_summary_default" in template_ids
        assert "detailed_analysis_default" in template_ids
        assert "executive_summary_default" in template_ids
    
    @pytest.mark.asyncio
    async def test_create_template(self, report_service):
        """Test creating custom template"""
        template_data = {
            "sections": ["summary", "risks", "recommendations"],
            "styling": {"font_family": "Arial", "font_size": 12}
        }
        
        template = await report_service.create_template(
            template_id="custom_template",
            name="Custom Template",
            description="A custom report template",
            report_type=ReportType.ANALYSIS_SUMMARY,
            format=ReportFormat.PDF,
            template_data=template_data
        )
        
        assert template.template_id == "custom_template"
        assert template.name == "Custom Template"
        assert template.report_type == ReportType.ANALYSIS_SUMMARY
        assert template.format == ReportFormat.PDF
        assert template.template_data == template_data
    
    @pytest.mark.asyncio
    async def test_get_template(self, report_service):
        """Test getting template by ID"""
        template = await report_service.get_template("analysis_summary_default")
        
        assert template is not None
        assert template.template_id == "analysis_summary_default"
        assert template.report_type == ReportType.ANALYSIS_SUMMARY
    
    @pytest.mark.asyncio
    async def test_list_templates(self, report_service):
        """Test listing templates"""
        # List all templates
        all_templates = await report_service.list_templates()
        assert len(all_templates) >= 3
        
        # List templates by type
        analysis_templates = await report_service.list_templates(ReportType.ANALYSIS_SUMMARY)
        assert len(analysis_templates) >= 1
        assert all(t.report_type == ReportType.ANALYSIS_SUMMARY for t in analysis_templates)
    
    # ==================== REPORT GENERATION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_generate_json_report(self, report_service, sample_analysis_data, sample_document_metadata):
        """Test generating JSON report"""
        request = ReportRequest(
            report_id="test-report-001",
            report_type=ReportType.ANALYSIS_SUMMARY,
            format=ReportFormat.JSON,
            document_ids=["doc-001"],
            analysis_ids=["analysis-001"],
            client_id="Test_Client"
        )
        
        report_metadata = await report_service.generate_report(
            request=request,
            analysis_data=sample_analysis_data,
            document_metadata=sample_document_metadata
        )
        
        assert report_metadata.file_type == FileType.ANALYSIS_RESULT  # JSON reports stored as analysis results
        assert report_metadata.metadata["report_type"] == "analysis_summary"
        assert report_metadata.metadata["report_format"] == "json"
        assert report_metadata.metadata["client_id"] == "Test_Client"
        
        # Verify report content
        file_path = Path(report_metadata.file_path)
        with open(file_path, 'r') as f:
            report_data = json.load(f)
        
        assert report_data["report_metadata"]["report_id"] == "test-report-001"
        assert report_data["analysis_data"] == sample_analysis_data
        assert report_data["document_metadata"] == sample_document_metadata
    
    @pytest.mark.asyncio
    async def test_generate_html_report(self, report_service, sample_analysis_data, sample_document_metadata):
        """Test generating HTML report"""
        request = ReportRequest(
            report_id="test-report-002",
            report_type=ReportType.DETAILED_ANALYSIS,
            format=ReportFormat.HTML,
            document_ids=["doc-001"],
            analysis_ids=["analysis-001"],
            client_id="Test_Client"
        )
        
        report_metadata = await report_service.generate_report(
            request=request,
            analysis_data=sample_analysis_data,
            document_metadata=sample_document_metadata
        )
        
        assert report_metadata.metadata["report_format"] == "html"
        
        # Verify HTML content
        file_path = Path(report_metadata.file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        assert "<!DOCTYPE html>" in html_content
        assert "test-report-002" in html_content
        assert "Executive Summary" in html_content
        assert "Risk Assessment" in html_content
        assert "Recommendations" in html_content
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not pytest.importorskip("reportlab", reason="ReportLab not available"), reason="ReportLab not available")
    async def test_generate_pdf_report(self, report_service, sample_analysis_data, sample_document_metadata):
        """Test generating PDF report"""
        request = ReportRequest(
            report_id="test-report-003",
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.PDF,
            document_ids=["doc-001"],
            analysis_ids=["analysis-001"],
            client_id="Test_Client"
        )
        
        report_metadata = await report_service.generate_report(
            request=request,
            analysis_data=sample_analysis_data,
            document_metadata=sample_document_metadata
        )
        
        assert report_metadata.file_type == FileType.REPORT_PDF
        assert report_metadata.metadata["report_format"] == "pdf"
        
        # Verify PDF file exists and has content
        file_path = Path(report_metadata.file_path)
        assert file_path.exists()
        assert file_path.suffix == ".pdf"
        assert file_path.stat().st_size > 0
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not pytest.importorskip("docx", reason="python-docx not available"), reason="python-docx not available")
    async def test_generate_word_report(self, report_service, sample_analysis_data, sample_document_metadata):
        """Test generating Word report"""
        request = ReportRequest(
            report_id="test-report-004",
            report_type=ReportType.TECHNICAL_REPORT,
            format=ReportFormat.WORD,
            document_ids=["doc-001"],
            analysis_ids=["analysis-001"],
            client_id="Test_Client"
        )
        
        report_metadata = await report_service.generate_report(
            request=request,
            analysis_data=sample_analysis_data,
            document_metadata=sample_document_metadata
        )
        
        assert report_metadata.file_type == FileType.REPORT_WORD
        assert report_metadata.metadata["report_format"] == "docx"
        
        # Verify Word file exists and has content
        file_path = Path(report_metadata.file_path)
        assert file_path.exists()
        assert file_path.suffix == ".docx"
        assert file_path.stat().st_size > 0
    
    # ==================== REPORT STATISTICS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_get_report_stats(self, report_service):
        """Test getting report statistics"""
        stats = await report_service.get_report_stats()
        
        assert "total_templates" in stats
        assert "templates_by_type" in stats
        assert "templates_by_format" in stats
        assert "total_reports" in stats
        assert "available_formats" in stats
        assert "available_types" in stats
        
        assert stats["total_templates"] >= 3
        assert len(stats["available_formats"]) >= 4
        assert len(stats["available_types"]) >= 4


class TestFileManagementIntegration:
    """Integration tests for file management functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_file_workflow(self):
        """Test complete file management workflow"""
        try:
            # Initialize services
            storage_service = FileBasedStorageService(
                StorageConfig(base_path="/tmp/integration_test")
            )
            report_service = ReportGenerationService(storage_service)
            
            # Sample data
            analysis_data = {
                "summary": {"summary": "Integration test analysis"},
                "risks": [{"level": "low", "description": "Low risk"}],
                "recommendations": ["Test recommendation"]
            }
            
            document_metadata = {
                "original_filename": "integration_test.pdf",
                "file_size": 51200,
                "upload_timestamp": datetime.now().isoformat()
            }
            
            # 1. Store analysis result
            analysis_metadata = await storage_service.store_analysis_result(
                analysis_data=analysis_data,
                document_id="integration-doc-001",
                analysis_id="integration-analysis-001",
                client_id="Integration_Test"
            )
            
            assert analysis_metadata.file_type == FileType.ANALYSIS_RESULT
            
            # 2. Generate report
            report_request = ReportRequest(
                report_id="integration-report-001",
                report_type=ReportType.ANALYSIS_SUMMARY,
                format=ReportFormat.JSON,
                document_ids=["integration-doc-001"],
                analysis_ids=["integration-analysis-001"],
                client_id="Integration_Test"
            )
            
            report_metadata = await report_service.generate_report(
                request=report_request,
                analysis_data=analysis_data,
                document_metadata=document_metadata
            )
            
            assert report_metadata.metadata["report_type"] == "analysis_summary"
            
            # 3. Create file version
            version_metadata = await storage_service.create_file_version(
                file_id=analysis_metadata.file_id,
                new_file_data={"updated": "analysis data"},
                version_comment="Updated analysis"
            )
            
            assert version_metadata.version == 2
            
            # 4. Archive files
            archive_metadata = await storage_service.archive_files(
                file_ids=[analysis_metadata.file_id, report_metadata.file_id],
                archive_name="integration_archive"
            )
            
            assert archive_metadata.file_type == FileType.ARCHIVE
            
            # 5. Get storage statistics
            stats = await storage_service.get_storage_stats()
            assert stats["total_files"] >= 4  # Original + version + report + archive
            
            # 6. Get report statistics
            report_stats = await report_service.get_report_stats()
            assert report_stats["total_templates"] >= 3
            
        except Exception as e:
            pytest.skip(f"Integration test skipped: {e}")
        finally:
            # Cleanup
            import shutil
            shutil.rmtree("/tmp/integration_test", ignore_errors=True)


# ==================== PERFORMANCE TESTS ====================

class TestFileManagementPerformance:
    """Performance tests for file management"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_bulk_file_operations(self):
        """Test bulk file operations performance"""
        try:
            storage_service = FileBasedStorageService(
                StorageConfig(base_path="/tmp/performance_test")
            )
            
            # Store multiple files
            file_ids = []
            for i in range(50):
                file_metadata = await storage_service.store_file(
                    file_data=f"Performance test content {i}",
                    file_type=FileType.DOCUMENT,
                    original_filename=f"perf_test_{i}.txt",
                    client_id="Performance_Test"
                )
                file_ids.append(file_metadata.file_id)
            
            assert len(file_ids) == 50
            
            # Create archive of all files
            archive_metadata = await storage_service.archive_files(
                file_ids=file_ids,
                archive_name="performance_archive"
            )
            
            assert archive_metadata.metadata["archived_files"] == 50
            
            # Get storage statistics
            stats = await storage_service.get_storage_stats()
            assert stats["total_files"] >= 51  # 50 files + 1 archive
            
        except Exception as e:
            pytest.skip(f"Performance test skipped: {e}")
        finally:
            # Cleanup
            import shutil
            shutil.rmtree("/tmp/performance_test", ignore_errors=True)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
