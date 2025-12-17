# Optional Idle Sleep Feature

## Overview

The **Optional Idle Sleep** feature automatically stops or unloads services and models that haven't been used for a configurable period to save system resources. This is particularly useful for GPU memory management and reducing power consumption.

## Architecture

### Background Monitoring
- **Idle Monitor Task**: Background asyncio task that runs continuously
- **Configurable Intervals**: Checks for idle services every N minutes
- **Service-Specific Control**: Each service can have idle sleep enabled/disabled individually
- **Model Tracking**: Monitors model usage and keep-alive timers

### Resource Management
- **Service Containers**: Automatically stops idle Docker containers
- **Model Memory**: Unloads models from VRAM when keep-alive expires
- **Selective Control**: Redis stays running (critical service), others can sleep

## Configuration

### Global Settings
```python
AUTO_WAKE_SETTINGS = {
    "idle_sleep_enabled": True,           # Master switch for idle sleep
    "idle_timeout_minutes": 60,           # Stop services after N minutes idle
    "model_keep_alive_hours": 2,          # Keep models loaded for N hours
    "idle_check_interval_minutes": 5      # Check for idle every N minutes
}
```

### Service-Specific Settings
```python
SERVICE_REGISTRY = {
    "ollama": {
        "idle_sleep_enabled": True,       # Can be stopped when idle
        "desired": "off",                 # Only stops if desired=off
        "last_used": timestamp,           # Last usage timestamp
        "actual": "running"               # Current status
    },
    "qdrant": {
        "idle_sleep_enabled": True,       # Can be stopped when idle
        "desired": "off",
        "last_used": timestamp,
        "actual": "running"
    },
    "redis": {
        "idle_sleep_enabled": False,      # Always stays running
        "desired": "on",
        "last_used": timestamp,
        "actual": "running"
    }
}
```

### Model Tracking
```python
MODEL_REGISTRY = {
    "llama3.2:3b": {
        "last_used": timestamp,           # Last model usage
        "keep_alive_until": timestamp,    # When model will be unloaded
        "provider": "ollama"              # Model provider
    }
}
```

## Idle Sleep Logic

### Service Idle Sleep
```
Background Task (every 5 minutes):
1. Check each service in SERVICE_REGISTRY
2. Skip if idle_sleep_enabled = False
3. Skip if desired = "on" (user wants it running)
4. Calculate idle time = current_time - last_used
5. If idle_time > idle_timeout_minutes:
   - Stop the service container
   - Update actual status to "stopped"
   - Log the action
```

### Model Idle Sleep
```
Background Task (every 5 minutes):
1. Check each model in MODEL_REGISTRY
2. Calculate time_until_unload = keep_alive_until - current_time
3. If time_until_unload <= 0:
   - Send unload request to Ollama
   - Update keep_alive_until to 0
   - Log the action
```

## Real-World Scenarios

### Scenario 1: Whisper Server Idle Sleep
```
Initial State: Whisper server running, last used 2 hours ago
Background Check: idle_time = 120 minutes > idle_timeout (60 minutes)
Action: Stop whisper container
Result: GPU memory freed, power consumption reduced
Next Request: Auto-wake starts whisper when needed
```

### Scenario 2: Model Keep-Alive Expiration
```
Initial State: llama3.2:3b loaded, keep_alive_until = 2 hours from now
Background Check: current_time > keep_alive_until
Action: Send unload request to Ollama
Result: 3GB VRAM freed
Next Request: Model auto-loads when needed (cold start)
```

### Scenario 3: Selective Service Sleep
```
Configuration:
- Redis: idle_sleep_enabled = False (always running)
- Ollama: idle_sleep_enabled = True (can sleep)
- Qdrant: idle_sleep_enabled = True (can sleep)

After 1 hour idle:
- Redis: Still running (critical service)
- Ollama: Stopped (saves GPU memory)
- Qdrant: Stopped (saves RAM)
```

## API Endpoints

### Get Idle Status
```http
GET /admin/idle-status
```

Response:
```json
{
  "idle_sleep_enabled": true,
  "idle_timeout_minutes": 60,
  "model_keep_alive_hours": 2,
  "services": {
    "ollama": {
      "last_used": 1234567890,
      "idle_for_minutes": 45,
      "idle_sleep_enabled": true,
      "desired": "off",
      "actual": "running",
      "will_sleep_in_minutes": 15
    }
  },
  "models": {
    "llama3.2:3b": {
      "last_used": 1234567890,
      "keep_alive_until": 1234571490,
      "will_unload_in_minutes": 60,
      "provider": "ollama"
    }
  },
  "monitor_task_running": true
}
```

### Toggle Service Idle Sleep
```http
POST /admin/services/{service_name}/idle-sleep
Content-Type: application/json

{
  "enabled": false
}
```

### Force Unload Model
```http
POST /admin/models/{model_name}/unload
```

### Update Global Settings
```http
POST /admin/settings
Content-Type: application/json

{
  "idleSleepEnabled": true,
  "idleTimeout": 30,
  "modelKeepAlive": 1,
  "idleCheckInterval": 3
}
```

## Implementation Details

