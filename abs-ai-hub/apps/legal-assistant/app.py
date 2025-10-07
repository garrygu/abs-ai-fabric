import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import json

APP_ID = "legal-assistant"

HUB_GATEWAY_URL = os.getenv("HUB_GATEWAY_URL", "http://hub-gateway:8081")

HTTP = httpx.AsyncClient()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatReq(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 1024


class RagReq(BaseModel):
    query: str
    top_k: Optional[int] = 5
    collection: Optional[str] = None
    rerank: Optional[bool] = False


class AnalyzeReq(BaseModel):
    text: str
    policy: Optional[Dict[str, Any]] = None
    model: Optional[str] = None


app = FastAPI(title="ABS Legal Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "app": APP_ID}


@app.post("/chat")
async def chat(req: ChatReq, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    try:
        headers = {"X-ABS-App-Id": app_id or APP_ID}
        resp = await HTTP.post(
            f"{HUB_GATEWAY_URL.rstrip('/')}/v1/chat/completions",
            json=req.model_dump(),
            headers=headers,
            timeout=httpx.Timeout(60.0),
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, e.response.text)
    except Exception as e:
        raise HTTPException(500, f"chat error: {str(e)}")


@app.post("/rag")
async def rag(req: RagReq, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    try:
        headers = {"X-ABS-App-Id": app_id or APP_ID}

        # Embed the query via gateway (uses catalog policy/defaults)
        emb_resp = await HTTP.post(
            f"{HUB_GATEWAY_URL.rstrip('/')}/v1/embeddings",
            json={"input": [req.query]},
            headers=headers,
            timeout=httpx.Timeout(30.0),
        )
        emb_resp.raise_for_status()
        emb = emb_resp.json()["data"][0]["embedding"]

        # Determine collection: if not provided, use the app's configured embedding model-derived collection
        collection = req.collection or "default_vectors"

        # Search in Qdrant via gateway routing
        search_payload = {
            "vector": emb,
            "limit": req.top_k or 5,
            "with_payload": True,
        }
        qdr_resp = await HTTP.post(
            f"{HUB_GATEWAY_URL.rstrip('/')}/v1/collections/{collection}/points/search",
            json=search_payload,
            headers=headers,
            timeout=httpx.Timeout(30.0),
        )
        qdr_resp.raise_for_status()
        qdr = qdr_resp.json()

        # Build context string
        hits = qdr.get("result", [])
        context_parts = []
        for hit in hits:
            try:
                context_parts.append(hit.get("payload", {}).get("text") or "")
            except Exception:
                continue
        context = "\n\n".join([c for c in context_parts if c])

        # Ask LLM with context
        chat_payload = {
            "model": None,
            "messages": [
                {"role": "system", "content": "You are a legal assistant. Use the provided context if relevant. Keep answers concise and cite sections."},
                {"role": "user", "content": f"Context for reference:\n{context}\n\nQuestion: {req.query}"},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }
        chat_resp = await HTTP.post(
            f"{HUB_GATEWAY_URL.rstrip('/')}/v1/chat/completions",
            json=chat_payload,
            headers=headers,
            timeout=httpx.Timeout(60.0),
        )
        chat_resp.raise_for_status()
        out = chat_resp.json()
        return {
            "answer": out.get("choices", [{}])[0].get("message", {}).get("content"),
            "contexts": hits,
            "model": out.get("model"),
            "provider": out.get("provider"),
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, e.response.text)
    except Exception as e:
        raise HTTPException(500, f"rag error: {str(e)}")


@app.post("/analyze")
async def analyze(req: AnalyzeReq, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    try:
        headers = {"X-ABS-App-Id": app_id or APP_ID}
        template = (
            "You are a legal contract analyst.\n"
            "Analyze the provided text and return JSON with:\n"
            "- key_clauses: array of objects {{name, snippet}}\n"
            "- risks: array of objects {{type, severity, rationale, snippet}}\n"
            "- obligations: array of strings\n"
            "- summary: string\n"
            "Be concise. Only output valid JSON."
        )
        prompt = f"{template}\n\nTEXT:\n{req.text[:20000]}"
        payload = {
            "messages": [
                {"role": "system", "content": "Return only valid minified JSON as requested."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1200,
        }
        resp = await HTTP.post(
            f"{HUB_GATEWAY_URL.rstrip('/')}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=httpx.Timeout(90.0),
        )
        resp.raise_for_status()
        txt = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
        try:
            return json.loads(txt)
        except Exception:
            # Fallback if model returns non-JSON: wrap as summary
            return {"summary": txt}
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, e.response.text)
    except Exception as e:
        raise HTTPException(500, f"analyze error: {str(e)}")


@app.get("/")
async def ui():
    return HTMLResponse(
        """
        <!doctype html>
        <html>
        <head>
          <meta charset='utf-8'>
          <meta name='viewport' content='width=device-width, initial-scale=1'>
          <title>ABS Legal Assistant</title>
          <style>
            body{font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#f6f8fb; margin:0}
            .wrap{max-width: 1000px; margin: 0 auto; padding: 24px}
            .card{background:#fff; border:1px solid #eaecef; border-radius:10px; padding:16px; margin-bottom:16px}
            .row{display:flex; gap:12px}
            .col{flex:1}
            textarea{width:100%; min-height:120px; padding:10px}
            input, select, button{padding:8px 12px}
            .messages{min-height:220px; max-height:360px; overflow:auto; background:#fafbfc; border:1px solid #eaecef; padding:10px}
            .msg{margin-bottom:10px}
            .usr{color:#1f6feb}
            .asst{color:#24292f}
            .ctx{font-size:12px; color:#57606a}
          </style>
        </head>
        <body>
          <div class='wrap'>
            <h2>ABS Legal Assistant</h2>
            <div class='card'>
              <div class='messages' id='msgs'></div>
              <div class='row'>
                <div class='col'>
                  <textarea id='q' placeholder='Ask a legal question...'></textarea>
                </div>
              </div>
              <div class='row'>
                <button onclick='sendChat()'>Send</button>
                <button onclick='askRag()'>Ask with RAG</button>
              </div>
            </div>

            <div class='card'>
              <h3>Analyze Text</h3>
              <textarea id='doc' placeholder='Paste contract or legal text to analyze'></textarea>
              <div><button onclick='analyze()'>Analyze</button></div>
              <pre id='analysis' style='white-space:pre-wrap; background:#fafbfc; padding:10px; border:1px solid #eaecef;'></pre>
            </div>
          </div>

          <script>
            const APP_ID = 'legal-assistant';
            const G = '';
            const msgs = document.getElementById('msgs');

            function addMsg(role, txt){
              const d = document.createElement('div');
              d.className = 'msg ' + (role==='user'?'usr':'asst');
              d.textContent = (role==='user'? 'You: ': 'Assistant: ') + txt;
              msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight;
            }

            async function sendChat(){
              const q = document.getElementById('q').value.trim();
              if(!q) return; addMsg('user', q);
              const payload = {messages:[{role:'user', content:q}], temperature:0.2};
              const r = await fetch(G + '/chat',{method:'POST', headers:{'Content-Type':'application/json','X-ABS-App-Id':APP_ID}, body: JSON.stringify(payload)});
              const j = await r.json();
              const a = j.choices?.[0]?.message?.content || JSON.stringify(j);
              addMsg('assistant', a);
            }

            async function askRag(){
              const q = document.getElementById('q').value.trim();
              if(!q) return; addMsg('user', q + ' (RAG)');
              const r = await fetch(G + '/rag',{method:'POST', headers:{'Content-Type':'application/json','X-ABS-App-Id':APP_ID}, body: JSON.stringify({query:q})});
              const j = await r.json();
              addMsg('assistant', j.answer || JSON.stringify(j));
              if (j.contexts) {
                const c = document.createElement('div'); c.className='ctx';
                c.textContent = 'Contexts: ' + j.contexts.length;
                msgs.appendChild(c);
              }
            }

            async function analyze(){
              const t = document.getElementById('doc').value.trim();
              if(!t) return;
              const r = await fetch(G + '/analyze',{method:'POST', headers:{'Content-Type':'application/json','X-ABS-App-Id':APP_ID}, body: JSON.stringify({text:t})});
              const j = await r.json();
              document.getElementById('analysis').textContent = JSON.stringify(j, null, 2);
            }
          </script>
        </body>
        </html>
        """
    )


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("APP_PORT", "8050")), reload=False)

