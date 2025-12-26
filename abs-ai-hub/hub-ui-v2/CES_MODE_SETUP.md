# CES Mode Setup Guide for Hub UI v2

## Overview

CES (Consumer Electronics Show) mode enables a **read-only admin interface** for demo purposes. When enabled, dangerous operations (delete, stop services, modify policies) are disabled while keeping safe operations (view, refresh, inspect) enabled.

## Quick Start

### Option 1: Development Mode (Runtime)

Create a `.env` file in the `hub-ui-v2` directory:

```bash
# .env
VITE_CES_MODE=true
```

Then start the dev server:
```bash
npm run dev
```

**Note**: Changes to `.env` require restarting the dev server.

### Option 2: Production Build (Build-Time)

Set the environment variable before building:

```bash
# Windows (PowerShell)
$env:CES_MODE="true"; npm run build

# Windows (CMD)
set CES_MODE=true && npm run build

# Linux/Mac
CES_MODE=true npm run build
```

Or create a `.env.production` file:
```bash
# .env.production
CES_MODE=true
```

Then build:
```bash
npm run build
```

## Verification

### Check if CES Mode is Active

1. **Visual Indicator**: A banner appears at the top of the Admin page:
   ```
   🔒 CES Demo Mode Active
   Admin operations are read-only. Viewing and monitoring enabled; 
   destructive actions disabled for demo safety.
   ```

2. **Console Log**: In development mode, check the browser console:
   ```
   [CESMode] Initialized: { isCESMode: true, buildTimeFlag: true }
   ```

3. **Disabled Operations**: The following buttons/actions will be disabled:
   - ⏹ Stop Service
   - ▶ Start Service  
   - 🔄 Restart Service
   - ⏸️ Suspend Service
   - 🗑️ Delete Model
   - 🗑️ Clear Cache
   - 📥 Restore Snapshot
   - Policy checkboxes and inputs

## Environment Variables

| Variable | Purpose | When Used |
|----------|---------|-----------|
| `VITE_CES_MODE` | Development runtime | `npm run dev` |
| `CES_MODE` | Production build-time | `npm run build` |

Both accept: `true`, `1`, `false`, `0`, or unset (defaults to `false`)

## Files Modified

When CES mode is enabled, the following components are affected:

- **AdminView.vue**: All dangerous operations are disabled
- **CESModeBanner.vue**: Displays the banner
- **useCESRestrictions.ts**: Provides restriction logic
- **useCESMode.ts**: Detects CES mode status

## Disabling CES Mode

### Development
Remove or set to `false` in `.env`:
```bash
VITE_CES_MODE=false
```
Restart the dev server.

### Production
Rebuild without the environment variable:
```bash
npm run build
```

## Troubleshooting

### CES Mode Not Activating

1. **Check environment variable**:
   ```bash
   # Windows PowerShell
   echo $env:VITE_CES_MODE
   
   # Linux/Mac
   echo $VITE_CES_MODE
   ```

2. **Verify .env file location**: Must be in `hub-ui-v2/` directory (same level as `package.json`)

3. **Restart dev server**: Environment variable changes require a restart

4. **Check console logs**: Look for `[CESMode] Initialized` message in browser console

### Build-Time vs Runtime

- **Build-time** (`CES_MODE`): Value is baked into the build, cannot be changed without rebuilding
- **Runtime** (`VITE_CES_MODE`): Can be changed via `.env` file, requires dev server restart

For production deployments, use build-time (`CES_MODE`) to ensure the mode cannot be accidentally changed.

## Example Workflow

```bash
# 1. Enable CES mode for development
cd hub-ui-v2
echo "VITE_CES_MODE=true" > .env

# 2. Start dev server
npm run dev

# 3. Verify in browser
# - Open Admin page
# - Check for CES banner
# - Try clicking "Stop Service" - should be disabled

# 4. Build for production with CES mode
CES_MODE=true npm run build

# 5. Serve production build
npm run preview
```

## Security Note

CES mode is a **client-side restriction**. For true security, also implement server-side restrictions in the Gateway API to prevent unauthorized operations even if CES mode is bypassed.

