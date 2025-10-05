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

# Settings storage (in production, this would be in a database)
USER_SETTINGS = {
    "default_model": "llama3.2:latest",
    "temperature": 0.7,
    "max_tokens": 1024,
    "system_prompt": "You are Onyx, a helpful AI assistant. Be concise and helpful in your responses.",
    "enable_rag": True,
    "enable_web_search": False,
    "theme": "light"
}

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatReq(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "llama3.2:latest"
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
        response = await HTTP_CLIENT.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=httpx.Timeout(30.0, connect=10.0)
        )
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
        logger.error(f"LLM service HTTP error: status={e.response.status_code} body={e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except httpx.RequestError as e:
        logger.exception(f"LLM service request error: {e}")
        raise HTTPException(status_code=502, detail=f"Upstream LLM request error: {str(e)}")
    except Exception as e:
        logger.exception("Unexpected error forwarding chat request")
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
            model="llama3.2:latest"
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

# Settings endpoints
@app.get("/settings")
async def get_settings():
    """Get current user settings"""
    return USER_SETTINGS

@app.post("/settings")
async def update_settings(request: Request):
    """Update user settings"""
    try:
        new_settings = await request.json()
        
        # Validate and update settings
        for key, value in new_settings.items():
            if key in USER_SETTINGS:
                USER_SETTINGS[key] = value
        
        logger.info(f"Settings updated: {new_settings}")
        return {"status": "success", "settings": USER_SETTINGS}
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")

@app.get("/models")
async def get_available_models():
    """Get list of available models from Ollama"""
    try:
        response = await HTTP_CLIENT.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags")
        if response.is_success:
            models_data = response.json()
            models = [model["name"] for model in models_data.get("models", [])]
            return {"models": models}
        else:
            return {"models": ["llama3.2:latest"]}
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return {"models": ["llama3.2:latest"]}

# Web UI endpoint
@app.get("/", response_class=HTMLResponse)
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
            .settings-button {
                position: absolute;
                top: 1rem;
                right: 1rem;
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: all 0.2s;
            }
            .settings-button:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-1px);
            }
            .settings-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
                backdrop-filter: blur(5px);
            }
            .settings-modal.show {
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .settings-content {
                background: white;
                border-radius: 15px;
                padding: 2rem;
                max-width: 500px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            .settings-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1.5rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #e9ecef;
            }
            .settings-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: #333;
                margin: 0;
            }
            .close-button {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: #6c757d;
                padding: 0.25rem;
                border-radius: 50%;
                width: 2rem;
                height: 2rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .close-button:hover {
                background: #f8f9fa;
                color: #333;
            }
            .settings-group {
                margin-bottom: 1.5rem;
            }
            .settings-label {
                display: block;
                font-weight: 600;
                color: #333;
                margin-bottom: 0.5rem;
            }
            .settings-input {
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 1rem;
                transition: border-color 0.2s;
            }
            .settings-input:focus {
                outline: none;
                border-color: #007bff;
            }
            .settings-select {
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 1rem;
                background: white;
                cursor: pointer;
            }
            .settings-range {
                width: 100%;
                margin: 0.5rem 0;
            }
            .settings-checkbox {
                margin-right: 0.5rem;
            }
            .settings-textarea {
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                font-size: 1rem;
                resize: vertical;
                min-height: 100px;
                font-family: inherit;
            }
            .settings-buttons {
                display: flex;
                gap: 1rem;
                justify-content: flex-end;
                margin-top: 2rem;
                padding-top: 1rem;
                border-top: 1px solid #e9ecef;
            }
            .btn {
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            .btn-primary {
                background: #007bff;
                color: white;
            }
            .btn-primary:hover {
                background: #0056b3;
            }
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            .btn-secondary:hover {
                background: #545b62;
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
            <button class="settings-button" id="settingsButton">⚙️ Settings</button>
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

        <!-- Settings Modal -->
        <div class="settings-modal" id="settingsModal">
            <div class="settings-content">
                <div class="settings-header">
                    <h2 class="settings-title">⚙️ Settings</h2>
                    <button class="close-button" id="closeSettings">×</button>
                </div>
                
                <div class="settings-group">
                    <label class="settings-label" for="modelSelect">AI Model</label>
                    <select class="settings-select" id="modelSelect">
                        <option value="llama3.2:latest">Llama 3.2 Latest</option>
                    </select>
                </div>

                <div class="settings-group">
                    <label class="settings-label" for="temperatureRange">Temperature: <span id="temperatureValue">0.7</span></label>
                    <input type="range" class="settings-range" id="temperatureRange" min="0" max="2" step="0.1" value="0.7">
                </div>

                <div class="settings-group">
                    <label class="settings-label" for="maxTokensInput">Max Tokens</label>
                    <input type="number" class="settings-input" id="maxTokensInput" min="100" max="4096" value="1024">
                </div>

                <div class="settings-group">
                    <label class="settings-label" for="systemPromptTextarea">System Prompt</label>
                    <textarea class="settings-textarea" id="systemPromptTextarea" placeholder="Enter system prompt...">You are Onyx, a helpful AI assistant. Be concise and helpful in your responses.</textarea>
                </div>

                <div class="settings-group">
                    <label class="settings-label">
                        <input type="checkbox" class="settings-checkbox" id="enableRag" checked>
                        Enable RAG (Retrieval-Augmented Generation)
                    </label>
                </div>

                <div class="settings-group">
                    <label class="settings-label">
                        <input type="checkbox" class="settings-checkbox" id="enableWebSearch">
                        Enable Web Search
                    </label>
                </div>

                <div class="settings-group">
                    <label class="settings-label" for="themeSelect">Theme</label>
                    <select class="settings-select" id="themeSelect">
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                        <option value="auto">Auto</option>
                    </select>
                </div>

                <div class="settings-buttons">
                    <button class="btn btn-secondary" id="cancelSettings">Cancel</button>
                    <button class="btn btn-primary" id="saveSettings">Save Settings</button>
                </div>
            </div>
        </div>

        <script>
            const chatMessages = document.getElementById('chatMessages');
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            const typingIndicator = document.getElementById('typingIndicator');
            
            // Settings elements
            const settingsButton = document.getElementById('settingsButton');
            const settingsModal = document.getElementById('settingsModal');
            const closeSettings = document.getElementById('closeSettings');
            const cancelSettings = document.getElementById('cancelSettings');
            const saveSettings = document.getElementById('saveSettings');
            const temperatureRange = document.getElementById('temperatureRange');
            const temperatureValue = document.getElementById('temperatureValue');
            
            // Current settings
            let currentSettings = {
                default_model: 'llama3.2:latest',
                temperature: 0.7,
                max_tokens: 1024,
                system_prompt: 'You are Onyx, a helpful AI assistant. Be concise and helpful in your responses.',
                enable_rag: true,
                enable_web_search: false,
                theme: 'light'
            };

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
                                { role: 'system', content: currentSettings.system_prompt },
                                { role: 'user', content: message }
                            ],
                            model: currentSettings.default_model,
                            temperature: currentSettings.temperature,
                            max_tokens: currentSettings.max_tokens
                        })
                    });

                    const data = await response.json();
                    
                    // Hide typing indicator
                    hideTyping();
                    
                    // Add assistant response
                    const assistantMessage = data.choices?.[0]?.message?.content || 'Sorry, I could not process your request.';
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
            
            // Settings functionality
            async function loadSettings() {
                try {
                    const response = await fetch('/settings');
                    const settings = await response.json();
                    currentSettings = settings;
                    await loadAvailableModels();
                    populateSettingsForm();
                } catch (error) {
                    console.error('Error loading settings:', error);
                }
            }
            
            async function loadAvailableModels() {
                try {
                    const response = await fetch('/models');
                    const data = await response.json();
                    const modelSelect = document.getElementById('modelSelect');
                    
                    // Clear existing options
                    modelSelect.innerHTML = '';
                    
                    // Add available models
                    data.models.forEach(model => {
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        modelSelect.appendChild(option);
                    });
                } catch (error) {
                    console.error('Error loading models:', error);
                }
            }
            
            function populateSettingsForm() {
                document.getElementById('modelSelect').value = currentSettings.default_model;
                document.getElementById('temperatureRange').value = currentSettings.temperature;
                document.getElementById('temperatureValue').textContent = currentSettings.temperature;
                document.getElementById('maxTokensInput').value = currentSettings.max_tokens;
                document.getElementById('systemPromptTextarea').value = currentSettings.system_prompt;
                document.getElementById('enableRag').checked = currentSettings.enable_rag;
                document.getElementById('enableWebSearch').checked = currentSettings.enable_web_search;
                document.getElementById('themeSelect').value = currentSettings.theme;
            }
            
            async function saveSettingsToServer() {
                try {
                    const settingsToSave = {
                        default_model: document.getElementById('modelSelect').value,
                        temperature: parseFloat(document.getElementById('temperatureRange').value),
                        max_tokens: parseInt(document.getElementById('maxTokensInput').value),
                        system_prompt: document.getElementById('systemPromptTextarea').value,
                        enable_rag: document.getElementById('enableRag').checked,
                        enable_web_search: document.getElementById('enableWebSearch').checked,
                        theme: document.getElementById('themeSelect').value
                    };
                    
                    const response = await fetch('/settings', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(settingsToSave)
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        currentSettings = result.settings;
                        console.log('Settings saved successfully');
                        return true;
                    } else {
                        console.error('Failed to save settings');
                        return false;
                    }
                } catch (error) {
                    console.error('Error saving settings:', error);
                    return false;
                }
            }
            
            // Settings event listeners
            settingsButton.addEventListener('click', () => {
                settingsModal.classList.add('show');
                populateSettingsForm();
            });
            
            closeSettings.addEventListener('click', () => {
                settingsModal.classList.remove('show');
            });
            
            cancelSettings.addEventListener('click', () => {
                settingsModal.classList.remove('show');
            });
            
            saveSettings.addEventListener('click', async () => {
                const saved = await saveSettingsToServer();
                if (saved) {
                    settingsModal.classList.remove('show');
                    // Show success message
                    addMessage('Settings saved successfully!', false);
                } else {
                    alert('Failed to save settings. Please try again.');
                }
            });
            
            temperatureRange.addEventListener('input', () => {
                temperatureValue.textContent = temperatureRange.value;
            });
            
            // Close modal when clicking outside
            settingsModal.addEventListener('click', (e) => {
                if (e.target === settingsModal) {
                    settingsModal.classList.remove('show');
                }
            });
            
            // Load settings on page load
            console.log('Starting Onyx AI Assistant...');
            console.log('Settings button:', settingsButton);
            console.log('Send button:', sendButton);
            loadSettings();
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)