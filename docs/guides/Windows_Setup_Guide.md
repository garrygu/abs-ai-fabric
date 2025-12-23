# ABS AI Hub - Windows Setup Guide

This guide provides step-by-step instructions for setting up ABS AI Hub on Windows 10 Pro or later, including Docker Desktop configuration and GPU passthrough for NVIDIA GPUs.

---

## Prerequisites

- **Windows 10 Pro** or later (Windows 11 recommended)
- **NVIDIA GPU** with CUDA support
- **Administrator access** for PowerShell scripts
- **Docker Desktop for Windows** (latest version recommended)

---

## 1. Install Docker Desktop

### 1.1 Download and Install

1. Download Docker Desktop from: https://www.docker.com/products/docker-desktop/
2. Run the installer and follow the setup wizard
3. **Important**: During installation, ensure "Use WSL 2 instead of Hyper-V" is selected (this is the default on Windows 10 version 2004+)

### 1.2 Verify Installation

After installation, Docker Desktop should start automatically. Verify it's running:

```powershell
docker --version
docker compose version
```

---

## 2. Configure Docker Desktop for GPU Support

### 2.1 Enable WSL 2 Engine (CRITICAL)

**On Windows, Docker Desktop uses WSL2 (Windows Subsystem for Linux) as the backend for GPU passthrough. The standalone NVIDIA Container Toolkit is NOT manually installed on Windows like it is on Linux.**

1. **Open Docker Desktop Settings**
   - Click the Docker Desktop icon in the system tray
   - Select **Settings** (gear icon)

2. **Verify WSL 2 Engine is Active**
   - Go to **General** tab
   - Ensure **"Use the WSL 2 based engine"** is **checked** ✅
   - If not checked, check it and click **"Apply & Restart"**

3. **Enable WSL Integration**
   - Go to **Resources** → **WSL Integration**
   - Ensure your default WSL distro (usually **Ubuntu**) is **enabled** ✅
   - If you don't have a WSL distro installed, Docker Desktop will prompt you to install one
   - Click **"Apply & Restart"** if you made changes

### 2.2 Verify GPU Access

After configuring Docker Desktop, verify that containers can access the GPU:

```powershell
# Test GPU access in a container
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

**Expected Output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 5XX.XX       Driver Version: XXX.XXX       CUDA Version: 12.0  |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA RTX ...   Off  | 00000000:XX:XX.0  On |                  N/A |
|  XX%    XX°C    P0    XXXW / XXXW |   XXXMiB / XXXXXMiB |     XX%      Default |
+-------------------------------+----------------------+----------------------+
```

**If you see an error** like "could not select device driver" or "nvidia-smi: command not found":
- Ensure WSL 2 engine is enabled (Step 2.1)
- Ensure WSL Integration is enabled for your distro (Step 2.1)
- Update your NVIDIA drivers to the latest version
- Restart Docker Desktop
- Restart your computer if the issue persists

---

## 3. Install WSL 2 (If Not Already Installed)

If Docker Desktop prompts you to install WSL 2:

### Option A: Automatic Installation (Recommended)

1. Docker Desktop will provide a link to install WSL 2
2. Follow the installation wizard
3. Restart your computer when prompted

### Option B: Manual Installation

```powershell
# Run PowerShell as Administrator
wsl --install

# Restart your computer
# After restart, WSL 2 will be configured automatically
```

### Verify WSL 2 Installation

```powershell
wsl --list --verbose
```

You should see your distro (usually Ubuntu) with version **2**.

---

## 4. Update NVIDIA Drivers

Ensure you have the latest NVIDIA drivers installed:

1. Visit: https://www.nvidia.com/Download/index.aspx
2. Select your GPU model and download the latest driver
3. Install the driver and restart your computer
4. Verify driver installation:

```powershell
# Check NVIDIA driver version
nvidia-smi
```

---

## 5. Configure Docker Compose for GPU

