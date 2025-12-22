# Application Manifest Specification

**Version**: 1.0.0  
**Last Updated**: 2025-12-22  
**Status**: Active

---

## Overview

This document defines the structure and requirements for application manifests (`asset.yaml`) in the AI Fabric platform. Application manifests describe AI applications, their dependencies, lifecycle policies, and metadata required for runtime management.

---

## Manifest Structure

### File Format

- **Format**: YAML
- **File Name**: `asset.yaml`
- **Location**: `assets/apps/{app_id}/asset.yaml`
- **Encoding**: UTF-8

### Schema Version

```yaml
interface: application
interface_version: v1
class: app
```

---

## Core Fields

### 1. Identity Section

#### `asset_id` (required)
- **Type**: `string`
- **Pattern**: `^[a-z0-9-]+$` (lowercase alphanumeric with hyphens)
- **Description**: Unique identifier for the application
- **Example**: `contract-reviewer-v2`, `legal-assistant`
- **Validation**:
  - Must be unique across all assets
  - Maximum length: 64 characters
  - Must match directory name

#### `display_name` (required)
- **Type**: `string`
- **Description**: Human-readable name shown in UI
- **Example**: `"Contract Reviewer v2"`, `"Legal Assistant"`
- **Maximum Length**: 128 characters

#### `version` (required)
- **Type**: `string`
- **Format**: Semantic versioning (`major.minor.patch`)
- **Example**: `"1.0.0"`, `"2.1.3"`
- **Validation**: Must follow semver pattern `^\d+\.\d+\.\d+$`

#### `description` (required)
- **Type**: `string`
- **Description**: Brief description of application functionality
- **Recommended Length**: 50-200 characters
- **Example**: `"Professional AI-powered contract analysis platform with modern three-panel interface"`

---

### 2. Interface Classification

> [!IMPORTANT]
> **Interface Semantics**: The `interface: application` field is a **classification interface**, not a **runtime capability interface**. This distinguishes it from other ABS AI Fabric interfaces like `llm-runtime`, `vector-store`, or `cache-queue`, which define capability contracts for runtime services.

#### Understanding Interface Types in ABS AI Fabric

**Runtime Capability Interfaces** (e.g., `llm-runtime`, `vector-store`, `cache-queue`):
- Define specific capability contracts
- Specify standardized APIs and behaviors
- Enable provider substitution (e.g., swap Ollama for vLLM)
- Enforce interface compliance

**Classification Interfaces** (e.g., `application`):
- Categorize assets for discovery and management
- Do not define runtime behavior contracts
- Used for organizational purposes in the asset registry
- May have associated metadata schemas but not API contracts

#### `interface` (required)
- **Type**: `string`
- **Value**: `application` (fixed for app manifests)
- **Description**: Classification interface indicating this asset is an application
- **Semantic**: This is a **classification marker**, not a capability contract
- **Note**: Unlike runtime interfaces (`llm-runtime`, `vector-store`), this does not define a standardized API or enable provider substitution

#### `interface_version` (required)
- **Type**: `string`
- **Value**: `v1` (current version)
- **Description**: Version of the application manifest specification
- **Purpose**: Allows schema evolution while maintaining backward compatibility

#### `class` (required)
- **Type**: `string`
- **Value**: `app` (fixed for applications)
- **Description**: Asset class identifier used for filtering and discovery
- **Usage**: Enables queries like `/v1/assets?class=app`

#### Why Keep `interface: application`?

**Backward Compatibility**: Existing manifests and tooling depend on this field.

**Future Extensibility**: May evolve into capability interfaces if standard app APIs emerge (e.g., health checks, lifecycle management).

**Consistency**: Maintains uniform asset structure across all asset types.

---

### 3. Policy Section

The `policy` section defines model dependencies and configuration defaults.

```yaml
policy:
  required_models:
    - llama3.2:3b
    - llama3.2:latest
  allowed_embeddings:
    - legal-bert
    - bge-small-en-v1.5
  defaults:
    chat_model: llama3.2:3b
    embed_model: legal-bert
    provider: auto
    dim: 768
```

