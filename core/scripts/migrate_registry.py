#!/usr/bin/env python3
"""
Registry Migration Script

Converts legacy registry.json and catalog.json to the new
assets/ directory structure with asset.yaml files.

Usage:
    python migrate_registry.py --input-dir ../gateway --output-dir ../../assets
"""

import os
import sys
import json
import argparse
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


def load_json(path: str) -> dict:
    """Load a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def sanitize_path(name: str) -> str:
    """Sanitize a name for use in file paths (Windows compatible)."""
    # Replace invalid Windows path characters
    invalid_chars = [':', '*', '?', '"', '<', '>', '|']
    result = name
    for char in invalid_chars:
        result = result.replace(char, '_')
    return result


def save_yaml(path: str, data: dict):
    """Save data as YAML file."""
    # Sanitize path components for Windows
    path_obj = Path(path)
    safe_parts = [sanitize_path(part) for part in path_obj.parts]
    safe_path = Path(*safe_parts)
    
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    with open(safe_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"  Created: {safe_path}")


def convert_app_asset(asset: dict) -> dict:
    """Convert an app asset from catalog format to asset.yaml format."""
    return {
        'asset_id': asset.get('id'),
        'display_name': asset.get('name'),
        'interface': 'application',
        'interface_version': 'v1',
        'class': 'app',
        'description': asset.get('description', ''),
        'policy': asset.get('policy', {}),
        'metadata': asset.get('metadata', {}),
        'lifecycle': asset.get('lifecycle', {'desired': 'on-demand'})
    }


def convert_service_asset(asset: dict) -> dict:
    """Convert a service asset to asset.yaml format."""
    service_type = asset.get('type', 'unknown')
    
    # Map service types to interfaces
    interface_map = {
        'llm-backend': 'llm-runtime',
        'vector-db': 'vector-store',
        'database': 'metadata-store',
        'asr': 'speech'
    }
    
    return {
        'asset_id': asset.get('id'),
        'display_name': asset.get('name'),
        'interface': interface_map.get(service_type, service_type),
        'interface_version': 'v1',
        'class': 'service',
        'description': asset.get('description', ''),
        'container': {
            'name': asset.get('metadata', {}).get('container', f"abs-{asset.get('id')}")
        },
        'endpoints': {
            'health': asset.get('metadata', {}).get('health', '')
        },
        'metadata': asset.get('metadata', {}),
        'lifecycle': asset.get('lifecycle', {'desired': 'running'})
    }


def convert_model_asset(asset: dict) -> dict:
    """Convert a model asset to asset.yaml format."""
    return {
        'asset_id': asset.get('id'),
        'display_name': asset.get('name'),
        'interface': 'model',
        'interface_version': 'v1',
        'class': 'model',
        'description': asset.get('description', ''),
        'provider': asset.get('metadata', {}).get('provider', 'ollama'),
        'metadata': asset.get('metadata', {}),
        'lifecycle': asset.get('lifecycle', {'desired': 'on-demand'})
    }


def convert_tool_asset(tool: dict) -> dict:
    """Convert a tool to asset.yaml format."""
    return {
        'asset_id': tool.get('id'),
        'display_name': tool.get('name'),
        'interface': 'tool',
        'interface_version': 'v1',
        'class': 'tool',
        'type': tool.get('type', 'utility'),
        'endpoint': tool.get('endpoint', ''),
        'policy': tool.get('policy', {}),
        'metadata': tool.get('metadata', {}),
        'lifecycle': {'desired': 'on-demand'}
    }


def migrate_catalog(catalog_path: str, output_dir: str, dry_run: bool = False):
    """Migrate catalog.json to asset.yaml files."""
    print(f"\n[Migrating Catalog] {catalog_path}")
    
    catalog = load_json(catalog_path)
    assets = catalog.get('assets', [])
    tools = catalog.get('tools', [])
    datasets = catalog.get('datasets', [])
    
    stats = {'apps': 0, 'services': 0, 'models': 0, 'tools': 0, 'datasets': 0}
    
    # Migrate assets
    for asset in assets:
        asset_class = asset.get('class', 'unknown')
        asset_id = asset.get('id', 'unknown')
        
        if asset_class == 'app':
            converted = convert_app_asset(asset)
            out_path = os.path.join(output_dir, 'apps', asset_id, 'asset.yaml')
            stats['apps'] += 1
        elif asset_class == 'service':
            converted = convert_service_asset(asset)
            interface = converted.get('interface', 'service')
            out_path = os.path.join(output_dir, 'core', interface, asset_id, 'asset.yaml')
            stats['services'] += 1
        elif asset_class == 'model':
            converted = convert_model_asset(asset)
            out_path = os.path.join(output_dir, 'models', asset_id, 'asset.yaml')
            stats['models'] += 1
        else:
            print(f"  Skipping unknown class: {asset_class} ({asset_id})")
            continue
        
        if not dry_run:
            save_yaml(out_path, converted)
        else:
            print(f"  [DRY-RUN] Would create: {out_path}")
    
    # Migrate tools
    for tool in tools:
        converted = convert_tool_asset(tool)
        tool_id = tool.get('id', 'unknown')
        out_path = os.path.join(output_dir, 'tools', tool_id, 'asset.yaml')
        stats['tools'] += 1
        
        if not dry_run:
            save_yaml(out_path, converted)
        else:
            print(f"  [DRY-RUN] Would create: {out_path}")
    
    # Migrate datasets (simplified)
    for ds in datasets:
        ds_id = ds.get('id', 'unknown')
        out_path = os.path.join(output_dir, 'datasets', ds_id, 'asset.yaml')
        stats['datasets'] += 1
        
        converted = {
            'asset_id': ds_id,
            'display_name': ds.get('name', ds_id),
            'interface': 'dataset',
            'interface_version': 'v1',
            'class': 'dataset',
            'type': ds.get('type', 'files'),
            'storage': ds.get('storage', {}),
            'policy': ds.get('policy', {}),
            'metadata': ds.get('metadata', {})
        }
        
        if not dry_run:
            save_yaml(out_path, converted)
        else:
            print(f"  [DRY-RUN] Would create: {out_path}")
    
    return stats


def migrate_registry(registry_path: str, output_dir: str, dry_run: bool = False):
    """Migrate registry.json aliases to a centralized aliases.yaml."""
    print(f"\n[Migrating Registry] {registry_path}")
    
    registry = load_json(registry_path)
    aliases = registry.get('aliases', {})
    
    out_path = os.path.join(output_dir, 'registry', 'aliases.yaml')
    
    converted = {
        'version': '1.0',
        'description': 'Model name aliases mapping logical names to provider-specific IDs',
        'aliases': aliases
    }
    
    if not dry_run:
        save_yaml(out_path, converted)
    else:
        print(f"  [DRY-RUN] Would create: {out_path}")
    
    return len(aliases)


def update_assets_index(output_dir: str, dry_run: bool = False):
    """Regenerate assets/registry/assets.json index."""
    print(f"\n[Updating Asset Index]")
    
    index = {
        'version': '1.0',
        'description': 'ABS AI Fabric Asset Registry Index',
        'core_assets': [],
        'apps': [],
        'models': [],
        'tools': [],
        'datasets': []
    }
    
    # Scan for asset.yaml files
    for root, dirs, files in os.walk(output_dir):
        if 'asset.yaml' in files:
            rel_path = os.path.relpath(os.path.join(root, 'asset.yaml'), output_dir)
            
            # Load to get asset_id and interface
            with open(os.path.join(root, 'asset.yaml'), 'r') as f:
                asset = yaml.safe_load(f)
            
            entry = {
                'id': asset.get('asset_id'),
                'interface': asset.get('interface'),
                'path': rel_path.replace('\\', '/')
            }
            
            asset_class = asset.get('class', 'unknown')
            if asset_class == 'service':
                index['core_assets'].append(entry)
            elif asset_class == 'app':
                index['apps'].append(entry)
            elif asset_class == 'model':
                index['models'].append(entry)
            elif asset_class == 'tool':
                index['tools'].append(entry)
            elif asset_class == 'dataset':
                index['datasets'].append(entry)
    
    out_path = os.path.join(output_dir, 'registry', 'assets.json')
    
    if not dry_run:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
        print(f"  Updated: {out_path}")
    else:
        print(f"  [DRY-RUN] Would update: {out_path}")
    
    return index


def main():
    parser = argparse.ArgumentParser(description='Migrate legacy registry to asset.yaml format')
    parser.add_argument('--input-dir', default='../gateway', help='Directory containing registry.json and catalog.json')
    parser.add_argument('--output-dir', default='../../assets', help='Output directory for assets/')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.abspath(args.output_dir)
    
    print(f"ABS AI Fabric - Registry Migration")
    print(f"===================================")
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Mode:   {'DRY-RUN' if args.dry_run else 'LIVE'}")
    
    # Check input files
    catalog_path = os.path.join(input_dir, 'catalog.json')
    registry_path = os.path.join(input_dir, 'registry.json')
    
    if not os.path.exists(catalog_path):
        print(f"Error: catalog.json not found at {catalog_path}")
        sys.exit(1)
    
    if not os.path.exists(registry_path):
        print(f"Warning: registry.json not found at {registry_path}")
        registry_path = None
    
    # Migrate
    stats = migrate_catalog(catalog_path, output_dir, args.dry_run)
    
    alias_count = 0
    if registry_path:
        alias_count = migrate_registry(registry_path, output_dir, args.dry_run)
    
    # Update index
    if not args.dry_run:
        update_assets_index(output_dir, args.dry_run)
    
    print(f"\n[Summary]")
    print(f"  Apps:     {stats['apps']}")
    print(f"  Services: {stats['services']}")
    print(f"  Models:   {stats['models']}")
    print(f"  Tools:    {stats['tools']}")
    print(f"  Datasets: {stats['datasets']}")
    print(f"  Aliases:  {alias_count}")
    print(f"\nMigration {'would be' if args.dry_run else ''} complete!")


if __name__ == '__main__':
    main()
