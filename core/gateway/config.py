import os

# ---- Config ----
PORT = int(os.getenv("GATEWAY_PORT", "8081"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "http://vllm:8000/v1")
OPENAI_KEY  = os.getenv("OPENAI_API_KEY", "abs-local")
ONYX_BASE = os.getenv("ONYX_BASE_URL", "http://onyx:8000")
REGISTRY_PATH = os.getenv("REGISTRY_PATH", "registry.json")
APPS_REGISTRY_PATH = os.getenv("APPS_REGISTRY_PATH", os.path.join("..", "abs-ai-hub", "apps-registry.json"))
CATALOG_PATH = os.getenv("CATALOG_PATH", os.path.join("catalog.json"))

# Container name mapping
CONTAINER_MAP = {
    "ollama": "abs-ollama",
    "qdrant": "abs-qdrant", 
    "redis": "abs-redis",
    "hub-gateway": "abs-hub-gateway",
    "onyx": "abs-onyx",
    "postgresql": "document-hub-postgres",
    "whisper-server": "abs-whisper-server"
}

# Auto-wake settings
AUTO_WAKE_SETTINGS = {
    "enabled": True,
    "idle_timeout_minutes": 60,
    "model_keep_alive_hours": 2,
    "idle_sleep_enabled": True,
    "idle_check_interval_minutes": 5
}

# Service dependencies
SERVICE_DEPENDENCIES = {
    "ollama": [],  
    "qdrant": [],  
    "redis": [],   
    "postgresql": [],  
    "hub-gateway": ["redis"],  
    "onyx": ["redis", "qdrant"],
    "whisper": [],
    "minio": [],
    "parser": []
}

# Service startup order
SERVICE_STARTUP_ORDER = ["redis", "postgresql", "qdrant", "ollama", "onyx", "hub-gateway"]

# Supported default models
SUPPORTED_DEFAULT_MODELS = [
    "llama3.2:3b",
    "llama3.2:latest",
    "llama3:8b",
]

# State Registries (Runtime)
MODEL_REGISTRY = {}
