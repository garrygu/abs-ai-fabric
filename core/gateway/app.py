import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Config
from config import PORT, AUTO_WAKE_SETTINGS

# Import Services
from services.autowake import start_idle_monitor, stop_idle_monitor
from services.docker_service import docker_service
from services.asset_manager import get_asset_manager
from adapters.llm_runtime import get_llm_adapter
from adapters.vector_store import get_vector_store_adapter
from adapters.cache_queue import get_cache_queue_adapter

# Import Routers
from routers import chat, assets, ops, store, inspector, attract

# Initialize Logger
logger = logging.getLogger("gateway")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ABS Hub Gateway")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Events
@app.on_event("startup")
async def startup_event():
    # Initialize Asset Manager
    manager = await get_asset_manager()
    print(f"Asset Manager: {len(manager.get_all_assets())} assets loaded")
    
    # Initialize Adapters
    llm = await get_llm_adapter()
    if llm.is_initialized():
        print(f"LLM Adapter ready: {llm.get_asset().asset_id}")
    
    vector = await get_vector_store_adapter()
    if vector.is_initialized():
        print(f"Vector Store Adapter ready: {vector.get_asset().asset_id}")
    
    cache = await get_cache_queue_adapter()
    if cache.is_initialized():
        print(f"Cache Queue Adapter ready")
    
    if AUTO_WAKE_SETTINGS["idle_sleep_enabled"]:
        await start_idle_monitor()
    print("ABS Hub Gateway started")

@app.on_event("shutdown")
async def shutdown_event():
    await stop_idle_monitor()
    print("ABS Hub Gateway shutdown")

# Include Routers
app.include_router(chat.router)
app.include_router(assets.router)
app.include_router(ops.router)
app.include_router(store.router)
app.include_router(inspector.router)
app.include_router(attract.router)

# Health
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