#### `policy.required_models` (optional)
- **Type**: `array<string>`
- **Description**: List of LLM models required by the application
- **Format**: Ollama model names (e.g., `model:tag`)
- **Usage**: Used for dependency checking and automatic provisioning
- **Example**: `["llama3.2:3b", "llama3:8b", "llama4:scout"]`

#### `policy.allowed_embeddings` (optional)
- **Type**: `array<string>`
- **Description**: List of allowed embedding models
- **Format**: Embedding model identifiers from asset registry
- **Example**: `["legal-bert", "nomic-embed-text", "all-minilm"]`

#### `policy.defaults` (optional)
- **Type**: `object`
- **Description**: Default configuration values
- **Fields**:
  - `chat_model`: Default LLM model for chat
  - `embed_model`: Default embedding model
  - `provider`: Provider preference (`auto`, `ollama`, `vllm`)
  - `dim`: Embedding dimension size (e.g., `384`, `768`)

---

### 4. Lifecycle Section

Defines application lifecycle behavior and resource management.

```yaml
lifecycle:
  desired: on-demand
  auto_sleep_min: 15
```

#### `lifecycle.desired` (required)
- **Type**: `string`
- **Allowed Values**:
  - `always-on`: Application always running
  - `on-demand`: Start when accessed, sleep after idle period
  - `manual`: Requires manual start/stop
- **Default**: `on-demand`
- **Description**: Desired runtime state

#### `lifecycle.auto_sleep_min` (optional)
- **Type**: `integer`
- **Description**: Minutes of inactivity before auto-sleep
- **Range**: `1-1440` (1 minute to 24 hours)
- **Default**: `15`
- **Applies To**: `on-demand` applications only

---

### 5. Ownership Section

Defines access control and visibility.

```yaml
ownership:
  provider: admin
  visibility: shared
  requestable: true
```

#### `ownership.provider` (required)
- **Type**: `string`
- **Allowed Values**:
  - `system`: System-provided application
  - `admin`: Administrator-managed
  - `user`: User-owned
- **Description**: Who manages the application

#### `ownership.visibility` (required)
- **Type**: `string`
- **Allowed Values**:
  - `public`: Visible to all users
  - `shared`: Visible within workspace
  - `private`: Only visible to owner
- **Default**: `shared`

#### `ownership.requestable` (optional)
- **Type**: `boolean`
- **Description**: Whether users can request access to this app
- **Default**: `true`

---

### 6. Metadata Section

> [!WARNING]
> **Mixed Concerns in V1**: The `metadata` section currently contains three distinct types of information:
> - **Entrypoints** (`url`, `port`): Runtime access information
> - **UI Hints** (`category`, `tags`, `icon`): Presentation layer metadata
> - **True Metadata** (`documentation_url`, `support_email`): Descriptive information
> 
> This is acceptable for v1 but will be restructured in v2 for better semantic clarity.

Additional application-specific metadata, UI hints, and runtime entrypoints.

```yaml
metadata:
  # Entrypoint (really runtime, not metadata)
  url: http://localhost:8082
  port: 8082
  
  # UI hints (really presentation, not metadata)
  icon: contract.svg
  category: Legal Apps
  tags:
    - contract-analysis
    - nlp
    - legal
  
  # True metadata
  documentation_url: https://docs.example.com/contract-reviewer
  support_email: support@example.com
  status: active
```

#### `metadata.url` (required)
- **Type**: `string`
- **Format**: Valid HTTP/HTTPS URL
- **Description**: Application access URL (entrypoint)
- **Example**: `http://localhost:8082`
- **Semantic Note**: This is an **entrypoint**, not metadata. Will move to `entrypoint.url` in v2.

#### `metadata.port` (optional)
- **Type**: `integer`
- **Range**: `1024-65535`
- **Description**: Primary application port
- **Extracted From**: URL if not specified
- **Semantic Note**: This is an **entrypoint detail**, not metadata. Will move to `entrypoint.port` in v2.

#### `metadata.icon` (optional)
- **Type**: `string`
- **Description**: Relative path to application icon
- **Format**: SVG, PNG, or JPG
- **Location**: `assets/apps/{app_id}/{icon}`
- **Semantic Note**: This is a **UI hint**, not metadata. Will move to `ui.icon` in v2.

