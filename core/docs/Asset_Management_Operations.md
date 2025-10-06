# Asset Management Operations Guide

## Overview

The ABS AI Hub implements a comprehensive asset management system where all resources (apps, services, models, tools, datasets, secrets) are managed through a unified catalog with consistent operations: **Edit**, **Enable/Disable**, and **Delete**.

## Architecture

```
Management UI (manage.html) → Hub Gateway (/admin/assets) → catalog.json → Policy Enforcement
```

## Asset Types and Operations

### 📱 Applications (Apps)

Applications are containerized services that provide specific functionality to users.

#### **Edit Operations**
- **Policy Configuration**
  - Modify `allowed_models`: Change which LLM models the app can use
  - Modify `allowed_embeddings`: Change which embedding models are permitted
  - Update `defaults`: Set default chat model, embedding model, provider, dimensions
- **Metadata Updates**
  - Change `url`: Update application endpoint
  - Modify `description`: Update app description
  - Update configuration parameters
- **Lifecycle Settings**
  - Set `lifecycle.desired`: running, stopped, or paused

**Example Edit:**
```json
{
  "policy": {
    "allowed_models": ["llama3.2:7b", "llama3.2:latest"],
    "allowed_embeddings": ["legal-bert", "bge-small-en-v1.5"],
    "defaults": {
      "chat_model": "llama3.2:7b",
      "embed_model": "legal-bert",
      "provider": "huggingface",
      "dim": 768
    }
  }
}
```

#### **Enable/Disable Operations**
- **Enable**: `lifecycle.desired = "running"`
  - Gateway starts Docker container
  - App becomes accessible via its URL
  - Health checks begin monitoring
- **Disable**: `lifecycle.desired = "stopped"`
  - Gateway stops Docker container
  - App becomes inaccessible
  - Resources are freed
- **Pause**: `lifecycle.desired = "paused"`
  - Gateway pauses container (if supported)
  - App state preserved but not accessible

#### **Delete Operations**
- Remove asset from `catalog.json`
- Gateway stops and removes Docker container
- Remove from service discovery
- Clean up audit logs and references
- **Warning**: This is irreversible and will make the app unavailable

---

### ⚙️ Services (Core Infrastructure)

Core services provide foundational capabilities (LLM backends, vector databases, caches).

#### **Edit Operations**
- **Configuration Updates**
  - Modify service URLs and endpoints
  - Update health check endpoints
  - Change container names and configurations
- **Lifecycle Management**
  - Set desired state (running/stopped)
- **Service Discovery**
  - Update metadata for service discovery

**Example Service Edit:**
```json
{
  "metadata": {
    "url": "http://localhost:11434",
    "health": "http://localhost:11434/api/tags",
    "container": "abs-ollama"
  },
  "lifecycle": {
    "desired": "running"
  }
}
```

#### **Enable/Disable Operations**
- **Enable**: Start core service container
  - Service becomes available to all dependent apps
  - Health monitoring begins
- **Disable**: Stop core service container
  - Service becomes unavailable
  - Dependent apps may fail

#### **Delete Operations**
- Remove service from catalog and service discovery
- Stop and remove service container
- **Critical Warning**: This may break all dependent applications
- **Impact**: Apps using this service will lose functionality

---

### 🧠 Models

Models define LLM and embedding capabilities with provider routing.

#### **Edit Operations**
- **Provider Mapping**
  - Update which provider serves which model
  - Modify aliases in `registry.json`
- **Configuration**
  - Update model parameters and dimensions
  - Change model capabilities and descriptions

**Example Model Edit:**
```json
{
  "aliases": {
    "llama3.2:latest": {
      "openai": "llama3.2:latest",
      "ollama": "llama3.2:latest",
      "huggingface": "meta-llama/Llama-3.2-11B"
    }
  }
}
```

#### **Enable/Disable Operations**
- **Enable**: Model available for use by apps
- **Disable**: Model blocked from use (policy enforcement)
- **Effect**: Apps cannot use disabled models

#### **Delete Operations**
- Remove alias from `registry.json`
- Remove from all app `allowed_models` lists
- **Impact**: Apps using this model will need to switch to alternatives

---

### 🔧 Tools

Tools provide specific processing capabilities (OCR, parsing, chunking).

#### **Edit Operations**
- **Configuration**
  - Update endpoint URLs and parameters
  - Modify tool capabilities and descriptions
- **Metadata**
  - Change tool descriptions and categories

**Example Tool Edit:**
```json
{
  "metadata": {
    "endpoint": "http://localhost:8003/ocr",
    "capabilities": ["image", "pdf"],
    "max_file_size": "10MB"
  }
}
```

#### **Enable/Disable Operations**
- **Enable**: Tool available for use by apps
- **Disable**: Tool blocked from use
- **Effect**: Apps cannot access disabled tools

#### **Delete Operations**
- Remove tool from catalog
- **Impact**: Apps using this tool will lose functionality

---

### 📊 Datasets

Datasets represent collections of data for training, analysis, or RAG.

#### **Edit Operations**
- **Storage Configuration**
  - Update dataset location and storage type
  - Modify access permissions and paths
- **Metadata**
  - Change descriptions, versions, and schemas
  - Update data quality and lineage information

**Example Dataset Edit:**
```json
{
  "metadata": {
    "storage_type": "minio",
    "path": "s3://datasets/contracts/v2/",
    "version": "2.1",
    "access_level": "restricted"
  }
}
```

#### **Enable/Disable Operations**
- **Enable**: Dataset available for ingestion and querying
- **Disable**: Dataset blocked from access
- **Effect**: Apps cannot use disabled datasets

#### **Delete Operations**
- Remove dataset from catalog
- **Warning**: May break apps that depend on the dataset
- **Impact**: Apps using this dataset will lose access to data

