# ABS App Registry API
# Provides dynamic app list for the unified framework

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import json
import os

router = APIRouter()

@router.get("/api/apps")
async def get_apps():
    """Get list of available ABS applications"""
    try:
        # Load from apps-registry.json
        registry_path = os.path.join(os.path.dirname(__file__), "..", "apps-registry.json")
        
        if os.path.exists(registry_path):
            with open(registry_path, 'r') as f:
                registry = json.load(f)
            
            apps = []
            for app_id, app_info in registry.get("apps", {}).items():
                app_data = {
                    "id": app_id,
                    "name": app_info.get("name", app_id.replace("-", " ").title()),
                    "description": app_info.get("description", "ABS Application"),
                    "icon": app_info.get("icon", "fas fa-cube"),
                    "colorClass": app_info.get("colorClass", "bg-gray-600"),
                    "url": app_info.get("url", f"/{app_id}"),
                    "status": app_info.get("status", "active"),
                    "version": app_info.get("version", "1.0.0"),
                    "category": app_info.get("category", "general"),
                    "tags": app_info.get("tags", []),
                    "permissions": app_info.get("permissions", []),
                    "config": app_info.get("config", {})
                }
                apps.append(app_data)
            
            return {
                "apps": apps,
                "total": len(apps),
                "categories": list(set(app.get("category") for app in apps)),
                "last_updated": os.path.getmtime(registry_path)
            }
        else:
            # Fallback to hardcoded apps
            return {
                "apps": [
                    {
                        "id": "contract-reviewer",
                        "name": "Contract Reviewer",
                        "description": "AI Contract Analysis",
                        "icon": "fas fa-file-contract",
                        "colorClass": "bg-blue-600",
                        "url": "/contract-reviewer",
                        "status": "active",
                        "version": "1.0.0",
                        "category": "legal",
                        "tags": ["contracts", "ai", "analysis"],
                        "permissions": ["read", "write"],
                        "config": {}
                    },
                    {
                        "id": "contract-reviewer-v2",
                        "name": "Contract Reviewer v2",
                        "description": "Professional AI Contract Analysis",
                        "icon": "fas fa-file-contract",
                        "colorClass": "bg-blue-600",
                        "url": "/contract-reviewer-v2",
                        "status": "active",
                        "version": "2.0.0",
                        "category": "legal",
                        "tags": ["contracts", "ai", "analysis", "professional"],
                        "permissions": ["read", "write", "export"],
                        "config": {
                            "enableExport": True,
                            "enableSettings": True,
                            "customMenuItems": [
                                {
                                    "id": "export",
                                    "label": "Export",
                                    "icon": "fas fa-download",
                                    "action": "exportResults"
                                }
                            ]
                        }
                    },
                    {
                        "id": "legal-assistant",
                        "name": "Legal Assistant",
                        "description": "AI Legal Research Assistant",
                        "icon": "fas fa-gavel",
                        "colorClass": "bg-green-600",
                        "url": "/legal-assistant",
                        "status": "active",
                        "version": "1.0.0",
                        "category": "legal",
                        "tags": ["research", "ai", "legal"],
                        "permissions": ["read", "write"],
                        "config": {}
                    },
                    {
                        "id": "onyx",
                        "name": "Onyx",
                        "description": "AI Document Processing",
                        "icon": "fas fa-brain",
                        "colorClass": "bg-purple-600",
                        "url": "/onyx",
                        "status": "active",
                        "version": "1.0.0",
                        "category": "ai",
                        "tags": ["document", "processing", "ai"],
                        "permissions": ["read", "write"],
                        "config": {}
                    },
                    {
                        "id": "rag-pdf-voice",
                        "name": "RAG PDF Voice",
                        "description": "Voice-Enabled Document Search",
                        "icon": "fas fa-microphone",
                        "colorClass": "bg-red-600",
                        "url": "/rag-pdf-voice",
                        "status": "active",
                        "version": "1.0.0",
                        "category": "ai",
                        "tags": ["voice", "search", "pdf"],
                        "permissions": ["read", "write"],
                        "config": {}
                    },
                    {
                        "id": "whisper-server",
                        "name": "Whisper Server",
                        "description": "Speech-to-Text Service",
                        "icon": "fas fa-volume-up",
                        "colorClass": "bg-orange-600",
                        "url": "/whisper-server",
                        "status": "active",
                        "version": "1.0.0",
                        "category": "ai",
                        "tags": ["speech", "text", "service"],
                        "permissions": ["read"],
                        "config": {}
                    }
                ],
                "total": 6,
                "categories": ["legal", "ai"],
                "last_updated": None
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load app registry: {str(e)}")

@router.get("/api/apps/{app_id}")
async def get_app(app_id: str):
    """Get specific app information"""
    try:
        apps_response = await get_apps()
        app = next((app for app in apps_response["apps"] if app["id"] == app_id), None)
        
        if not app:
            raise HTTPException(status_code=404, detail=f"App '{app_id}' not found")
        
        return app
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get app info: {str(e)}")

@router.post("/api/apps/{app_id}/config")
async def update_app_config(app_id: str, config: Dict[str, Any]):
    """Update app configuration"""
    try:
        # This would typically update a database or config file
        # For now, just return success
        return {
            "message": f"App '{app_id}' configuration updated",
            "app_id": app_id,
            "config": config
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update app config: {str(e)}")

@router.get("/api/apps/categories")
async def get_app_categories():
    """Get list of app categories"""
    try:
        apps_response = await get_apps()
        categories = {}
        
        for app in apps_response["apps"]:
            category = app["category"]
            if category not in categories:
                categories[category] = {
                    "name": category.title(),
                    "count": 0,
                    "apps": []
                }
            
            categories[category]["count"] += 1
            categories[category]["apps"].append({
                "id": app["id"],
                "name": app["name"],
                "description": app["description"],
                "icon": app["icon"],
                "colorClass": app["colorClass"]
            })
        
        return categories
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")
