"""
Example integration of Document Service with Contract Reviewer v2
Shows how to replace Redis-only storage with PostgreSQL persistence
"""

import asyncio
from pathlib import Path
from document_service import DocumentService
from document_api import integrate_with_contract_reviewer
from fastapi import FastAPI, UploadFile, File, HTTPException
import json


class ContractReviewerWithPersistence:
    """Enhanced Contract Reviewer with PostgreSQL persistence"""
    
    def __init__(self):
        self.doc_service = DocumentService()
        self.app = FastAPI(title="Contract Reviewer v2 with Persistence")
        
        # Integrate document management API
        integrate_with_contract_reviewer(self.app)
    
    async def initialize(self):
        """Initialize the service"""
        await self.doc_service.initialize()
        print("✅ Contract Reviewer v2 with PostgreSQL persistence initialized")
    
    async def close(self):
        """Close the service"""
        await self.doc_service.close()
    
    async def analyze_contract_with_persistence(
        self,
        file_path: str,
        original_filename: str,
        analysis_data: dict,
        model_used: str = "llama3.2:3b",
        processing_time_ms: int = 1500
    ) -> dict:
        """
        Analyze a contract and persist results to PostgreSQL
        
        This replaces the Redis-only approach with full persistence
        """
        try:
            # 1. Create document record in PostgreSQL
            document = await self.doc_service.create_document(
                file_path=file_path,
                original_filename=original_filename,
                metadata={
                    "analysis_type": "contract_review",
                    "model_used": model_used,
                    "processing_time_ms": processing_time_ms
                }
            )
            
            document_id = document["id"]
            print(f"📄 Created document record: {document_id}")
            
            # 2. Create analysis result in PostgreSQL
            analysis_result = await self.doc_service.create_analysis_result(
                document_id=document_id,
                analysis_type="contract_review",
                analysis_data=analysis_data,
                model_used=model_used,
                processing_time_ms=processing_time_ms
            )
            
            analysis_id = analysis_result["id"]
            print(f"🔍 Created analysis result: {analysis_id}")
            
            # 3. Return combined result
            return {
                "document_id": document_id,
                "analysis_id": analysis_id,
                "document": document,
                "analysis": analysis_result,
                "status": "completed"
            }
            
        except Exception as e:
            print(f"❌ Error in contract analysis: {e}")
            raise
    
    async def get_document_analysis_history(self, document_id: str) -> list:
        """Get analysis history for a document"""
        try:
            analyses = await self.doc_service.get_analysis_results_by_document(
                document_id=document_id,
                analysis_type="contract_review"
            )
            return analyses
        except Exception as e:
            print(f"❌ Error getting analysis history: {e}")
            return []
    
    async def get_user_documents(self, limit: int = 10, offset: int = 0) -> tuple:
        """Get user's documents with pagination"""
        try:
            documents, total_count = await self.doc_service.get_documents(
                limit=limit,
                offset=offset,
                order_by="upload_timestamp",
                order_direction="DESC"
            )
            return documents, total_count
        except Exception as e:
            print(f"❌ Error getting user documents: {e}")
            return [], 0


# ==================== EXAMPLE USAGE ====================

async def example_contract_analysis():
    """Example of analyzing a contract with persistence"""
    
    # Initialize the enhanced contract reviewer
    reviewer = ContractReviewerWithPersistence()
    await reviewer.initialize()
    
    try:
        # Simulate contract analysis
        sample_analysis_data = {
            "summary": "This is a standard NDA contract with typical confidentiality provisions.",
            "document_type": "Non-Disclosure Agreement",
            "key_points": [
                "Confidentiality period: 2 years",
                "Governing law: California",
                "Dispute resolution: Arbitration"
            ],
            "risks": [
                {
                    "level": "low",
                    "description": "Standard confidentiality clause",
                    "rationale": "Typical NDA language"
                }
            ],
            "recommendations": [
                "Review confidentiality period",
                "Consider adding return of materials clause"
            ],
            "citations": [
                "Section 2.1: Confidentiality obligations",
                "Section 4.2: Term and termination"
            ]
        }
        
        # Create a temporary file for testing
        with open("/tmp/sample_contract.pdf", "w") as f:
            f.write("Sample contract content")
        
        # Analyze contract with persistence
        result = await reviewer.analyze_contract_with_persistence(
            file_path="/tmp/sample_contract.pdf",
            original_filename="sample_contract.pdf",
            analysis_data=sample_analysis_data,
            model_used="llama3.2:3b",
            processing_time_ms=1500
        )
        
        print(f"✅ Analysis completed:")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Analysis ID: {result['analysis_id']}")
        print(f"   Status: {result['status']}")
        
        # Get analysis history
        history = await reviewer.get_document_analysis_history(result['document_id'])
        print(f"📊 Analysis history: {len(history)} analyses")
        
        # Get user documents
        documents, total = await reviewer.get_user_documents(limit=5)
        print(f"📋 User documents: {len(documents)} of {total} total")
        
        # Clean up
        Path("/tmp/sample_contract.pdf").unlink(missing_ok=True)
        
    finally:
        await reviewer.close()


