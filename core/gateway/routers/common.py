from fastapi import APIRouter

# Helper to load registry for models/catalogs
# This is a bit duplicative of logic in legacy app.py, but essential for routers
import os
import json
from config import REGISTRY_PATH, APPS_REGISTRY_PATH, CATALOG_PATH

def get_registry():
    REG = {}
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            REG = json.load(f)
    return REG

def get_catalog():
    CATALOG = {}
    if os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                CATALOG = json.load(f)
        except Exception:
            pass
    return CATALOG

def save_registry(reg):
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2)

def save_catalog(cat):
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2)
