import os, io, json, uuid, hashlib, tempfile, subprocess
from pathlib import Path
from typing import List, Dict, Optional
import fitz  # PyMuPDF
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import gradio as gr
import uvicorn
import requests
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from datetime import datetime
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

APP_PORT = int(os.getenv("APP_PORT", "7860"))
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "contract_chunks"
HUB_GATEWAY_URL = os.getenv("HUB_GATEWAY_URL", "http://hub-gateway:8081")
POLICY_FILE = os.getenv("POLICY_FILE", "/app/policy/nda.yml")
DATA_DIR = Path(os.getenv("ABS_DATA_DIR", "/data"))
REPORTS_DIR = DATA_DIR / "reports"
UPLOADS_DIR = DATA_DIR / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Global state for review history
review_history = []
executor = ThreadPoolExecutor(max_workers=4)

from docx import Document as DocxDocument

ALLOWED_EXTS = {".pdf", ".docx"}

def read_docx_text(path: Path) -> str:
    doc = DocxDocument(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text)

def read_any_text(path: Path) -> tuple[str, str]:
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}. Please upload PDF or DOCX.")
    if ext == ".pdf":
        pdf_path = ocr_if_scanned(path)
        return read_pdf_text(pdf_path), "pdf"
    return read_docx_text(path), "docx"



# ----- models/clients -----
qdrant = QdrantClient(url=QDRANT_URL)

# Initialize collection with default embedding dimension (will be updated on first use)
EMBED_DIM = 384  # Default for bge-small-en-v1.5
try:
    qdrant.get_collection(COLLECTION)
except Exception:
    qdrant.recreate_collection(
        COLLECTION,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE)
    )

def sha256_of_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def ocr_if_scanned(pdf_path: Path) -> Path:
    out = pdf_path.with_suffix(".ocr.pdf")
    try:
        subprocess.run(["ocrmypdf", "--skip-text", str(pdf_path), str(out)], check=True)
        return out if out.exists() else pdf_path
    except Exception:
        return pdf_path

def read_pdf_text(path: Path) -> str:
    doc = fitz.open(str(path))
    texts = []
    for page in doc:
        texts.append(page.get_text())
    return "\n".join(texts)

def chunk_text(text: str, max_chars=1200, overlap=120):
    chunks = []
    i=0
    while i < len(text):
        chunk = text[i:i+max_chars]
        chunks.append(chunk)
        i += max_chars - overlap
    return chunks

def upsert_chunks(chunks: List[str]):
    # Get embeddings from Hub Gateway
    response = requests.post(
        f"{HUB_GATEWAY_URL}/v1/embeddings",
        headers={"X-ABS-App-Id": "contract-reviewer"},
        json={"input": chunks},
        timeout=60
    )
    response.raise_for_status()
    embeddings_data = response.json()
    
    vectors = [item["embedding"] for item in embeddings_data["data"]]
    ids = [str(uuid.uuid4()) for _ in chunks]
    qdrant.upsert(
        COLLECTION,
        points=[{"id": ids[i], "vector": vectors[i], "payload": {"text": chunks[i]}} for i in range(len(chunks))]
    )

def retrieve(query: str, top_k=6) -> List[str]:
    # Get query embedding from Hub Gateway
    response = requests.post(
        f"{HUB_GATEWAY_URL}/v1/embeddings",
        headers={"X-ABS-App-Id": "contract-reviewer"},
        json={"input": [query]},
        timeout=60
    )
    response.raise_for_status()
    embeddings_data = response.json()
    
    qvec = embeddings_data["data"][0]["embedding"]
    res = qdrant.search(COLLECTION, query_vector=qvec, limit=top_k)
    return [hit.payload["text"] for hit in res]

def openai_chat(messages, max_tokens=1024) -> str:
    # Use Hub Gateway for chat completions
    response = requests.post(
        f"{HUB_GATEWAY_URL}/v1/chat/completions",
        headers={"X-ABS-App-Id": "contract-reviewer"},
        json={
        "messages": messages,
            "temperature": 0.2,
            "max_tokens": max_tokens
        },
        timeout=120
    )
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]

