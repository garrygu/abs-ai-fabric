# Auto-Wake Dependency Management

## Overview

The ABS AI Hub auto-wake mechanism now includes comprehensive dependency management to ensure services start in the correct order and all dependencies are satisfied before a service becomes available.

## Dependency Architecture

### Service Dependencies
```python
SERVICE_DEPENDENCIES = {
    "ollama": [],                    # No dependencies
    "qdrant": [],                    # No dependencies  
    "redis": [],                     # No dependencies
    "hub-gateway": ["redis"],        # Depends on Redis
    "whisper": [],                   # Future: No dependencies
    "minio": [],                     # Future: No dependencies
    "parser": []                     # Future: No dependencies
}
```

### Startup Order
```python
SERVICE_STARTUP_ORDER = ["redis", "qdrant", "ollama", "hub-gateway"]
```

## Auto-Wake Sequence with Dependencies

### Scenario 1: Simple Service Request
```
App calls /v1/chat/completions → needs Ollama
Gateway checks Ollama status → stopped
Gateway starts Ollama (no dependencies) → success
Gateway waits for Ollama health check → ready
Gateway pre-loads model → success
Gateway forwards request → success
```

### Scenario 2: Complex Dependency Chain
```
App calls /v1/answer → needs Ollama + Qdrant + Redis
Gateway resolves dependencies:
  - Ollama: no dependencies
  - Qdrant: no dependencies  
  - Redis: no dependencies
Gateway starts services in order: [redis, qdrant, ollama]
Gateway waits for each service health check
Gateway pre-loads models
Gateway forwards request
```

### Scenario 3: Hub Gateway Dependency
```
Admin calls /admin/services/hub-gateway/control → start
Gateway checks hub-gateway dependencies → needs Redis
Gateway starts Redis first → success
Gateway waits for Redis health check → ready
Gateway starts hub-gateway → success
Gateway waits for hub-gateway health check → ready
```

## Implementation Details

### Core Functions

#### `ensure_service_ready_with_dependencies(service_name)`
- Checks service status
- Validates all dependencies are running
- Starts dependencies if needed
- Starts main service
- Waits for readiness

#### `start_service_with_dependencies(service_name)`
- Resolves service dependencies
- Starts dependencies in correct order
- Waits for each dependency to be ready
- Starts main service

#### `resolve_service_dependencies(required_services)`
- Takes a list of required services
- Resolves all transitive dependencies
- Returns services in startup order
- Handles circular dependency detection

#### `ensure_multiple_services_ready(required_services)`
- Handles complex scenarios with multiple services
- Resolves all dependencies
- Starts services in dependency order
- Ensures all services are ready

### API Endpoints

#### `GET /admin/services/dependencies`
Returns dependency information:
```json
{
  "dependencies": {
    "hub-gateway": ["redis"],
    "ollama": [],
    "qdrant": [],
    "redis": []
  },
  "startupOrder": ["redis", "qdrant", "ollama", "hub-gateway"],
  "containerMap": {
    "ollama": "abs-ollama",
    "qdrant": "abs-qdrant",
    "redis": "abs-redis",
    "hub-gateway": "abs-hub-gateway"
  }
}
```

#### `POST /admin/services/ensure-ready`
Ensures multiple services are ready:
```json
{
  "required_services": ["ollama", "qdrant"]
}
```

Response:
```json
{
  "status": "success",
  "message": "All required services are ready: ['ollama', 'qdrant']",
  "resolved_services": ["redis", "qdrant", "ollama"]
}
```

## Real-World Scenarios

### Contract Reviewer App
```
App needs: Ollama + Qdrant + Redis
Dependencies resolved: [redis, qdrant, ollama]
Startup sequence:
1. Start Redis → wait for ready
2. Start Qdrant → wait for ready  
3. Start Ollama → wait for ready
4. Pre-load legal-bert model
5. App ready for use
```

### RAG PDF Voice App
```
App needs: Ollama + Qdrant + Redis + Whisper
Dependencies resolved: [redis, qdrant, ollama, whisper]
Startup sequence:
1. Start Redis → wait for ready
2. Start Qdrant → wait for ready
3. Start Ollama → wait for ready
4. Start Whisper → wait for ready
5. Pre-load embedding model
6. App ready for use
```

### Admin Operations
```
Admin stops Redis → Hub Gateway detects dependency missing
Auto-restart sequence:
1. Start Redis → wait for ready
2. Restart Hub Gateway → wait for ready
3. All services operational
```

## Error Handling

### Dependency Resolution Failures
- **Circular Dependencies**: Detected and reported
- **Missing Dependencies**: Services not in registry
- **Container Not Found**: Docker container missing

### Service Startup Failures
- **Dependency Timeout**: Dependency doesn't become ready
- **Health Check Failure**: Service starts but not healthy
- **Resource Constraints**: Insufficient resources

### Graceful Degradation
- **Partial Failure**: Some services start, others fail
- **Fallback Options**: Alternative service providers
- **User Notification**: Clear error messages

## Configuration

### Settings
```json
{
  "autoWakeEnabled": true,
  "idleTimeout": 60,
  "modelKeepAlive": 2,
  "serviceRegistry": {
    "ollama": {"desired": "on", "actual": "running", "last_used": 1234567890},
    "qdrant": {"desired": "on", "actual": "running", "last_used": 1234567890},
    "redis": {"desired": "on", "actual": "running", "last_used": 1234567890}
  }
}
```

### Adding New Services
1. Add service to `CONTAINER_MAP`
2. Add dependencies to `SERVICE_DEPENDENCIES`
3. Add to `SERVICE_STARTUP_ORDER` if needed
4. Add health check logic to `wait_for_service_ready`

## Benefits

✅ **Reliable Startup**: Services always start in correct order  
✅ **Dependency Safety**: No service starts without dependencies  
✅ **Complex Scenarios**: Handles multiple interdependent services  
✅ **Error Recovery**: Graceful handling of startup failures  
✅ **Monitoring**: Full visibility into dependency resolution  
✅ **Extensibility**: Easy to add new services and dependencies  

## Future Enhancements

### Planned Features
1. **Dynamic Dependencies**: Runtime dependency discovery
2. **Health Monitoring**: Continuous dependency health checks
3. **Load Balancing**: Multiple instances of services
4. **Service Mesh**: Advanced service communication

### Extension Points
1. **Custom Health Checks**: Service-specific readiness tests
2. **Dependency Injection**: Runtime dependency configuration
3. **Service Discovery**: Automatic service detection
4. **Circuit Breakers**: Fault tolerance patterns
