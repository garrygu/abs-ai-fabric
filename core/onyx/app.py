import os
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://vllm:8000/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "abs-local")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# HTTP client for forwarding requests
HTTP_CLIENT = httpx.AsyncClient()

# Placeholder for a simple in-memory "knowledge base"
KNOWLEDGE_BASE = {}

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatReq(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "llama3.1:8b"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024

# Create FastAPI app
app = FastAPI(title="Onyx AI Assistant", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Onyx AI Assistant is running"}

@app.post("/chat")
async def chat_with_llm(req: ChatReq, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """
    Handles chat requests, forwarding them to the appropriate LLM (Ollama or OpenAI-compatible).
    This is a simplified example; a real Onyx would have more sophisticated routing and RAG.
    """
    logger.info(f"Received chat request from app_id: {app_id} for model: {req.model}")
    
    # Determine which LLM to use (simplified logic)
    llm_base_url = OLLAMA_BASE_URL
    headers = {}
    if "openai" in req.model.lower() or "vllm" in req.model.lower(): # Example for routing
        llm_base_url = OPENAI_BASE_URL
        headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
        # Adjust payload for OpenAI compatibility if needed
        payload = req.model_dump()
        endpoint = f"{llm_base_url.rstrip('/')}/chat/completions"
    else: # Assume Ollama
        payload = {
            "model": req.model,
            "messages": [m.model_dump() for m in req.messages],
            "stream": False,
            "options": {"temperature": req.temperature}
        }
        endpoint = f"{llm_base_url.rstrip('/')}/api/chat"

    try:
        response = await HTTP_CLIENT.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        
        if "ollama" in llm_base_url:
            # Normalize Ollama response to OpenAI-like format
            ollama_data = response.json()
            text = ollama_data.get("message", {}).get("content", ollama_data.get("response", ""))
            return {
                "id": "chatcmpl_onyx",
                "object": "chat.completion",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text}}],
                "model": req.model,
                "provider": "ollama"
            }
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM service error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Error forwarding chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Onyx chat internal error: {str(e)}")

