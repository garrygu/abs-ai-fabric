import os, io, json, uuid, hashlib, tempfile, subprocess
from pathlib import Path
from typing import List, Dict
import fitz  # PyMuPDF
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File
import gradio as gr
import uvicorn
import requests
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

APP_PORT = int(os.getenv("APP_PORT", "7860"))
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "contract_chunks"
HUB_GATEWAY_URL = os.getenv("HUB_GATEWAY_URL", "http://hub-gateway:8081")
POLICY_FILE = os.getenv("POLICY_FILE", "/app/policy/nda.yml")
DATA_DIR = Path(os.getenv("ABS_DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

# app.py (add/replace helpers)
from fastapi import HTTPException
from fastapi.responses import JSONResponse
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

        (DATA_DIR / f"report-{uuid.uuid4()}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return JSONResponse(status_code=200, content=result)

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

def gradio_ui():
    def _go(files):
        f = files[0] if isinstance(files, list) else files
        mime = "application/pdf" if f.name.lower().endswith(".pdf") else \
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        with open(f.name, "rb") as fh:
            r = requests.post("http://localhost:7860/api/review",
                            files={"file": (Path(f.name).name, fh, mime)},
                            timeout=300)
        try:
            return json.dumps(r.json(), ensure_ascii=False, indent=2)
        except Exception:
            return f"HTTP {r.status_code}\n{r.text[:800]}"


    return gr.Interface(
        fn=_go,
        inputs=gr.File(file_types=[".pdf", ".docx"], label="上传合同 (PDF/DOCX)"),
        outputs=gr.Code(label="审查结果（JSON）"),
        title="合同审查助手（MVP）",
        description="上传合同，自动提取关键条款、风险、缺失项，并附带引用。"
    )

if __name__ == "__main__":
    ui = gradio_ui()
    # Mount Gradio Blocks on the FastAPI app root path
    app = gr.mount_gradio_app(app, ui, path="/")
    # Run a single uvicorn server to serve FastAPI (including mounted Gradio UI)
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
