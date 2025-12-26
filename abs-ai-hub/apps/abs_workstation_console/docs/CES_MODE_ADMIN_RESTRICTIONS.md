# CES Mode Admin Restrictions - Best Practices

## Overview

In CES (Consumer Electronics Show) demo mode, Admin pages should be **visible but read-only**. This allows showcasing the full admin interface while preventing accidental or malicious destructive operations.

## Implementation Pattern

### 1. Use CES Restrictions Composable

```typescript
import { useCESRestrictions } from '@/composables/useCESRestrictions'

const { 
  isCESMode, 
  isOperationAllowed, 
  getOperationRestriction,
  cesBannerMessage,
  canEdit,
  canDelete,
  canControlServices 
} = useCESRestrictions()
```

### 2. Display CES Mode Banner

Always show a banner at the top of admin pages when CES mode is active:

```vue
<CESModeBanner />
```

### 3. Disable Dangerous Operations

#### Pattern A: Conditional Disabling

```vue
<button 
  @click="deleteModel(model)"
  :disabled="!canDelete || loading"
  :title="!canDelete ? 'Disabled in CES demo mode' : 'Delete model'"
>
  🗑️ Delete
</button>
```

#### Pattern B: Using Operation Restrictions

```vue
<script setup>
const restriction = getOperationRestriction('delete-model')
</script>

<template>
  <button 
    @click="deleteModel(model)"
    :disabled="restriction.disabled || loading"
    :title="restriction.tooltip || 'Delete model'"
  >
    🗑️ Delete
  </button>
</template>
```

#### Pattern C: Conditional Rendering (Less Preferred)

```vue
<!-- Only show if allowed -->
<button 
  v-if="canDelete"
  @click="deleteModel(model)"
>
  🗑️ Delete
</button>
```

**Recommendation**: Use Pattern A or B (disable + tooltip) rather than hiding buttons, as it:
- Shows the full interface
- Makes it clear what's disabled
- Provides better UX than hidden features

### 4. Visual Indicators

#### Disabled Button Styling

```css
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  position: relative;
}

button:disabled::after {
  content: '🔒';
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 0.7rem;
}
```

#### CES Mode Badge

Add a small badge to disabled operations:

```vue
<button :disabled="!canDelete">
  🗑️ Delete
  <span v-if="!canDelete" class="ces-badge">CES</span>
</button>
```

## Dangerous Operations List

The following operations should be disabled in CES mode:

### Service Lifecycle
- ✅ **Start Service** - Can disrupt demo
- ✅ **Stop Service** - Can break functionality
- ✅ **Restart Service** - Can interrupt demo
- ✅ **Suspend Service** - Can break functionality

### Model Operations
- ✅ **Delete Model** - Destructive, irreversible
- ✅ **Unload Model** - Can break running demos

### Asset Operations
- ✅ **Delete Asset** - Destructive
- ✅ **Edit Asset** - Can modify demo configuration
- ✅ **Update Policy** - Can change demo behavior

### System Operations
- ✅ **Clear Cache** - Can affect demo state
- ✅ **Restore Snapshot** - Can reset demo
- ✅ **Export/Import Config** - Can modify system

### Configuration
- ✅ **Save Config** - Can persist changes
- ✅ **Reset Config** - Can break demo

## Safe Operations (Always Allowed)

These operations are safe and should remain enabled:

- ✅ **View/Inspect** - Read-only viewing
- ✅ **Refresh** - Reload data
- ✅ **Health Check** - Diagnostic only
- ✅ **View Metrics** - Monitoring only
- ✅ **View Logs** - Read-only
- ✅ **View Dependencies** - Read-only

## Example Implementation

```vue
<template>
  <div class="admin-page">
    <!-- CES Mode Banner -->
    <CESModeBanner />
    
    <!-- Service Controls -->
    <section>
      <h2>Service Controls</h2>
      
      <div v-for="service in services" :key="service.name">
        <button 
          @click="startService(service)"
          :disabled="!canControlServices || service.running"
          :title="!canControlServices ? 'Disabled in CES demo mode' : 'Start service'"
        >
          ▶ Start
        </button>
        
        <button 
          @click="stopService(service)"
          :disabled="!canControlServices || !service.running"
          :title="!canControlServices ? 'Disabled in CES demo mode' : 'Stop service'"
        >
          ⏹ Stop
        </button>
        
        <!-- View-only actions always enabled -->
        <button @click="viewLogs(service)">
          📋 View Logs
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useCESRestrictions } from '@/composables/useCESRestrictions'
import CESModeBanner from '@/components/CESModeBanner.vue'

const { canControlServices } = useCESRestrictions()

function startService(service: any) {
  if (!canControlServices.value) {
    return // Early return if disabled
  }
  // ... start logic
}
</script>
```

## Best Practices Summary

1. ✅ **Show, Don't Hide**: Display all admin features but disable dangerous ones
2. ✅ **Clear Messaging**: Use tooltips and banners to explain why operations are disabled
3. ✅ **Visual Feedback**: Use disabled styling + lock icons to indicate restrictions
4. ✅ **Consistent Pattern**: Use the composable everywhere for consistency
5. ✅ **Safe Operations**: Keep read-only operations (view, refresh, inspect) enabled
6. ✅ **Early Returns**: Check restrictions in function bodies as defense-in-depth

## Testing Checklist

- [ ] CES banner appears when CES mode is active
- [ ] Dangerous operations are disabled (not hidden)
- [ ] Tooltips explain why operations are disabled
- [ ] Safe operations (view, refresh) still work
- [ ] Visual indicators (disabled styling) are clear
- [ ] No console errors when clicking disabled buttons