#### `metadata.category` (optional)
- **Type**: `string`
- **Description**: Application category for grouping
- **Examples**: `"Legal Apps"`, `"Document Processing"`, `"Chat Assistants"`
- **Semantic Note**: This is a **UI classification**, not metadata. Will move to `ui.category` in v2.

#### `metadata.tags` (optional)
- **Type**: `array<string>`
- **Description**: Searchable tags for discovery
- **Example**: `["contract-analysis", "nlp", "legal"]`
- **Semantic Note**: This is a **UI hint**, not metadata. Will move to `ui.tags` in v2.

#### `metadata.status` (optional)
- **Type**: `string`
- **Allowed Values**: `active`, `disabled`, `deprecated`
- **Description**: Lifecycle management status
- **Default**: `active`
- **Semantic Note**: This is **lifecycle state**, not metadata. May move to `lifecycle.status` in v2.

#### `metadata.documentation_url` (optional)
- **Type**: `string`
- **Format**: Valid HTTP/HTTPS URL
- **Description**: Link to application documentation
- **Semantic Note**: This is **true metadata** and will remain in `metadata` in v2.

#### `metadata.support_email` (optional)
- **Type**: `string`
- **Format**: Valid email address
- **Description**: Support contact email
- **Semantic Note**: This is **true metadata** and will remain in `metadata` in v2.

#### V2 Restructuring Plan

In v2, the `metadata` section will be split into semantically distinct sections:

```yaml
# Future v2 structure
entrypoint:
  url: http://localhost:8082
  port: 8082
  protocol: http
  health_check: /health

ui:
  icon: contract.svg
  category: Legal Apps
  tags:
    - contract-analysis
    - legal-tech
  theme:
    primary_color: "#FF6B00"
    
metadata:
  # True free-form descriptive metadata only
  documentation_url: https://docs.example.com
  support_email: support@example.com
  license: MIT
  vendor: ABS Legal Tech
  custom_field: any_value
```

**Benefits of Restructuring**:
- **Semantic Clarity**: Each section has a clear, single purpose
- **Validation**: Can enforce strict schemas for `entrypoint` and `ui`, while keeping `metadata` flexible
- **Extensibility**: Easier to add new entrypoint types (WebSocket, gRPC) or UI hints without polluting metadata
- **Tooling**: Tools can target specific sections (e.g., UI builders read `ui`, health checkers read `entrypoint`)

---

## Complete Example

```yaml
asset_id: contract-reviewer-v2
display_name: Contract Reviewer v2
version: "1.0.0"

interface: application
interface_version: v1
class: app

description: Professional AI-powered contract analysis platform with modern three-panel interface

policy:
  required_models:
    - llama3.2:3b
    - llama3.2:latest
    - llama3:8b
    - llama4:scout
  allowed_embeddings:
    - legal-bert
    - nomic-embed-text
    - mxbai-embed-large
    - bge-small-en-v1.5
  defaults:
    chat_model: llama3.2:3b
    embed_model: legal-bert
    provider: auto
    dim: 768

lifecycle:
  desired: on-demand
  auto_sleep_min: 15

ownership:
  provider: admin
  visibility: shared
  requestable: true

metadata:
  url: http://localhost:8082
  port: 8082
  category: Legal Apps
  tags:
    - contract-analysis
    - legal-tech
    - ai-assistant
```

---

## Validation Rules

### Required Fields
All manifests MUST include:
- `asset_id`
- `display_name`
- `version`
- `interface` (must be `"application"`)
- `interface_version` (must be `"v1"`)
- `class` (must be `"app"`)
- `description`
- `lifecycle.desired`
- `ownership.provider`
- `ownership.visibility`
- `metadata.url`

### Field Constraints
1. **Unique Identifiers**: `asset_id` must be unique across all assets
2. **Version Format**: `version` must follow semantic versioning
3. **Model References**: Models in `required_models` and `allowed_embeddings` should exist in the registry
4. **URL Format**: `metadata.url` must be a valid, reachable URL
5. **Lifecycle Compatibility**: `auto_sleep_min` only valid when `desired: on-demand`

### Best Practices
1. Use descriptive `asset_id` values (prefer `contract-reviewer-v2` over `cr2`)
2. Keep `description` concise but informative
3. Always specify `defaults` if app has configurable models
4. Include `tags` for better discoverability
5. Set realistic `auto_sleep_min` values based on startup time
6. Document all `required_models` to prevent runtime failures