ABS AI Hub services that require GPU access use the `runtime: nvidia` configuration in `docker-compose.yml`. This is already configured in the Core services.

Example from `core/docker-compose.yml`:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    runtime: nvidia  # This enables GPU access
    environment:
      TZ: ${TZ}
      OLLAMA_KEEP_ALIVE: "24h"
    # ... rest of configuration
```

**Note**: On Windows with Docker Desktop + WSL2, the `runtime: nvidia` directive works automatically once WSL 2 engine is enabled. No additional configuration is needed.

---

## 6. Troubleshooting GPU Access

### Issue: Container cannot see GPU

**Symptoms:**
- `nvidia-smi` fails inside container
- GPU utilization shows 0% in monitoring tools
- Models fail to load or run very slowly

**Solutions:**

1. **Verify Docker Desktop WSL 2 Configuration**
   - Open Docker Desktop → Settings → General
   - Ensure "Use the WSL 2 based engine" is checked
   - Go to Resources → WSL Integration
   - Ensure your WSL distro is enabled
   - Click "Apply & Restart"

2. **Check NVIDIA Driver Version**
   ```powershell
   nvidia-smi
   ```
   - Ensure driver version is 470.63.01 or later
   - Update drivers if needed

3. **Verify WSL 2 is Running**
   ```powershell
   wsl --list --verbose
   ```
   - Ensure your distro shows version **2** (not 1)

4. **Restart Docker Desktop**
   - Right-click Docker Desktop icon → Quit Docker Desktop
   - Restart Docker Desktop
   - Wait for it to fully start

5. **Restart Computer**
   - Sometimes a full restart is needed after driver updates

6. **Test GPU Access Again**
   ```powershell
   docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
   ```

### Issue: "WSL 2 installation is incomplete"

**Solution:**
1. Download the WSL 2 Linux kernel update package:
   https://aka.ms/wsl2kernel
2. Install the update package
3. Restart your computer
4. Verify: `wsl --set-default-version 2`

### Issue: Docker Desktop won't start

**Solutions:**
1. Ensure Windows features are enabled:
   ```powershell
   # Run as Administrator
   Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
   Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
   ```
2. Restart your computer
3. Try starting Docker Desktop again

---

## 7. Verify ABS AI Hub Setup

After completing the above steps, verify your ABS AI Hub installation:

```powershell
# Navigate to core directory
cd C:\ABS\core

# Start Core services
.\start-core.ps1

# Check if Ollama can see the GPU
docker exec abs-ollama nvidia-smi

# Verify services are running
docker compose ps
```

---

## 8. Additional Resources

- **Docker Desktop Documentation**: https://docs.docker.com/desktop/windows/
- **WSL 2 Documentation**: https://docs.microsoft.com/en-us/windows/wsl/
- **NVIDIA Container Toolkit** (Linux reference): https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/
  - *Note: On Windows, Docker Desktop handles this automatically through WSL2*

---

## Summary Checklist

- [ ] Docker Desktop installed
- [ ] WSL 2 engine enabled in Docker Desktop Settings → General
- [ ] WSL Integration enabled for default distro (Settings → Resources → WSL Integration)
- [ ] NVIDIA drivers updated to latest version
- [ ] GPU access verified with `docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi`
- [ ] Core services start successfully
- [ ] Ollama container can access GPU

---

**Important Notes:**

1. **NVIDIA Container Toolkit is NOT manually installed on Windows** - Docker Desktop handles GPU passthrough automatically through WSL2
2. **WSL 2 is required** - The older Hyper-V backend does not support GPU passthrough
3. **Always use `runtime: nvidia`** in docker-compose.yml for services that need GPU access
4. **Restart Docker Desktop** after making configuration changes
5. **Update NVIDIA drivers regularly** for best compatibility

---

✅ Once all steps are complete, your ABS AI Hub should have full GPU access for AI model inference, vector operations, and other GPU-accelerated workloads.