### Background Task Management
```python
async def idle_monitor_task():
    """Background task to monitor and handle idle services and models"""
    while True:
        try:
            await check_and_handle_idle_services()
            await check_and_handle_idle_models()
            
            sleep_seconds = AUTO_WAKE_SETTINGS["idle_check_interval_minutes"] * 60
            await asyncio.sleep(sleep_seconds)
        except Exception as e:
            print(f"Error in idle monitor task: {e}")
            await asyncio.sleep(60)  # Sleep for 1 minute on error
```

### Service Lifecycle Integration
```python
@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup"""
    if AUTO_WAKE_SETTINGS["idle_sleep_enabled"]:
        await start_idle_monitor()
        print("ABS Hub Gateway started with idle sleep monitoring enabled")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks on application shutdown"""
    await stop_idle_monitor()
    print("ABS Hub Gateway shutdown - idle monitor stopped")
```

### Model Usage Tracking
```python
async def preload_model_if_needed(model_name: str, provider: str) -> bool:
    """Pre-load a model into VRAM if using Ollama"""
    # ... load model logic ...
    
    if r.is_success:
        # Track model usage and keep-alive
        current_time = time.time()
        keep_alive_until = current_time + (AUTO_WAKE_SETTINGS['model_keep_alive_hours'] * 3600)
        
        MODEL_REGISTRY[model_name] = {
            "last_used": current_time,
            "keep_alive_until": keep_alive_until,
            "provider": provider
        }
        print(f"Model {model_name} loaded and tracked for keep-alive until {keep_alive_until}")
```

## Benefits

### Resource Optimization
✅ **GPU Memory**: Automatically frees VRAM when models are idle  
✅ **System RAM**: Stops unused service containers  
✅ **Power Consumption**: Reduces CPU/GPU usage during idle periods  
✅ **Storage I/O**: Reduces disk activity from stopped services  

### User Experience
✅ **Seamless Operation**: Services auto-start when needed  
✅ **Transparent**: Users don't notice idle sleep (auto-wake handles it)  
✅ **Configurable**: Granular control over which services can sleep  
✅ **Monitoring**: Full visibility into idle status and timing  

### System Stability
✅ **Graceful Shutdown**: Services stop cleanly when idle  
✅ **Error Recovery**: Background task handles errors gracefully  
✅ **Resource Limits**: Prevents resource exhaustion  
✅ **Selective Control**: Critical services (Redis) stay running  

## Configuration Examples

### Conservative (Always On)
```json
{
  "idle_sleep_enabled": false,
  "idle_timeout_minutes": 120,
  "model_keep_alive_hours": 4
}
```

### Balanced (Default)
```json
{
  "idle_sleep_enabled": true,
  "idle_timeout_minutes": 60,
  "model_keep_alive_hours": 2,
  "idle_check_interval_minutes": 5
}
```

### Aggressive (Maximum Savings)
```json
{
  "idle_sleep_enabled": true,
  "idle_timeout_minutes": 15,
  "model_keep_alive_hours": 0.5,
  "idle_check_interval_minutes": 2
}
```

### Service-Specific Configuration
```json
{
  "services": {
    "ollama": {"idle_sleep_enabled": true},      // Can sleep
    "qdrant": {"idle_sleep_enabled": true},      // Can sleep  
    "redis": {"idle_sleep_enabled": false},      // Always running
    "whisper": {"idle_sleep_enabled": true}      // Can sleep
  }
}
```

## Monitoring and Troubleshooting

### Log Messages
```
Service ollama has been idle for 60 minutes, stopping...
Successfully stopped idle service ollama
Model llama3.2:3b keep-alive expired, unloading...
Successfully unloaded idle model llama3.2:3b
Idle monitor task started
```

### Common Issues
1. **Service Won't Sleep**: Check `desired` status and `idle_sleep_enabled`
2. **Model Won't Unload**: Verify Ollama is responding to unload requests
3. **Background Task Stopped**: Check for errors in idle monitor task
4. **Resource Not Freed**: Verify Docker containers are actually stopped

### Debugging Commands
```bash
# Check idle status
curl http://localhost:8081/admin/idle-status

# Force unload a model
curl -X POST http://localhost:8081/admin/models/llama3.2:3b/unload

# Disable idle sleep for a service
curl -X POST http://localhost:8081/admin/services/ollama/idle-sleep \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

## Future Enhancements

### Planned Features
1. **Predictive Sleep**: ML-based prediction of service usage patterns
2. **Resource Monitoring**: CPU/GPU usage-based sleep decisions
3. **User Activity Detection**: Sleep based on user presence
4. **Scheduled Sleep**: Time-based sleep schedules

### Advanced Scenarios
1. **Load Balancing**: Sleep instances based on load
2. **Cost Optimization**: Cloud resource cost-based sleep
3. **Energy Management**: Power consumption optimization
4. **Performance Tuning**: Dynamic timeout adjustment

---

## Summary

The Optional Idle Sleep feature provides intelligent resource management by automatically stopping idle services and unloading unused models. It integrates seamlessly with the auto-wake mechanism to ensure services are available when needed while optimizing resource usage during idle periods.

Key benefits include reduced GPU memory usage, lower power consumption, and improved system efficiency, all while maintaining a seamless user experience through automatic service management.