---

### 🔐 Secrets

Secrets manage sensitive information like API keys and credentials.

#### **Edit Operations**
- **Configuration**
  - Update secret location and type (env_var vs vault)
  - Modify access scope and permissions
- **Metadata**
  - Change descriptions and usage information

**Example Secret Edit:**
```json
{
  "metadata": {
    "type": "vault",
    "vault_path": "secret/openai/api-key-v2",
    "access_scope": ["contract-reviewer", "onyx-assistant"]
  }
}
```

#### **Enable/Disable Operations**
- **Enable**: Secret available for apps to use
- **Disable**: Secret blocked from access
- **Effect**: Apps cannot access disabled secrets

#### **Delete Operations**
- Remove secret from catalog
- **Warning**: May break apps that need the secret
- **Impact**: Apps using this secret will lose access to external services

---

## Implementation Details

### Gateway Integration

The Hub Gateway (`core/gateway/app.py`) handles all asset operations:

1. **API Endpoints**
   - `POST /admin/assets` - Create new asset
   - `PUT /admin/assets/{asset_id}` - Update existing asset
   - `DELETE /admin/assets/{asset_id}` - Delete asset
   - `POST /admin/assets/{asset_id}/lifecycle` - Set lifecycle state

2. **Policy Enforcement**
   - Immediately enforces policy changes
   - Blocks unauthorized model/embedding usage
   - Updates service discovery automatically

3. **Container Management**
   - Starts/stops Docker containers based on lifecycle state
   - Monitors health and restarts failed containers
   - Manages resource allocation

### Management UI

The management interface (`abs-ai-hub/hub-ui/assets/manage.html`) provides:

1. **Asset Browser**
   - Grouped by type (Apps, Services, Models, Tools, Datasets, Secrets)
   - Collapsible sections with counts
   - Real-time status indicators

2. **CRUD Operations**
   - Add new assets with validation
   - Edit existing assets with form pre-population
   - Delete with confirmation dialogs
   - Enable/disable with immediate feedback

3. **Policy Management**
   - Visual policy editor for apps
   - Model and embedding selection
   - Default configuration management

### Operation Workflow

```
1. User initiates operation in Management UI
2. UI validates input and shows impact warnings
3. UI sends request to Gateway API
4. Gateway updates catalog.json
5. Gateway enforces changes immediately
6. Gateway manages containers (if applicable)
7. UI refreshes to show updated state
8. Audit log records the operation
```

## Best Practices

### Before Making Changes

1. **Check Dependencies**
   - Review which apps use the asset
   - Understand impact of changes
   - Plan for rollback if needed

2. **Validate Configuration**
   - Ensure URLs are accessible
   - Verify model names are correct
   - Check policy consistency

3. **Test in Staging**
   - Test changes in non-production environment
   - Verify all dependent apps still work
   - Validate performance impact

### Safe Operations

1. **Enable/Disable First**
   - Use enable/disable to test changes
   - Revert quickly if issues occur
   - Less disruptive than delete/recreate

2. **Gradual Rollout**
   - Change one app at a time
   - Monitor for issues
   - Roll back if problems arise

3. **Document Changes**
   - Record what was changed and why
   - Note any issues encountered
   - Update runbooks if needed

### Emergency Procedures

1. **Quick Disable**
   - Set `lifecycle.desired = "stopped"`
   - Immediately stops problematic assets
   - Preserves configuration for later analysis

2. **Policy Rollback**
   - Revert to previous policy configuration
   - Use version control to track changes
   - Test rollback in staging first

3. **Service Recovery**
   - Check service health endpoints
   - Restart failed containers
   - Review logs for error patterns

## Monitoring and Observability

### Health Checks

All assets include health monitoring:
- **Apps**: HTTP health endpoints
- **Services**: Container status and service endpoints
- **Models**: Provider availability and model loading
- **Tools**: Endpoint accessibility and response times

### Audit Logging

All operations are logged:
- **Who**: User/app that made the change
- **What**: Asset and operation performed
- **When**: Timestamp of the operation
- **Why**: Reason for the change (if provided)

### Metrics

Track key metrics:
- **Asset Availability**: Uptime and health status
- **Operation Success**: Success/failure rates
- **Policy Violations**: Blocked requests and reasons
- **Resource Usage**: Container resource consumption

## Troubleshooting

### Common Issues

1. **Policy Enforcement Failures**
   - Check model names in aliases
   - Verify app has required permissions
   - Review gateway logs for details

2. **Container Management Issues**
   - Check Docker daemon status
   - Verify network connectivity
   - Review container logs

3. **Service Discovery Problems**
   - Verify service registration in catalog
   - Check service health endpoints
   - Review network configuration

### Debug Commands

```bash
# Check catalog status
curl http://localhost:8081/catalog

# Check specific asset
curl http://localhost:8081/assets/{asset_id}

# Check service discovery
curl http://localhost:8081/.well-known/abs-services

# Check container status
docker ps --filter "name=abs-"
```

## Security Considerations

### Access Control

- **Authentication**: All admin operations require authentication
- **Authorization**: Role-based access to different asset types
- **Audit**: All operations logged for compliance

### Secret Management

- **Encryption**: Secrets encrypted at rest and in transit
- **Rotation**: Regular secret rotation procedures
- **Access**: Minimal access principle for secrets

### Policy Enforcement

- **Validation**: All policy changes validated before application
- **Isolation**: Apps cannot access unauthorized resources
- **Monitoring**: Continuous monitoring for policy violations

---

*This document provides comprehensive guidance for managing assets in the ABS AI Hub control plane. For specific implementation details, refer to the source code in `core/gateway/app.py` and `abs-ai-hub/hub-ui/assets/manage.html`.*
