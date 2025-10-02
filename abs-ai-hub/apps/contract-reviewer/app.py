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
from sentence_transformers import SentenceTransformer

APP_PORT = int(os.getenv("APP_PORT", "7860"))
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "contract_chunks"
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
POLICY_FILE = os.getenv("POLICY_FILE", "/app/policy/nda.yml")
DATA_DIR = Path(os.getenv("ABS_DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.2:3b")

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
embedder = SentenceTransformer(EMBED_MODEL_NAME)
qdrant = QdrantClient(url=QDRANT_URL)
try:
    qdrant.get_collection(COLLECTION)
except Exception:
    qdrant.recreate_collection(
        COLLECTION,
        vectors_config=VectorParams(size=embedder.get_sentence_embedding_dimension(), distance=Distance.COSINE)
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
    vectors = embedder.encode(chunks).tolist()
    ids = [str(uuid.uuid4()) for _ in chunks]
    qdrant.upsert(
        COLLECTION,
        points=[{"id": ids[i], "vector": vectors[i], "payload": {"text": chunks[i]}} for i in range(len(chunks))]
    )

def retrieve(query: str, top_k=6) -> List[str]:
    qvec = embedder.encode([query])[0].tolist()
    res = qdrant.search(COLLECTION, query_vector=qvec, limit=top_k)
    return [hit.payload["text"] for hit in res]

def openai_chat(messages, max_tokens=1024) -> str:
    # Ollama API
    url = f"{OLLAMA_API_BASE}/api/chat"
    payload = {
        "model": CHAT_MODEL,
        "messages": messages,
        "options": {
            "temperature": 0.2,
            "num_predict": max_tokens
        }
    }
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"]

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

    try:
        data = json.loads(rsp)
    except Exception:
        # fallback: wrap text as JSON field
        data = {"summary": rsp, "raw": rsp}

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
        chunks = chunk_text(text);  upsert_chunks(chunks)

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