# ==================== MIGRATION FROM REDIS-ONLY ====================

class MigrationHelper:
    """Helper class to migrate from Redis-only to PostgreSQL persistence"""
    
    def __init__(self):
        self.doc_service = DocumentService()
    
    async def migrate_redis_analysis_to_postgres(self, redis_data: dict) -> dict:
        """
        Migrate analysis data from Redis format to PostgreSQL format
        
        Args:
            redis_data: Analysis data from Redis cache
            
        Returns:
            PostgreSQL-compatible analysis data
        """
        try:
            # Extract document information
            document_info = {
                "original_filename": redis_data.get("file_name", "unknown.pdf"),
                "metadata": {
                    "migrated_from_redis": True,
                    "redis_analysis_id": redis_data.get("analysis_id"),
                    "migration_timestamp": "2024-01-01T00:00:00"
                }
            }
            
            # Extract analysis data
            analysis_data = {
                "summary": redis_data.get("summary", {}).get("summary", ""),
                "document_type": redis_data.get("summary", {}).get("document_type", "Contract"),
                "key_points": redis_data.get("summary", {}).get("key_points", []),
                "risks": redis_data.get("summary", {}).get("risks", []),
                "recommendations": redis_data.get("summary", {}).get("recommendations", []),
                "citations": redis_data.get("summary", {}).get("citations", [])
            }
            
            # Create document record
            document = await self.doc_service.create_document(
                file_path="/migrated/from_redis",  # Placeholder path
                original_filename=document_info["original_filename"],
                metadata=document_info["metadata"]
            )
            
            # Create analysis result
            analysis_result = await self.doc_service.create_analysis_result(
                document_id=document["id"],
                analysis_type="contract_review",
                analysis_data=analysis_data,
                model_used=redis_data.get("model_used", "llama3.2:3b"),
                processing_time_ms=redis_data.get("processing_time_ms", 0)
            )
            
            return {
                "document_id": document["id"],
                "analysis_id": analysis_result["id"],
                "migration_status": "success"
            }
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return {"migration_status": "failed", "error": str(e)}


# ==================== INTEGRATION WITH EXISTING APP ====================

def integrate_with_existing_app(existing_app: FastAPI):
    """
    Integrate document persistence with existing Contract Reviewer v2 app
    
    Usage:
        from contract_reviewer_persistence import integrate_with_existing_app
        integrate_with_existing_app(app)
    """
    
    # Add document management endpoints
    integrate_with_contract_reviewer(existing_app)
    
    # Add custom endpoints for Contract Reviewer v2
    @existing_app.post("/api/analyze-with-persistence")
    async def analyze_with_persistence(
        file: UploadFile = File(...),
        metadata: str = None
    ):
        """Enhanced analyze endpoint with PostgreSQL persistence"""
        try:
            # Parse metadata
            parsed_metadata = None
            if metadata:
                parsed_metadata = json.loads(metadata)
            
            # Save uploaded file
            with open(f"/tmp/{file.filename}", "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Initialize document service
            doc_service = DocumentService()
            await doc_service.initialize()
            
            try:
                # Create document record
                document = await doc_service.create_document(
                    file_path=f"/tmp/{file.filename}",
                    original_filename=file.filename,
                    metadata=parsed_metadata
                )
                
                # TODO: Add actual contract analysis logic here
                # For now, return the document record
                return {
                    "status": "success",
                    "document_id": document["id"],
                    "message": "Document uploaded and ready for analysis"
                }
                
            finally:
                await doc_service.close()
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run example
    asyncio.run(example_contract_analysis())