def review_contract(text: str, policy: str) -> Dict:
    # collect context via retrieval queries for common clauses
    queries = [
        "Confidentiality clause", "Liability limitation", "Indemnity",
        "Intellectual Property ownership", "Termination", "Governing Law",
        "Assignment", "Data Protection / Privacy"
    ]
    contexts = []
    for q in queries:
        contexts.extend(retrieve(q))
    context = "\n---\n".join(contexts[:12])

    with open("/app/prompts/review_prompt.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()

    user_prompt = f"""POLICY:\n{policy}\n\nCONTEXT:\n{context}\n"""
    rsp = openai_chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ], max_tokens=int(os.getenv("MAX_TOKENS", "1024")))

    # Debug: Log the raw response
    print(f"DEBUG: Raw LLM response: {repr(rsp)}")
    
    try:
        # Try to extract JSON from the response
        # Look for JSON object in the response
        import re
        json_match = re.search(r'\{.*\}', rsp, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            print(f"DEBUG: Extracted JSON string: {repr(json_str)}")
            data = json.loads(json_str)
        else:
            # If no JSON found, wrap the response
            print("DEBUG: No JSON found in response")
            data = {"summary": rsp, "raw": rsp}
    except json.JSONDecodeError as e:
        # If JSON parsing fails, wrap the response
        print(f"DEBUG: JSON parsing failed: {str(e)}")
        data = {"summary": rsp, "raw": rsp, "error": f"JSON parsing failed: {str(e)}"}
    except Exception as e:
        # Any other error
        print(f"DEBUG: Processing failed: {str(e)}")
        data = {"summary": rsp, "raw": rsp, "error": f"Processing failed: {str(e)}"}

    return data

# -------- FastAPI + Gradio --------
app = FastAPI()

class ReviewResponse(BaseModel):
    summary: str
    clauses: list | None = None
    risks: list | None = None
    missing: list | None = None
    citations: list | None = None
    input_sha256: str

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/api/history")
def get_history():
    """Get review history"""
    return {"history": review_history[-50:]}  # Last 50 reviews

@app.get("/api/reports/{report_id}")
def get_report(report_id: str):
    """Get a specific report by ID"""
    report_file = REPORTS_DIR / f"report-{report_id}.json"
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    with open(report_file, "r", encoding="utf-8") as f:
        return json.load(f)

@app.delete("/api/reports/{report_id}")
def delete_report(report_id: str):
    """Delete a specific report"""
    report_file = REPORTS_DIR / f"report-{report_id}.json"
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_file.unlink()
    
    # Remove from history
    global review_history
    review_history = [h for h in review_history if h["id"] != report_id]
    
    return {"message": "Report deleted successfully"}

# Remove:  @app.post("/api/review", response_model=ReviewResponse)
@app.post("/api/review")
async def api_review(file: UploadFile = File(...)):
    try:
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Empty file.")

        ext = Path(file.filename).suffix or ".pdf"
        upath = DATA_DIR / f"upload-{uuid.uuid4()}{ext}"
        upath.write_bytes(raw)
        input_hash = sha256_of_bytes(raw)

        text, kind = read_any_text(upath)
        print(f"DEBUG: Text extracted, length: {len(text)}")
        chunks = chunk_text(text)
        print(f"DEBUG: Text chunked into {len(chunks)} chunks")
        upsert_chunks(chunks)
        print("DEBUG: Chunks upserted to Qdrant")

        policy = Path(POLICY_FILE).read_text(encoding="utf-8")
        result = review_contract(text, policy)
        result.update({"input_sha256": input_hash, "file_kind": kind})

        # Save report to reports directory
        report_id = str(uuid.uuid4())
        report_file = REPORTS_DIR / f"report-{report_id}.json"
        report_data = {
            **result,
            "report_id": report_id,
            "timestamp": datetime.now().isoformat(),
            "file_name": file.filename,
            "file_size": len(raw),
            "file_type": kind
        }
        report_file.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # Add to history
        review_history.append({
            "id": report_id,
            "filename": file.filename,
            "timestamp": datetime.now().isoformat(),
            "summary": result.get("summary", ""),
            "risks_count": len(result.get("risks", [])),
            "file_size": len(raw)
        })
        
        return JSONResponse(status_code=200, content=report_data)

    except HTTPException as he:
        # clean JSON, no bytes
        return JSONResponse(status_code=he.status_code, content={"error": he.detail})
    except Exception as e:
        # last-resort error message (string only)
        print(f"ERROR in review endpoint: {str(e)}")
        print(f"ERROR type: {type(e)}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        return JSONResponse(status_code=400, content={"error": str(e)})

def create_modern_ui():
    """Create a modern, production-ready UI using Gradio Blocks"""
    
    # Custom CSS for modern styling
    custom_css = """
    .gradio-container {
        max-width: 1200px !important;
        margin: 0 auto !important;
    }
    .upload-section {
        border: 2px dashed #e1e5e9;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: #f8f9fa;
        transition: all 0.3s ease;
    }
    .upload-section:hover {
        border-color: #007bff;
        background: #e3f2fd;
    }
    .result-section {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-top: 1rem;
    }
    .risk-high { color: #dc3545; font-weight: bold; }
    .risk-medium { color: #fd7e14; font-weight: bold; }
    .risk-low { color: #28a745; font-weight: bold; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    """
    
    def process_document(file):
        """Process uploaded document"""
        if file is None:
            return None, "Please upload a document first.", "", "", ""
        
        try:
            mime = "application/pdf" if file.name.lower().endswith(".pdf") else \
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            with open(file.name, "rb") as fh:
                response = requests.post("http://localhost:7860/api/review",
                                       files={"file": (Path(file.name).name, fh, mime)},
                            timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                return format_results(result), create_summary_html(result), create_risks_html(result), create_recommendations_html(result), result.get("report_id", "")
            else:
                return None, f"Error: {response.status_code} - {response.text[:500]}", "", "", ""
                
        except Exception as e:
            return None, f"Error processing document: {str(e)}", "", "", ""
    
    def format_results(result):
        """Format results as JSON"""
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def create_summary_html(result):
        """Create HTML summary with better formatting"""
        summary = result.get("summary", "No summary available")
        doc_type = result.get("document_type", "Unknown")
        key_points = result.get("key_points", [])
        
        # Clean and format the summary text
        def format_text(text, max_length=500):
            """Format text for better readability"""
            if len(text) <= max_length:
                return text
            
            # Find the last complete sentence within the limit
            truncated = text[:max_length]
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            
            # Use the last complete sentence or paragraph
            if last_period > max_length * 0.7:
                return text[:last_period + 1] + "..."
            elif last_newline > max_length * 0.7:
                return text[:last_newline] + "..."
            else:
                return text[:max_length] + "..."
        
        # Format the summary with proper line breaks and structure
        formatted_summary = format_text(summary)
        
        # Add line breaks for better readability
        formatted_summary = formatted_summary.replace('. ', '.<br>')
        formatted_summary = formatted_summary.replace('\n', '<br>')
        
        # Determine document type with better formatting
        type_display = {
            "Contract": "📋 Contract",
            "Technical Document": "📊 Technical Document", 
            "Policy": "📜 Policy",
            "Other": "📄 Document"
        }.get(doc_type, f"📄 {doc_type}")
        
        html = f"""
        <div class="result-section">
            <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
                <h3 style="margin: 0; color: #2c3e50;">📄 Document Summary</h3>
            </div>
            
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-weight: 600; color: #495057; margin-right: 0.5rem;">Document Type:</span>
                    <span style="background: #e3f2fd; color: #1565c0; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.9rem; font-weight: 500;">
                        {type_display}
                    </span>
                </div>
            </div>
            
            <div style="margin-bottom: 1.5rem;">
                <h4 style="color: #34495e; margin-bottom: 0.75rem; font-size: 1.1rem;">📝 Executive Summary</h4>
                <div style="background: white; padding: 1.25rem; border-left: 4px solid #3498db; border-radius: 0 8px 8px 0; line-height: 1.6; color: #2c3e50;">
                    {formatted_summary}
                </div>
            </div>
        """
        
        if key_points:
            html += f"""
            <div>
                <h4 style="color: #34495e; margin-bottom: 0.75rem; font-size: 1.1rem;">🎯 Key Points</h4>
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 1rem;">
                    <ul style="margin: 0; padding-left: 1.5rem; color: #856404;">
            """
            for point in key_points:
                # Format key points for better readability
                formatted_point = point.replace('. ', '.<br>') if len(point) > 100 else point
                html += f"<li style='margin-bottom: 0.5rem; line-height: 1.5;'>{formatted_point}</li>"
            html += """
                    </ul>
                </div>
            </div>
            """
        
        html += "</div>"
        return html
    
    def create_risks_html(result):
        """Create HTML for risks with better formatting"""
        risks = result.get("risks", [])
        if not risks:
            return """
            <div class="result-section">
                <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
                    <h3 style="margin: 0; color: #2c3e50;">⚠️ Risk Analysis</h3>
                </div>
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 1.5rem; text-align: center;">
                    <div style="color: #155724; font-size: 1.1rem; font-weight: 500;">
                        ✅ No significant risks identified
                    </div>
                    <div style="color: #6c757d; margin-top: 0.5rem; font-size: 0.9rem;">
                        This document appears to be low risk based on the analysis.
                    </div>
                </div>
            </div>
            """
        
        # Count risks by level
        risk_counts = {"high": 0, "medium": 0, "low": 0}
        for risk in risks:
            level = risk.get("level", "Low").lower()
            if level in risk_counts:
                risk_counts[level] += 1
        
        html = f"""
        <div class="result-section">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
                <h3 style="margin: 0; color: #2c3e50;">⚠️ Risk Analysis</h3>
                <div style="display: flex; gap: 0.5rem;">
        """
        
        # Add risk level badges
        for level, count in risk_counts.items():
            if count > 0:
                colors = {
                    "high": {"bg": "#f8d7da", "text": "#721c24", "border": "#dc3545"},
                    "medium": {"bg": "#fff3cd", "text": "#856404", "border": "#fd7e14"},
                    "low": {"bg": "#d4edda", "text": "#155724", "border": "#28a745"}
                }
                color = colors[level]
                html += f"""
                <span style="background: {color['bg']}; color: {color['text']}; border: 1px solid {color['border']}; 
                           padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 500;">
                    {level.upper()}: {count}
                </span>
                """
        
        html += """
                </div>
            </div>
        """
        
        for i, risk in enumerate(risks, 1):
            level = risk.get("level", "Low").lower()
            description = risk.get("description", "No description provided")
            rationale = risk.get("rationale", "No rationale provided")
            
            # Format text for better readability
            description = description.replace('. ', '.<br>') if len(description) > 150 else description
            rationale = rationale.replace('. ', '.<br>') if len(rationale) > 150 else rationale
            
            colors = {
                "high": {"border": "#dc3545", "bg": "#f8d7da", "badge": "#dc3545"},
                "medium": {"border": "#fd7e14", "bg": "#fff3cd", "badge": "#fd7e14"},
                "low": {"border": "#28a745", "bg": "#d4edda", "badge": "#28a745"}
            }
            color = colors.get(level, colors["low"])
            
            html += f"""
            <div style="margin-bottom: 1.25rem; border: 1px solid {color['border']}; border-radius: 8px; 
                        background: {color['bg']}; overflow: hidden;">
                <div style="background: {color['badge']}; color: white; padding: 0.75rem 1rem; font-weight: 600; 
                            font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px;">
                    Risk #{i} • {level.upper()} Priority
                </div>
                <div style="padding: 1rem;">
                    <div style="margin-bottom: 0.75rem;">
                        <div style="font-weight: 600; color: #2c3e50; margin-bottom: 0.25rem; font-size: 1rem;">
                            📋 Issue Description
                        </div>
                        <div style="color: #495057; line-height: 1.5;">
                            {description}
                        </div>
                    </div>
                    <div>
                        <div style="font-weight: 600; color: #2c3e50; margin-bottom: 0.25rem; font-size: 1rem;">
                            💡 Rationale
                        </div>
                        <div style="color: #6c757d; line-height: 1.5; font-style: italic;">
                            {rationale}
                        </div>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
        return html
    
    def create_recommendations_html(result):
        """Create HTML for recommendations with better formatting"""
        recommendations = result.get("recommendations", [])
        citations = result.get("citations", [])
        
        html = f"""
        <div class="result-section">
            <div style="display: flex; align-items: center; margin-bottom: 1.5rem;">
                <h3 style="margin: 0; color: #2c3e50;">💡 Recommendations & Citations</h3>
            </div>
        """
        
        if recommendations:
            html += f"""
            <div style="margin-bottom: 2rem;">
                <h4 style="color: #34495e; margin-bottom: 1rem; font-size: 1.1rem; display: flex; align-items: center;">
                    🎯 Action Items ({len(recommendations)})
                </h4>
                <div style="background: #e8f5e8; border: 1px solid #c3e6cb; border-radius: 8px; padding: 1rem;">
            """
            
            for i, rec in enumerate(recommendations, 1):
                # Format recommendations for better readability
                formatted_rec = rec.replace('. ', '.<br>') if len(rec) > 100 else rec
                html += f"""
                <div style="margin-bottom: 1rem; padding: 0.75rem; background: white; border-radius: 6px; 
                            border-left: 4px solid #28a745;">
                    <div style="display: flex; align-items: flex-start;">
                        <span style="background: #28a745; color: white; width: 24px; height: 24px; border-radius: 50%; 
                                     display: flex; align-items: center; justify-content: center; font-size: 0.8rem; 
                                     font-weight: 600; margin-right: 0.75rem; flex-shrink: 0; margin-top: 0.125rem;">
                            {i}
                        </span>
                        <div style="color: #2c3e50; line-height: 1.5;">
                            {formatted_rec}
                        </div>
                    </div>
                </div>
                """
            
            html += """
                </div>
            </div>
            """
        else:
            html += """
            <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 1.5rem; 
                        text-align: center; margin-bottom: 2rem;">
                <div style="color: #6c757d; font-size: 1rem;">
                    ℹ️ No specific recommendations provided for this document.
                </div>
            </div>
            """
        
        if citations:
            html += f"""
            <div>
                <h4 style="color: #34495e; margin-bottom: 1rem; font-size: 1.1rem; display: flex; align-items: center;">
                    📚 Document Citations ({len(citations)})
                </h4>
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 1rem;">
            """
            
            for i, citation in enumerate(citations, 1):
                section = citation.get('section', 'Unknown Section')
                text = citation.get('text', 'No text available')
                
                # Format citation text for better readability
                formatted_text = text.replace('. ', '.<br>') if len(text) > 120 else text
                
                html += f"""
                <div style="margin-bottom: 1rem; padding: 0.75rem; background: white; border-radius: 6px; 
                            border-left: 4px solid #ffc107;">
                    <div style="display: flex; align-items: flex-start;">
                        <span style="background: #ffc107; color: #212529; width: 24px; height: 24px; border-radius: 50%; 
                                     display: flex; align-items: center; justify-content: center; font-size: 0.8rem; 
                                     font-weight: 600; margin-right: 0.75rem; flex-shrink: 0; margin-top: 0.125rem;">
                            {i}
                        </span>
                        <div>
                            <div style="font-weight: 600; color: #856404; margin-bottom: 0.25rem; font-size: 0.9rem;">
                                📍 {section}
                            </div>
                            <div style="color: #495057; line-height: 1.5; font-style: italic;">
                                "{formatted_text}"
                            </div>
                        </div>
                    </div>
                </div>
                """
            
            html += """
                </div>
            </div>
            """
        else:
            html += """
            <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 1.5rem; 
                        text-align: center;">
                <div style="color: #6c757d; font-size: 1rem;">
                    ℹ️ No specific citations found in this document.
                </div>
            </div>
            """
        
        html += "</div>"
        return html
    
    def get_history_data():
        """Get review history"""
        try:
            response = requests.get("http://localhost:7860/api/history")
            if response.status_code == 200:
                history = response.json().get("history", [])
                if not history:
                    return "No review history available."
                
                html = """
                <div class="result-section">
                    <h3>📋 Review History</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 0.5rem; border: 1px solid #dee2e6;">File</th>
                                <th style="padding: 0.5rem; border: 1px solid #dee2e6;">Date</th>
                                <th style="padding: 0.5rem; border: 1px solid #dee2e6;">Summary</th>
                                <th style="padding: 0.5rem; border: 1px solid #dee2e6;">Risks</th>
                            </tr>
                        </thead>
                        <tbody>
                """
                
                for item in history[-10:]:  # Show last 10
                    date = datetime.fromisoformat(item["timestamp"]).strftime("%Y-%m-%d %H:%M")
                    html += f"""
                    <tr>
                        <td style="padding: 0.5rem; border: 1px solid #dee2e6;">{item["filename"]}</td>
                        <td style="padding: 0.5rem; border: 1px solid #dee2e6;">{date}</td>
                        <td style="padding: 0.5rem; border: 1px solid #dee2e6;">{item["summary"][:100]}...</td>
                        <td style="padding: 0.5rem; border: 1px solid #dee2e6;">{item["risks_count"]}</td>
                    </tr>
                    """
                
                html += "</tbody></table></div>"
                return html
            else:
                return "Error loading history."
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Create the modern UI
    with gr.Blocks(css=custom_css, title="Contract Review Assistant") as demo:
        gr.Markdown("""
        # 📋 Contract Review Assistant
        **AI-Powered Document Analysis & Risk Assessment**
        
        Upload your contracts and documents for comprehensive analysis, risk assessment, and actionable recommendations.
        """)
        
        with gr.Tabs():
            # Main Review Tab
            with gr.Tab("🔍 Document Review"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📤 Upload Document")
                        file_input = gr.File(
                            label="Upload PDF or DOCX file",
                            file_types=[".pdf", ".docx"],
                            file_count="single"
                        )
                        
                        process_btn = gr.Button("🚀 Analyze Document", variant="primary", size="lg")
                        
                        gr.Markdown("""
                        ### 📊 Supported Features
                        - **Document Analysis**: Extract key information and structure
                        - **Risk Assessment**: Identify potential risks and issues
                        - **Smart Recommendations**: Get actionable insights
                        - **Citation Tracking**: Find relevant sections and quotes
                        - **Export Options**: Download reports in multiple formats
                        """)
                    
                    with gr.Column(scale=2):
                        gr.Markdown("### 📋 Analysis Results")
                        
                        with gr.Row():
                            with gr.Column():
                                summary_html = gr.HTML(label="Summary")
                            with gr.Column():
                                risks_html = gr.HTML(label="Risk Analysis")
                        
                        recommendations_html = gr.HTML(label="Recommendations")
                        
                        with gr.Row():
                            json_output = gr.Code(label="Raw JSON Results", language="json")
                            report_id_output = gr.Textbox(label="Report ID", visible=False)
            
            # History Tab
            with gr.Tab("📚 Review History"):
                history_btn = gr.Button("🔄 Refresh History", variant="secondary")
                history_html = gr.HTML(label="History")
            
            # Settings Tab
            with gr.Tab("⚙️ Settings"):
                gr.Markdown("### 🔧 Application Settings")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("""
                        **Processing Options:**
                        - Document chunk size: 1200 characters
                        - Overlap: 120 characters
                        - Embedding model: all-minilm
                        - Chat model: llama3.2:3b
                        """)
                    
                    with gr.Column():
                        gr.Markdown("""
                        **System Status:**
                        - Hub Gateway: Connected
                        - Vector Database: Active
                        - Cache: Enabled
                        - Reports: Stored locally
                        """)
                
                gr.Markdown("### 📁 Data Management")
                with gr.Row():
                    clear_history_btn = gr.Button("🗑️ Clear History", variant="stop")
                    export_data_btn = gr.Button("📤 Export Data", variant="secondary")
        
        # Event handlers
        process_btn.click(
            fn=process_document,
            inputs=[file_input],
            outputs=[json_output, summary_html, risks_html, recommendations_html, report_id_output]
        )
        
        history_btn.click(
            fn=get_history_data,
            outputs=[history_html]
        )
        
        # Load history on tab switch
        demo.load(
            fn=get_history_data,
            outputs=[history_html]
        )
    
    return demo

if __name__ == "__main__":
    ui = create_modern_ui()
    # Mount Gradio Blocks on the FastAPI app root path
    app = gr.mount_gradio_app(app, ui, path="/")
    # Run a single uvicorn server to serve FastAPI (including mounted Gradio UI)
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
