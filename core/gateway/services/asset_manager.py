"""
Asset Manager Service

Loads asset definitions from the assets/ directory and resolves
interface bindings from bindings.yaml.

This is the core service that enables the "Everything is an Asset" architecture.
Now with Schema v1.0 validation and lifecycle state population.
"""

import os
import json
import yaml
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import Pydantic schema for validation
try:
    from schemas.asset_schema import Asset as AssetSchema, validate_asset_yaml
    SCHEMA_VALIDATION_ENABLED = True
except ImportError:
    SCHEMA_VALIDATION_ENABLED = False
    print("Warning: Pydantic schema not available, validation disabled")

# Paths (relative to container working dir /app)
ASSETS_ROOT = os.getenv("ASSETS_ROOT", "/app/assets")
BINDINGS_PATH = os.getenv("BINDINGS_PATH", "/app/bindings.yaml")
REGISTRY_PATH = os.getenv("ASSETS_REGISTRY_PATH", "/app/assets/registry/assets.json")


# Container status cache (shared across all Asset instances)
# Format: {container_name: (status, timestamp)}
_container_status_cache: Dict[str, tuple] = {}
_CACHE_TTL = 5  # Cache for 5 seconds

# Ollama running models cache (shared across all Asset instances)
# Format: {model_name: (is_running, timestamp)}
_ollama_running_models_cache: Dict[str, tuple] = {}
_OLLAMA_CACHE_TTL = 2  # Cache for 2 seconds (models load/unload frequently)

