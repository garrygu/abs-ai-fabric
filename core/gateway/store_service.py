"""
App Store Service
Handles store aggregation, app discovery, and installation
"""
import os
import json
import subprocess
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class StoreService:
    def __init__(self, base_path: str = None):
        # In Docker container, files are mounted at /app
        # Try container paths first, then fallback to relative paths
        if os.path.exists("/app/store-sources.json"):
            # Running in Docker container
            self.base_path = "/app"
            self.store_sources_path = "/app/store-sources.json"
            self.apps_dir = "/app/apps"
            # Use a writable location for cache (inside /app, not in mounted volume)
            self.store_cache_dir = "/tmp/store_cache"  # Use /tmp which is writable
        else:
            # Running locally
            self.base_path = base_path or os.path.join(os.path.dirname(__file__), "..", "..")
            self.store_sources_path = os.path.join(self.base_path, "abs-ai-hub", "store-sources.json")
            self.apps_dir = os.path.join(self.base_path, "abs-ai-hub", "apps")
            self.store_cache_dir = os.path.join(self.base_path, "abs-ai-hub", "store", "cache")
        
        # Ensure directories exist (skip if read-only filesystem)
        # Don't fail initialization if cache directory can't be created
        try:
            os.makedirs(self.store_cache_dir, exist_ok=True)
        except Exception as e:
            # Silently continue if cache directory cannot be created (read-only filesystem is OK)
            # Cache is optional, store service can work without it
            logger.debug(f"Could not create cache directory {self.store_cache_dir}: {e}, continuing without cache")
        
        # Load store sources config
        try:
            self.sources_config = self._load_sources_config()
            logger.info(f"Store Service initialized. Sources config loaded: {len(self.sources_config.get('sources', []))} sources")
        except Exception as e:
            logger.error(f"Failed to load store sources config: {e}")
            self.sources_config = {"sources": [], "version": "1.0.0"}
    
    def _load_sources_config(self) -> Dict[str, Any]:
        """Load store sources configuration"""
        try:
            if os.path.exists(self.store_sources_path):
                with open(self.store_sources_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load store sources config: {e}")
        return {"sources": [], "version": "1.0.0"}
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Load catalog.json to check installed apps"""
        catalog_path = os.path.join(os.path.dirname(__file__), "catalog.json")
        try:
            if os.path.exists(catalog_path):
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load catalog: {e}")
        return {"assets": []}
    
    def _load_apps_registry(self) -> Dict[str, Any]:
        """Load apps-registry.json to check installed apps"""
        # Try container path first, then relative path
        if os.path.exists("/app/apps-registry.json"):
            registry_path = "/app/apps-registry.json"
        else:
            registry_path = os.path.join(self.base_path, "abs-ai-hub", "apps-registry.json")
        try:
            if os.path.exists(registry_path):
                with open(registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load apps registry: {e}")
        return {"applications": []}
    
    def _scan_local_apps(self) -> List[Dict[str, Any]]:
        """Scan local apps directory for apps with manifests"""
        apps = []
        if not os.path.exists(self.apps_dir):
            return apps
        
        for item in os.listdir(self.apps_dir):
            app_path = os.path.join(self.apps_dir, item)
            if not os.path.isdir(app_path):
                continue
            
            manifest_path = os.path.join(app_path, "app.manifest.json")
            if not os.path.exists(manifest_path):
                continue
            
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                app_data = {
                    "id": manifest.get("id", item),
                    "name": manifest.get("name", item),
                    "version": manifest.get("version", "1.0.0"),
                    "description": manifest.get("description", ""),
                    "category": manifest.get("category", "General"),
                    "author": manifest.get("author", "Unknown"),
                    "license": manifest.get("license", "Unknown"),
                    "keywords": manifest.get("keywords", []),
                    "source": {
                        "type": "self-developed",
                        "location": f"file://{app_path}",
                        "path": app_path
                    },
                    "icon": manifest.get("configuration", {}).get("icon", "fas fa-cube"),
                    "requirements": {
                        "services": manifest.get("configuration", {}).get("gateway_integration", {}).get("services", []),
                        "resources": {}
                    },
                    "metadata": {
                        "installed": False,
                        "installable": True
                    }
                }
                apps.append(app_data)
            except Exception as e:
                logger.warning(f"Failed to load manifest for {item}: {e}")
                continue
        
        return apps
    
    def _load_official_store(self) -> List[Dict[str, Any]]:
        """Load apps from official store (local cache or remote)"""
        apps = []
        sources = self.sources_config.get("sources", [])
        
        for source in sources:
            if source.get("type") != "official" or not source.get("enabled"):
                continue
            
            local_path = source.get("local_path")
            if local_path:
                # In container, map abs-ai-hub/store/ to /app/store/
                if local_path.startswith("abs-ai-hub/store/"):
                    # Replace with container path
                    container_path = local_path.replace("abs-ai-hub/store/", "/app/store/")
                    if os.path.exists(container_path):
                        local_path = container_path
                        logger.info(f"Using container path: {local_path}")
                    else:
                        # Fallback: try direct /app/store/ path
                        direct_path = local_path.replace("abs-ai-hub/store/", "/app/store/")
                        if os.path.exists(direct_path):
                            local_path = direct_path
                            logger.info(f"Using direct container path: {local_path}")
                        else:
                            # Fallback to relative path (if running locally)
                            local_path = os.path.join(self.base_path, local_path)
                            logger.info(f"Using relative path: {local_path}")
                elif not os.path.isabs(local_path):
                    # Resolve relative paths
                    local_path = os.path.join(self.base_path, local_path)
                
                logger.info(f"Checking store file at: {local_path}")
                if os.path.exists(local_path):
                    try:
                        with open(local_path, 'r', encoding='utf-8') as f:
                            store_data = json.load(f)
                            store_apps = store_data.get("apps", [])
                            logger.info(f"Loaded {len(store_apps)} apps from {local_path}")
                            apps.extend(store_apps)
                    except Exception as e:
                        logger.error(f"Failed to load official store from {local_path}: {e}")
                        logger.error(f"Error details: {str(e)}")
                else:
                    logger.warning(f"Store file not found at: {local_path}")
        
        return apps
    
    def aggregate_store_apps(self) -> List[Dict[str, Any]]:
        """Aggregate apps from all enabled sources"""
        all_apps = []
        
        # Load installed apps for status checking
        catalog = self._load_catalog()
        apps_registry = self._load_apps_registry()
        installed_app_ids = set()
        
        # Get installed app IDs from catalog
        for asset in catalog.get("assets", []):
            if asset.get("class") == "app":
                installed_app_ids.add(asset.get("id"))
        
        # Get installed app IDs from apps registry
        for app in apps_registry.get("applications", []):
            installed_app_ids.add(app.get("id"))
        
        # Load from official store
        official_apps = self._load_official_store()
        for app in official_apps:
            app["metadata"] = app.get("metadata", {})
            app["metadata"]["installed"] = app.get("id") in installed_app_ids
            app["metadata"]["source_type"] = "abs-official"
            all_apps.append(app)
        
        # Scan local apps directory
        local_apps = self._scan_local_apps()
        for app in local_apps:
            app["metadata"]["installed"] = app.get("id") in installed_app_ids
            app["metadata"]["source_type"] = "self-developed"
            all_apps.append(app)
        
        return all_apps
    
    def get_app_details(self, app_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific app"""
        apps = self.aggregate_store_apps()
        for app in apps:
            if app.get("id") == app_id:
                return app
        return None
    
    def install_app(self, app_id: str, install_dependencies: bool = False) -> Dict[str, Any]:
        """Install an app from the store"""
        app = self.get_app_details(app_id)
        if not app:
            raise ValueError(f"App {app_id} not found in store")
        
        if app.get("metadata", {}).get("installed"):
            raise ValueError(f"App {app_id} is already installed")
        
        source = app.get("source", {})
        source_type = source.get("type")
        source_path = source.get("path") or source.get("location", "").replace("file://", "")
        
        # Resolve source path - handle relative paths
        if source_path.startswith("file://"):
            source_path = source_path.replace("file://", "")
        
        # Handle relative paths from base_path
        if not os.path.isabs(source_path):
            # Check if it's relative to apps directory
            if source_path.startswith("abs-ai-hub/apps/"):
                source_path = os.path.join(self.base_path, source_path)
            elif source_path.startswith("apps/"):
                source_path = os.path.join(self.base_path, "abs-ai-hub", source_path)
            else:
                source_path = os.path.join(self.apps_dir, source_path)
        
        # Normalize path
        source_path = os.path.normpath(source_path)
        
        # Determine target directory
        target_dir = os.path.join(self.apps_dir, app_id)
        
        # Check if app is already physically present (from official store)
        app_already_exists = os.path.exists(target_dir)
        
        try:
            # If app doesn't exist, copy it
            if not app_already_exists:
                if not os.path.exists(source_path):
                    raise ValueError(f"Source path {source_path} does not exist")
                
                # Copy app files
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, target_dir, dirs_exist_ok=False)
                else:
                    raise ValueError(f"Source path {source_path} is not a directory")
            else:
                logger.info(f"App {app_id} already exists at {target_dir}, skipping file copy")
            
            # Validate app has manifest
            manifest_path = os.path.join(target_dir, "app.manifest.json")
            if not os.path.exists(manifest_path):
                # Try to create a basic manifest
                self._create_basic_manifest(manifest_path, app)
            else:
                # Load manifest to get actual app details
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                        # Update app data from manifest if available
                        app["version"] = manifest.get("version", app.get("version", "1.0.0"))
                        app["description"] = manifest.get("description", app.get("description", ""))
                        app["category"] = manifest.get("category", app.get("category", "General"))
                except Exception as e:
                    logger.warning(f"Failed to load manifest: {e}")
            
            # Register in apps-registry.json
            self._register_app_in_registry(app, target_dir)
            
            # Add to catalog.json as asset
            self._add_app_to_catalog(app, target_dir)
            
            return {
                "status": "success",
                "app_id": app_id,
                "path": target_dir,
                "message": f"App {app_id} installed successfully",
                "already_existed": app_already_exists
            }
        
        except Exception as e:
            # Only cleanup if we created the directory
            if not app_already_exists and os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)
            raise Exception(f"Failed to install app {app_id}: {str(e)}")
    
    def _create_basic_manifest(self, manifest_path: str, app: Dict[str, Any]):
        """Create a basic app.manifest.json if it doesn't exist"""
        manifest = {
            "name": app.get("name"),
            "id": app.get("id"),
            "version": app.get("version", "1.0.0"),
            "description": app.get("description", ""),
            "category": app.get("category", "General"),
            "author": app.get("author", "Unknown"),
            "license": app.get("license", "MIT")
        }
        
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
    
    def _register_app_in_registry(self, app: Dict[str, Any], app_path: str):
        """Register app in apps-registry.json"""
        # Try container path first
        if os.path.exists("/app/apps-registry.json"):
            registry_path = "/app/apps-registry.json"
        else:
            registry_path = os.path.join(self.base_path, "abs-ai-hub", "apps-registry.json")
        
        # Load existing registry
        registry = {"version": "1.0.0", "description": "ABS AI Hub Applications Registry", "applications": []}
        if os.path.exists(registry_path):
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        
        # Check if app already in registry
        existing_ids = {a.get("id") for a in registry.get("applications", [])}
        if app.get("id") in existing_ids:
            logger.info(f"App {app.get('id')} already in registry, skipping registration")
            return  # Already registered
        
        # Try to get port from manifest if available
        port = 8080
        manifest_path = os.path.join(app_path, "app.manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    port = manifest.get("configuration", {}).get("port") or \
                           manifest.get("port") or \
                           app.get("requirements", {}).get("port", 8080)
            except Exception:
                pass
        
        # Get health check endpoint from manifest if available
        health_endpoint = "/healthz"
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    health_endpoint = manifest.get("configuration", {}).get("health_check", {}).get("endpoint") or \
                                    manifest.get("health") or "/healthz"
            except Exception:
                pass
        
        # Add app to registry
        app_entry = {
            "name": app.get("name"),
            "id": app.get("id"),
            "category": app.get("category", "General"),
            "description": app.get("description", ""),
            "entrypoint": "docker compose up -d",
            "healthcheck": {
                "url": f"http://localhost:{port}{health_endpoint}",
                "expect": "200"
            },
            "port": port,
            "icon": app.get("icon", "fas fa-cube"),
            "path": f"apps/{app.get('id')}"
        }
        
        registry.setdefault("applications", []).append(app_entry)
        
        # Save registry
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
    
    def _add_app_to_catalog(self, app: Dict[str, Any], app_path: str):
        """Add app to catalog.json as an asset"""
        catalog_path = os.path.join(os.path.dirname(__file__), "catalog.json")
        
        # Load existing catalog
        catalog = {"version": "1.0", "assets": []}
        if os.path.exists(catalog_path):
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog = json.load(f)
        
        # Check if app already in catalog
        existing_ids = {a.get("id") for a in catalog.get("assets", [])}
        if app.get("id") in existing_ids:
            logger.info(f"App {app.get('id')} already in catalog, skipping")
            return  # Already in catalog
        
        # Try to get port from manifest if available
        port = 8080
        health_endpoint = "/healthz"
        manifest_path = os.path.join(app_path, "app.manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    port = manifest.get("configuration", {}).get("port") or \
                           manifest.get("port") or \
                           app.get("requirements", {}).get("port", 8080)
                    health_endpoint = manifest.get("configuration", {}).get("health_check", {}).get("endpoint") or \
                                    manifest.get("health") or "/healthz"
            except Exception:
                pass
        
        # Get services from manifest if available
        services = app.get("requirements", {}).get("services", [])
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    gateway_config = manifest.get("configuration", {}).get("gateway_integration", {})
                    if gateway_config.get("services"):
                        services = gateway_config.get("services")
            except Exception:
                pass
        
        # Create asset entry
        asset = {
            "id": app.get("id"),
            "class": "app",
            "name": app.get("name"),
            "version": app.get("version", "1.0.0"),
            "description": app.get("description", ""),
            "owner": "user",
            "lifecycle": {
                "desired": "stopped",
                "actual": "stopped"
            },
            "policy": {
                "allowed_models": [],
                "allowed_embeddings": [],
                "defaults": {}
            },
            "health": {
                "status": "unknown",
                "url": f"http://localhost:{port}{health_endpoint}"
            },
            "metadata": {
                "category": app.get("category", "General"),
                "icon": app.get("icon", "fas fa-cube"),
                "url": f"http://localhost:{port}",
                "port": port,
                "path": f"apps/{app.get('id')}",
                "services": services
            }
        }
        
        catalog.setdefault("assets", []).append(asset)
        
        # Save catalog
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2)

