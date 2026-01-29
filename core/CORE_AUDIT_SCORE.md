# Core Folder Audit Score

**Date:** 2025-01-28  
**Scope:** `core/` (scripts, gateway, docker-compose, config)

---

## Summary

| Category            | Score | Notes |
|---------------------|-------|--------|
| Hardcoded paths     | ⚠️ Fix | 4 files with absolute or machine-specific paths |
| Missing / wrong refs| ⚠️ Fix | Wrong compose filename in setup scripts |
| Env / config        | ✅    | `.env.example` present; gateway uses env where needed |
| Script portability  | ⚠️    | `start-core.ps1` / `stop-core.ps1` use `$PSScriptRoot` (good); `update-core.ps1` does not |

---

## 1. Hardcoded File Paths

### 1.1 `core/update-core.ps1`
- **Line 1:** `cd C:\ABS\core` — absolute Windows path; fails on other machines/layouts.
- **Fix:** Use `$PSScriptRoot` and `Set-Location $PSScriptRoot` (same pattern as `start-core.ps1` / `stop-core.ps1`).

### 1.2 `core/gateway/setup-postgresql.bat`
- **Line 16:** `C:\abs-shared-data\postgres` — hardcoded Windows data dir; script never uses it (compose uses named volume `postgres_data`).
- **Line 25:** `core.yml` — file does not exist; compose file is `docker-compose.yml` in parent `core/`.
- **Fix:** Use `docker-compose.yml` and `%~dp0\..` to run from `core/`; drop or make configurable the `C:\abs-shared-data\postgres` mkdir if not used.

### 1.3 `core/gateway/setup-postgresql.sh`
- **Line 18:** `/abs-shared-data/postgres` — hardcoded Linux path; same as bat, not used by current compose.
- **Line 27:** `core.yml` — should be `docker-compose.yml` (script `cd`s to `core/` via `$(dirname "$0")/..`).

### 1.4 `core/gateway/services/asset_manager.py`
- **Lines 366, 394:** `"C:/ABS/core/bindings.yaml"` and `"C:/ABS/assets/registry/assets.json"` — dev fallbacks; break on any other clone path or OS.
- **Fix:** Remove these or use env (e.g. `ASSETS_ROOT` / `BINDINGS_PATH`); rely on `REGISTRY_PATH` / `BINDINGS_PATH` and relative paths from `__file__` or cwd.

---

## 2. Wrong / Missing References

- **Compose file name:** `setup-postgresql.bat` and `setup-postgresql.sh` use `core.yml`. The actual file is `core/docker-compose.yml`. They should use `docker-compose.yml` when run from `core/`.
- **Network name:** Setup scripts create `abs-network`; `docker-compose.yml` uses `${ABS_NETWORK}` (default in `.env.example`: `abs-net`). Inconsistent; either use same name in scripts or document that setup scripts are legacy.

---

## 3. Intentional / OK Paths

- **docker-compose.yml:** `./gateway`, `../assets`, `../abs-ai-hub/...` — relative to compose file; correct.
- **Container paths:** `/app/...`, `/var/run/docker.sock`, `/var/lib/postgresql/data` — standard container layout; no change needed.
- **gateway config.py:** Uses `os.getenv(...)` with sensible defaults; `APPS_REGISTRY_PATH` relative to repo layout is acceptable.
- **store_service.py:** `/app/` paths for container, `base_path` from `__file__` for local; appropriate.
- **docker_service.py:** `unix:///var/run/docker.sock` — standard Docker socket; OK.
- **start-core.ps1 / stop-core.ps1:** Use `$PSScriptRoot` and `Join-Path`; portable.

---

## 4. Possibly Missing (Optional)

- **core/documents/:** Newegg base rule asks for a `documents/` in projects; repo has root `docs/`. Adding `core/documents/` for core-specific design/ops is optional.
- **gateway/.env.example:** Empty; could list any env vars the gateway reads (e.g. `GATEWAY_PORT`, `REDIS_URL`, `REGISTRY_PATH`, `BINDINGS_PATH`) for local runs.

---

## 5. Recommended Fixes (Priority)

1. **update-core.ps1:** Replace `cd C:\ABS\core` with `$CoreDir = $PSScriptRoot; Set-Location $CoreDir`.
2. **setup-postgresql.bat / setup-postgresql.sh:** Use `docker-compose.yml` instead of `core.yml`; make data dir optional or env-based if kept.
3. **asset_manager.py:** Remove `C:/ABS/...` fallbacks or replace with env-based paths only.

---

## 6. Applied Fixes (2025-01-28)

- **update-core.ps1:** Uses `$PSScriptRoot` and `Set-Location $CoreDir`.
- **setup-postgresql.bat / setup-postgresql.sh:** Use `docker-compose.yml`; network set to `abs-net` to match `.env.example`; removed unused shared data dir creation.
- **asset_manager.py:** Removed `C:/ABS/...` dev fallbacks; bindings and registry use env and relative paths only.