class Asset:
    """
    Represents a loaded asset definition.
    
    Wraps the raw YAML data and provides typed accessors.
    Optionally validated via Pydantic schema v1.0.
    """
    
    def __init__(self, data: Dict[str, Any], path: str, validated: bool = False):
        self._raw = data
        self._path = path
        self._validated = validated
        
        # Core identity
        self.asset_id = data.get("asset_id", "unknown")
        self.display_name = data.get("display_name", self.asset_id)
        self.interface = data.get("interface", "unknown")
        self.interface_version = data.get("interface_version", "v1")
        self.version = data.get("version", "1.0.0")
        self.asset_class = data.get("class", "unknown")
        self.description = data.get("description", "")
        
        # v1.0: Pack association
        self.pack_id = data.get("pack_id", None)
        
        # v1.0: Ownership & visibility
        self.ownership = data.get("ownership", {})
        
        # Runtime
        self.container = data.get("container", data.get("runtime", {}).get("container", {}))
        self.runtime = data.get("runtime", {})
        
        # Endpoints
        self.endpoints = data.get("endpoints", {})
        
        # Resources (v1.0)
        self.resources = data.get("resources", {})
        
        # Policy
        self.policy = data.get("policy", {})
        
        # Lifecycle (authored intent only - state is Gateway-populated)
        self.lifecycle = data.get("lifecycle", {})
        
        # Legacy fields
        self.capabilities = data.get("capabilities", [])
        self.metadata = data.get("metadata", {})
        self.adapter_required = data.get("adapter_required", False)
        self.adapter_module = data.get("adapter_module", None)
    
    def get_endpoint(self, name: str) -> Optional[str]:
        """Get a named endpoint URL."""
        return self.endpoints.get(name)
    
    def get_container_name(self) -> Optional[str]:
        """Get the Docker container name."""
        return self.container.get("name")
    
    def get_resource(self, key: str) -> Optional[Any]:
        """Get a resource requirement value."""
        return self.resources.get(key)
    
    def is_gpu_required(self) -> bool:
        """Check if GPU is required."""
        return self.resources.get("gpu_required", False)
    
    def _get_container_status(self, container_name: str) -> str:
        """Get real Docker container status with caching."""
        global _container_status_cache
        
        # Check cache first
        now = time.time()
        if container_name in _container_status_cache:
            cached_status, cached_time = _container_status_cache[container_name]
            if now - cached_time < _CACHE_TTL:
                return cached_status
        
        # Cache miss or expired - check Docker
        try:
            import subprocess
            # Reduced timeout from 5s to 1s for faster response
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Status}}", container_name],
                capture_output=True,
                text=True,
                timeout=1  # Reduced from 5 to 1 second
            )
            if result.returncode == 0:
                status = result.stdout.strip()
                # Map Docker status to our lifecycle states
                if status == "running":
                    mapped_status = "running"
                elif status == "exited" or status == "stopped":
                    mapped_status = "stopped"
                elif status == "paused":
                    mapped_status = "suspended"
                elif status == "restarting":
                    mapped_status = "warming"
                else:
                    mapped_status = "unknown"
                
                # Cache the result
                _container_status_cache[container_name] = (mapped_status, now)
                return mapped_status
            else:
                # Container not found - cache as unknown
                _container_status_cache[container_name] = ("unknown", now)
                return "unknown"
        except subprocess.TimeoutExpired:
            # Timeout - return cached value if available, otherwise unknown
            if container_name in _container_status_cache:
                return _container_status_cache[container_name][0]
            return "unknown"
        except Exception:
            # Any other error - return unknown
            if container_name in _container_status_cache:
                return _container_status_cache[container_name][0]
            return "unknown"
    
    def _check_ollama_model_running(self) -> bool:
        """Check if this model is currently running in Ollama."""
        global _ollama_running_models_cache
        
        # Get model name from asset_id or display_name
        # Model names in Ollama might be in format "model:tag" or just "model"
        model_name = self.asset_id
        if not model_name or model_name == "unknown":
            model_name = self.display_name
        
        # Check cache first
        now = time.time()
        if model_name in _ollama_running_models_cache:
            cached_running, cached_time = _ollama_running_models_cache[model_name]
            if now - cached_time < _OLLAMA_CACHE_TTL:
                return cached_running
        
        # Cache miss or expired - check Ollama
        try:
            import httpx
            from config import OLLAMA_BASE
            
            # Query Ollama's /api/ps endpoint to get running models
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{OLLAMA_BASE.rstrip('/')}/api/ps")
                if response.status_code == 200:
                    data = response.json()
                    running_models = data.get("models", [])
                    
                    # Check if our model is in the running list
                    # Ollama returns models as {"name": "model:tag", ...}
                    running_model_names = set()
                    for m in running_models:
                        name = m.get("name", "")
                        if name:
                            running_model_names.add(name)
                            # Also check without tag (e.g., "model:70b" -> "model")
                            if ":" in name:
                                running_model_names.add(name.split(":")[0])
                    
                    # Check if our model matches any running model
                    is_running = False
                    
                    # First, try exact match
                    if model_name in running_model_names:
                        is_running = True
                    else:
                        # Try normalized matching (handle variations in format)
                        # Normalize both asset_id and Ollama names for comparison
                        model_normalized = model_name.lower().replace("_", "-").replace(":", "-")
                        
                        for running_name in running_model_names:
                            running_normalized = running_name.lower().replace("_", "-").replace(":", "-")
                            
                            # Exact normalized match
                            if model_normalized == running_normalized:
                                is_running = True
                                break
                            
                            # Partial match (e.g., "deepseek-r1-70b" matches "deepseek-r1:70b")
                            if model_normalized in running_normalized or running_normalized in model_normalized:
                                is_running = True
                                break
                            
                            # Also check if base names match (without tag)
                            # e.g., "deepseek-r1:70b" and "deepseek-r1" should match
                            if ":" in model_name and ":" in running_name:
                                model_base = model_name.split(":")[0].lower().replace("_", "-")
                                running_base = running_name.split(":")[0].lower().replace("_", "-")
                                if model_base == running_base:
                                    is_running = True
                                    break
                    
                    # Cache the result
                    _ollama_running_models_cache[model_name] = (is_running, now)
                    
                    # Debug logging for model status matching
                    print(f"[AssetManager] Model '{model_name}' check: is_running={is_running}, ollama_models={[m.get('name') for m in running_models]}")
                    
                    return is_running
                else:
                    # Ollama API error - cache as not running
                    _ollama_running_models_cache[model_name] = (False, now)
                    return False
        except Exception as e:
            # Any error - return cached value if available, otherwise False
            if model_name in _ollama_running_models_cache:
                return _ollama_running_models_cache[model_name][0]
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary for API response.
        
        Note: lifecycle.state and metadata._status are Gateway-populated
        based on v1.0 governance rules.
        """
        # Derive lifecycle.state based on v1.0 state machine
        # Check real container status if this is a containerized asset
        lifecycle_with_state = self.lifecycle.copy()
        
        container_name = self.get_container_name()
        if container_name:
            # Check real Docker status
            observed_state = self._get_container_status(container_name)
            lifecycle_with_state["state"] = observed_state
        elif self.asset_class == "model" or self.interface in ["llm-runtime", "embedding-runtime", "image-runtime"]:
            # For models, check Ollama running state
            is_running = self._check_ollama_model_running()
            if is_running:
                lifecycle_with_state["state"] = "running"
            elif "state" not in lifecycle_with_state:
                # Default to idle if not running
                lifecycle_with_state["state"] = "idle"
        elif "state" not in lifecycle_with_state:
            # Non-containerized: derive from desired
            desired = lifecycle_with_state.get("desired", "on-demand")
            if desired == "running":
                lifecycle_with_state["state"] = "running"
            elif desired == "suspended":
                lifecycle_with_state["state"] = "suspended"
            else:  # on-demand
                lifecycle_with_state["state"] = "idle"  # Default to idle for on-demand
        
        return {
            # Identity
            "id": self.asset_id,  # Alias for UI compatibility
            "asset_id": self.asset_id,
            "display_name": self.display_name,
            "name": self.display_name,  # Alias for UI compatibility
            "version": self.version,
            
            # Contract
            "interface": self.interface,
            "interface_version": self.interface_version,
            "class": self.asset_class,
            "description": self.description,
            
            # Pack
            "pack_id": self.pack_id,
            
            # Ownership (v1.0)
            "ownership": self.ownership,
            
            # Runtime & Endpoints
            "runtime": self.runtime,
            "endpoints": self.endpoints,
            
            # Resources
            "resources": self.resources,
            
            # Policy
            "policy": self.policy,
            
            # Lifecycle with Gateway-populated state
            "lifecycle": lifecycle_with_state,
            
            # Metadata (UI reads from here)
            "metadata": self.metadata,
            
            # For backward compat with old UI
            "status": lifecycle_with_state.get("state", "ready"),
            
            # Validation status
            "_validated": self._validated
        }


class AssetManager:
    """
    Central manager for loading and resolving assets.
    
    Usage:
        manager = AssetManager()
        await manager.initialize()
        
        llm = manager.get_bound_asset("llm-runtime")
        endpoint = llm.get_endpoint("chat")
    """
    
    def __init__(self):
        self._assets: Dict[str, Asset] = {}
        self._bindings: Dict[str, str] = {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Load all assets and bindings."""
        try:
            self._load_bindings()
            self._load_assets()
            self._initialized = True
            print(f"AssetManager initialized: {len(self._assets)} assets, {len(self._bindings)} bindings")
            return True
        except Exception as e:
            print(f"AssetManager initialization failed: {e}")
            return False
    
    def _load_bindings(self):
        """Load bindings.yaml configuration."""
        try:
            # Try multiple paths for flexibility
            paths_to_try = [
                BINDINGS_PATH,
                os.path.join(os.getcwd(), "..", "bindings.yaml"),
                "/app/bindings.yaml",
                "C:/ABS/core/bindings.yaml"  # Dev fallback
            ]
            
            for path in paths_to_try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        self._bindings = data.get("core_bindings", {})
                        print(f"Loaded bindings from {path}")
                        return
            
            print("No bindings.yaml found, using defaults")
            self._bindings = {
                "llm-runtime": "ollama",
                "vector-store": "qdrant",
                "cache-queue": "redis"
            }
        except Exception as e:
            print(f"Error loading bindings: {e}")
            self._bindings = {}
    
    def _load_assets(self):
        """Load all asset definitions from the assets directory."""
        try:
            # Try to load from registry index first
            registry_paths = [
                REGISTRY_PATH,
                os.path.join(os.getcwd(), "..", "..", "..", "assets", "registry", "assets.json"),
                "C:/ABS/assets/registry/assets.json"  # Dev fallback
            ]
            
            for reg_path in registry_paths:
                if os.path.exists(reg_path):
                    with open(reg_path, "r", encoding="utf-8") as f:
                        registry = json.load(f)
                        assets_base = os.path.dirname(os.path.dirname(reg_path))
                        
                        # Load all registry sections
                        sections = [
                            "core_assets",
                            "apps", 
                            "models",
                            "tools",
                            "datasets",
                            "extended_assets"  # Legacy compatibility
                        ]
                        
                        for section in sections:
                            for asset_ref in registry.get(section, []):
                                asset_path = os.path.join(assets_base, asset_ref["path"])
                                self._load_asset_file(asset_path)
                        
                        print(f"Loaded assets from registry: {reg_path}")
                        return
            
            # Fallback: scan directory structure
            self._scan_assets_directory()
            
        except Exception as e:
            print(f"Error loading assets: {e}")
    
    def _load_asset_file(self, path: str):
        """Load a single asset.yaml file with optional validation."""
        try:
            if not os.path.exists(path):
                print(f"Asset file not found: {path}")
                return
            
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            # Validate with Pydantic if available
            validated = False
            if SCHEMA_VALIDATION_ENABLED:
                try:
                    validate_asset_yaml(data)
                    validated = True
                except Exception as ve:
                    print(f"Schema validation warning for {path}: {ve}")
            
            asset = Asset(data, path, validated=validated)
            self._assets[asset.asset_id] = asset
            status = "✓" if validated else "⚠"
            print(f"Loaded asset: {asset.asset_id} ({asset.interface}) [{status}]")
        except Exception as e:
            print(f"Error loading asset {path}: {e}")
    
    def _scan_assets_directory(self):
        """Fallback method to scan for asset.yaml files."""
        roots_to_try = [
            ASSETS_ROOT,
            "C:/ABS/assets"
        ]
        
        for root in roots_to_try:
            if os.path.isdir(root):
                for dirpath, _, filenames in os.walk(root):
                    if "asset.yaml" in filenames:
                        self._load_asset_file(os.path.join(dirpath, "asset.yaml"))
                return
    
    # --- Public API ---
    
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Get an asset by its ID."""
        return self._assets.get(asset_id)
    
    def get_bound_asset(self, interface: str) -> Optional[Asset]:
        """Get the asset bound to an interface."""
        asset_id = self._bindings.get(interface)
        if not asset_id:
            print(f"No binding found for interface: {interface}")
            return None
        return self.get_asset(asset_id)
    
    def get_all_assets(self) -> List[Asset]:
        """Get all loaded assets."""
        return list(self._assets.values())
    
    def get_assets_by_interface(self, interface: str) -> List[Asset]:
        """Get all assets implementing an interface."""
        return [a for a in self._assets.values() if a.interface == interface]
    
    def get_bindings(self) -> Dict[str, str]:
        """Get current interface bindings."""
        return self._bindings.copy()
    
    def get_llm_models(self) -> List[Asset]:
        """Get all LLM models (llm-runtime interface)."""
        return self.get_assets_by_interface("llm-runtime")
    
    def get_embedding_models(self) -> List[Asset]:
        """Get all embedding models (embedding-runtime interface)."""
        return self.get_assets_by_interface("embedding-runtime")
    
    # ============================================================
    # Asset Lifecycle Control (v1.0.1)
    # ============================================================
    
    async def start_asset(self, asset_id: str) -> Dict[str, Any]:
        """
        Start an asset. For containerized assets, starts the Docker container.
        
        Returns:
            dict with status, message, and new state
        """
        asset = self.get_asset(asset_id)
        if not asset:
            return {"success": False, "error": f"Asset not found: {asset_id}"}
        
        container_name = asset.get_container_name()
        if not container_name:
            return {"success": False, "error": f"Asset has no container: {asset_id}"}
        
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "start", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"Started container: {container_name}")
                return {
                    "success": True,
                    "message": f"Started {asset.display_name}",
                    "state": "running"
                }
            else:
                return {
                    "success": False,
                    "error": f"Docker start failed: {result.stderr}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def stop_asset(self, asset_id: str) -> Dict[str, Any]:
        """
        Stop an asset. For containerized assets, stops the Docker container.
        
        Returns:
            dict with status, message, and new state
        """
        asset = self.get_asset(asset_id)
        if not asset:
            return {"success": False, "error": f"Asset not found: {asset_id}"}
        
        container_name = asset.get_container_name()
        if not container_name:
            return {"success": False, "error": f"Asset has no container: {asset_id}"}
        
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                text=True,
                timeout=60  # Longer timeout for graceful stop
            )
            
            if result.returncode == 0:
                print(f"Stopped container: {container_name}")
                return {
                    "success": True,
                    "message": f"Stopped {asset.display_name}",
                    "state": "stopped"
                }
            else:
                return {
                    "success": False,
                    "error": f"Docker stop failed: {result.stderr}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def restart_asset(self, asset_id: str) -> Dict[str, Any]:
        """
        Restart an asset. For containerized assets, restarts the Docker container.
        
        Returns:
            dict with status, message, and new state
        """
        asset = self.get_asset(asset_id)
        if not asset:
            return {"success": False, "error": f"Asset not found: {asset_id}"}
        
        container_name = asset.get_container_name()
        if not container_name:
            return {"success": False, "error": f"Asset has no container: {asset_id}"}
        
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "restart", container_name],
                capture_output=True,
                text=True,
                timeout=90
            )
            
            if result.returncode == 0:
                print(f"Restarted container: {container_name}")
                return {
                    "success": True,
                    "message": f"Restarted {asset.display_name}",
                    "state": "running"
                }
            else:
                return {
                    "success": False,
                    "error": f"Docker restart failed: {result.stderr}"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_asset_status(self, asset_id: str) -> Dict[str, Any]:
        """
        Get real-time status of an asset by checking its container.
        
        Returns:
            dict with container_status, running, health
        """
        asset = self.get_asset(asset_id)
        if not asset:
            return {"status": "unknown", "error": f"Asset not found: {asset_id}"}
        
        container_name = asset.get_container_name()
        if not container_name:
            # Non-containerized asset
            return {"status": "n/a", "type": "non-container"}
        
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Status}}", container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                status = result.stdout.strip()
                return {
                    "status": status,
                    "running": status == "running",
                    "container": container_name
                }
            else:
                return {"status": "not_found", "running": False}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._initialized


# Singleton instance
_manager: Optional[AssetManager] = None


async def get_asset_manager() -> AssetManager:
    """Get or create the singleton AssetManager instance."""
    global _manager
    if _manager is None:
        _manager = AssetManager()
        await _manager.initialize()
    return _manager


def get_asset_manager_sync() -> Optional[AssetManager]:
    """Get the manager if already initialized (sync access)."""
    return _manager