@app.post("/rag")
async def rag_query(request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """
    Performs a RAG query. This is a placeholder.
    A real RAG implementation would query Qdrant, retrieve context, and then query an LLM.
    """
    payload = await request.json()
    query = payload.get("query")
    collection = payload.get("collection", "default_collection")
    top_k = payload.get("top_k", 5)

    logger.info(f"Received RAG query from app_id: {app_id} for query: {query} in collection: {collection}")

    # Placeholder: Simulate Qdrant search
    try:
        # In a real scenario, you'd first embed the query, then search Qdrant
        # For now, we'll just simulate a response
        search_results = [{"id": "doc1", "payload": {"text": "Simulated RAG document content."}}]

        context = " ".join([res["payload"]["text"] for res in search_results])
        
        # Simulate LLM call with context
        llm_response = await chat_with_llm(ChatReq(
            messages=[
                ChatMessage(role="system", content=f"You are an AI assistant. Use the following context to answer: {context}"),
                ChatMessage(role="user", content=query)
            ],
            model="llama3.1:8b"
        ))
        return {"response": llm_response["choices"][0]["message"]["content"], "context": search_results}
    except Exception as e:
        logger.error(f"Error during RAG query: {e}")
        raise HTTPException(status_code=500, detail=f"Onyx RAG internal error: {str(e)}")

@app.post("/ingest")
async def ingest_documents(request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """
    Ingests documents into the knowledge base. This is a placeholder.
    A real ingestion would embed documents and upsert to Qdrant.
    """
    payload = await request.json()
    documents = payload.get("documents", [])
    collection = payload.get("collection", "default_collection")

    logger.info(f"Received ingest request from app_id: {app_id} for {len(documents)} documents into collection: {collection}")

    # Placeholder: Simulate embedding and Qdrant upsert
    # In a real scenario, you'd use a sentence transformer to get vectors
    # For now, we'll just store them in memory
    for doc in documents:
        doc_id = doc.get("id", os.urandom(4).hex())
        KNOWLEDGE_BASE[doc_id] = doc
    
    return {"status": "success", "ingested_count": len(documents), "collection": collection}

@app.get("/agents")
async def list_agents(app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Lists available agents. This is a placeholder."""
    logger.info(f"Received list agents request from app_id: {app_id}")
    return {"agents": [{"id": "contract-reviewer", "name": "Contract Review Agent", "description": "Reviews legal contracts"},
                        {"id": "legal-researcher", "name": "Legal Research Agent", "description": "Performs legal research"}]}

@app.post("/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Executes a specific agent. This is a placeholder."""
    payload = await request.json()
    input_data = payload.get("input")
    context = payload.get("context", {})

    logger.info(f"Received execute agent request from app_id: {app_id} for agent: {agent_id} with input: {input_data}")

    # Simulate agent execution
    if agent_id == "contract-reviewer":
        response_text = f"Agent '{agent_id}' reviewed contract with input: '{input_data}'. Identified no major risks in simulated run."
    else:
        response_text = f"Agent '{agent_id}' executed with input: '{input_data}'. No specific action defined for this agent."
    
    return {"status": "success", "agent_id": agent_id, "response": response_text}

# Web UI endpoint
@app.get("/")
async def web_ui():
    """Serve a chat interface"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Onyx AI Assistant - Chat</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            .header {
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                padding: 1rem;
                text-align: center;
                color: white;
                border-bottom: 1px solid rgba(255,255,255,0.2);
            }
            .header h1 {
                font-size: 1.5rem;
                font-weight: 600;
            }
            .chat-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                max-width: 800px;
                margin: 0 auto;
                width: 100%;
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(10px);
                margin-top: 1rem;
                border-radius: 15px 15px 0 0;
                overflow: hidden;
            }
            .chat-messages {
                flex: 1;
                padding: 1rem;
                overflow-y: auto;
                max-height: calc(100vh - 200px);
            }
            .message {
                margin-bottom: 1rem;
                display: flex;
                align-items: flex-start;
            }
            .message.user {
                justify-content: flex-end;
            }
            .message.assistant {
                justify-content: flex-start;
            }
            .message-content {
                max-width: 70%;
                padding: 0.75rem 1rem;
                border-radius: 18px;
                word-wrap: break-word;
                line-height: 1.4;
            }
            .message.user .message-content {
                background: #007bff;
                color: white;
                border-bottom-right-radius: 5px;
            }
            .message.assistant .message-content {
                background: #f1f3f4;
                color: #333;
                border-bottom-left-radius: 5px;
            }
            .message-avatar {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                margin: 0 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.8rem;
                font-weight: bold;
            }
            .message.user .message-avatar {
                background: #007bff;
                color: white;
                order: 2;
            }
            .message.assistant .message-avatar {
                background: #28a745;
                color: white;
            }
            .input-container {
                padding: 1rem;
                background: white;
                border-top: 1px solid #e9ecef;
                display: flex;
                gap: 0.5rem;
            }
            .message-input {
                flex: 1;
                padding: 0.75rem 1rem;
                border: 2px solid #e9ecef;
                border-radius: 25px;
                outline: none;
                font-size: 1rem;
                transition: border-color 0.2s;
            }
            .message-input:focus {
                border-color: #007bff;
            }
            .send-button {
                padding: 0.75rem 1.5rem;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 1rem;
                font-weight: 600;
                transition: background-color 0.2s;
            }
            .send-button:hover {
                background: #0056b3;
            }
            .send-button:disabled {
                background: #6c757d;
                cursor: not-allowed;
            }
            .typing-indicator {
                display: none;
                padding: 0.75rem 1rem;
                color: #6c757d;
                font-style: italic;
            }
            .typing-indicator.show {
                display: block;
            }
            .welcome-message {
                text-align: center;
                color: #6c757d;
                margin: 2rem 0;
                font-size: 1.1rem;
            }
            .status-indicator {
                display: inline-block;
                width: 8px;
                height: 8px;
                background: #28a745;
                border-radius: 50%;
                margin-right: 0.5rem;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🤖 Onyx AI Assistant</h1>
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                <span class="status-indicator"></span>
                Ready to chat
            </div>
        </div>
        
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="welcome-message">
                    👋 Hello! I'm Onyx, your AI assistant. How can I help you today?
                </div>
            </div>
            
            <div class="typing-indicator" id="typingIndicator">
                Onyx is typing...
            </div>
            
            <div class="input-container">
                <input type="text" class="message-input" id="messageInput" placeholder="Type your message here..." autocomplete="off">
                <button class="send-button" id="sendButton">Send</button>
            </div>
        </div>

        <script>
            const chatMessages = document.getElementById('chatMessages');
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            const typingIndicator = document.getElementById('typingIndicator');

            function addMessage(content, isUser = false) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
                
                const avatar = document.createElement('div');
                avatar.className = 'message-avatar';
                avatar.textContent = isUser ? 'U' : 'O';
                
                const messageContent = document.createElement('div');
                messageContent.className = 'message-content';
                messageContent.textContent = content;
                
                messageDiv.appendChild(avatar);
                messageDiv.appendChild(messageContent);
                
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            function showTyping() {
                typingIndicator.classList.add('show');
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            function hideTyping() {
                typingIndicator.classList.remove('show');
            }

            async function sendMessage() {
                const message = messageInput.value.trim();
                if (!message) return;

                // Add user message
                addMessage(message, true);
                messageInput.value = '';
                sendButton.disabled = true;

                // Show typing indicator
                showTyping();

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            messages: [
                                { role: 'user', content: message }
                            ],
                            model: 'llama3.1:8b',
                            temperature: 0.7,
                            max_tokens: 1024
                        })
                    });

                    const data = await response.json();
                    
                    // Hide typing indicator
                    hideTyping();
                    
                    // Add assistant response
                    const assistantMessage = data.choices?.[0]?.message?.content || 'Sorry, I couldn\'t process your request.';
                    addMessage(assistantMessage, false);

                } catch (error) {
                    hideTyping();
                    addMessage('Sorry, there was an error processing your request. Please try again.', false);
                    console.error('Error:', error);
                } finally {
                    sendButton.disabled = false;
                    messageInput.focus();
                }
            }

            // Event listeners
            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // Focus input on load
            messageInput.focus();
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)