---

## Manifest Management

### Discovery
Applications are discovered by scanning:
```
assets/apps/*/asset.yaml
```

### Registration
1. Place application files in `assets/apps/{app_id}/`
2. Create `asset.yaml` following this specification
3. Add entry to asset registry: `assets/registry/assets.json`
```json
{
  "id": "contract-reviewer-v2",
  "interface": "application",
  "path": "apps/contract-reviewer-v2"
}
```
4. Restart gateway or trigger asset reload

### Validation
Run validation before registration:
```bash
# Validate YAML syntax
yamllint assets/apps/{app_id}/asset.yaml

# Validate against schema (if schema tool available)
validate-manifest assets/apps/{app_id}/asset.yaml
```

### Deregistration
To remove an application:
1. Remove from `assets/registry/assets.json`
2. Delete application directory: `assets/apps/{app_id}/`
3. Restart gateway or trigger asset reload

---

## UI Integration

### Display Fields
The UI uses these fields for rendering:
- `display_name`: Card title, page headers
- `description`: Card description
- `metadata.url`: "Open App" button link
- `metadata.icon`: Card icon (fallback to default if missing)
- `metadata.category`: Grouping and filtering
- `policy.required_models`: Dependency indicators
- `lifecycle.desired`: Status badges

### Status Determination
Application status is derived from:
- **Online**: Application responding at `metadata.url`
- **Offline**: Application registered but not responding
- **Degraded**: Application responding with errors
- **Unknown**: Unable to determine status

### Filtering
Apps can be filtered/excluded programmatically:
```typescript
// Exclude specific apps from "Installed" view
const installedApps = computed(() =>
    apps.value.filter(a => 
        (a.status === 'online' || a.status === 'offline') && 
        a.id !== 'deposition-summarizer'  // Example exclusion
    )
)
```

---

## Future Enhancements

### Planned Fields (v2)
- `health_check`: Custom health check endpoints
- `dependencies`: Service dependencies beyond models
- `scaling`: Auto-scaling configuration
- `monitoring`: Custom metrics and alerts
- `backup`: Data backup policies
- `security`: Security policies and authentication
- `resource_limits`: CPU/memory constraints

### Interface Evolution: From Classification to Capability

**Current State** (v1):
`interface: application` is a classification marker with no enforced contract.

**Potential Future** (v2+):
If application standardization emerges, `interface: application` could evolve into a **runtime capability interface**, defining:

**Standard Application APIs**:
```yaml
# Future capability contract
interface: application
interface_version: v2
capabilities:
  health:
    endpoint: /health
    method: GET
    expected_response: { "status": "healthy|degraded|unhealthy" }
  lifecycle:
    start: POST /admin/start
    stop: POST /admin/stop
    restart: POST /admin/restart
  metrics:
    endpoint: /metrics
    format: prometheus
```

**Benefits of Evolution**:
- **Standardized Management**: Uniform lifecycle control across all apps
- **Better Monitoring**: Consistent health check and metrics interfaces
- **Gateway Integration**: Hub can manage apps without app-specific logic
- **Provider Substitution**: Swap app implementations while maintaining interface

**Migration Strategy**:
1. V1 manifests remain valid indefinitely (classification only)
2. V2 adds optional capability declarations
3. Apps implementing V2 capabilities gain advanced management features
4. V1 apps continue to work with basic lifecycle support

**Decision Point**:
Whether to evolve `application` into a capability interface depends on:
- Emergence of common patterns across multiple apps
- Need for standardized lifecycle management
- Cost/benefit of enforcement vs flexibility

### Migration Path
V1 manifests will remain supported. V2 additions will be optional and backward-compatible.

---

## Related Documentation

- [Asset Registry Specification](./asset_registry_specification.md)
- [Model Manifest Specification](./model_manifest_specification.md)
- [Gateway API Documentation](./gateway_api.md)
- [App Development Guide](../development/app_development_guide.md)

---

## Change Log

### Version 1.0.0 (2025-12-22)
- Initial specification based on existing app manifests
- Documented all current fields and patterns
- Added validation rules and best practices
- Defined UI integration patterns
