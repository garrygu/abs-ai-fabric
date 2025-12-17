"""
Asset Manager Service

Loads asset definitions from the assets/ directory and resolves
interface bindings from bindings.yaml.

This is the core service that enables the "Everything is an Asset" architecture.
Now with Schema v1.2 validation.
"""

import os
import json
import yaml
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


class Asset:
    """
    Represents a loaded asset definition.
    
    Wraps the raw YAML data and provides typed accessors.
    Optionally validated via Pydantic schema v1.2.
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
        
        # v1.2: Pack association
        self.pack_id = data.get("pack_id", None)
        
        # Runtime
        self.container = data.get("container", data.get("runtime", {}).get("container", {}))
        self.runtime = data.get("runtime", {})
        
        # Endpoints
        self.endpoints = data.get("endpoints", {})
        
        # Resources (v1.2)
        self.resources = data.get("resources", {})
        
        # Policy
        self.policy = data.get("policy", {})
        
        # Lifecycle
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "asset_id": self.asset_id,
            "display_name": self.display_name,
            "interface": self.interface,
            "interface_version": self.interface_version,
            "version": self.version,
            "class": self.asset_class,
            "pack_id": self.pack_id,
            "endpoints": self.endpoints,
            "resources": self.resources,
            "lifecycle": self.lifecycle,
            "metadata": self.metadata,
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
                        
                        for asset_ref in registry.get("core_assets", []):
                            asset_path = os.path.join(assets_base, asset_ref["path"])
                            self._load_asset_file(asset_path)
                        
                        for asset_ref in registry.get("extended_assets", []):
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
