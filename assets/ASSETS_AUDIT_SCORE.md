# Assets Folder Scan

**Date:** 2025-01-28  
**Scope:** `assets/` (registry, apps, core, models, tools, datasets)

---

## Summary

| Category              | Status | Notes |
|-----------------------|--------|--------|
| Structure & registry  | OK     | 25 asset.yaml files; paths in assets.json match folders |
| Hardcoded file paths  | OK     | No filesystem paths (no C:\, /home) |
| Schema consistency    | Minor  | ownership.provider uses "platform" / "abs" vs schema system|admin|user |
| Missing references    | Minor  | mxbai-embed-large referenced in app policy but no asset/alias |
| Endpoint consistency  | Minor  | whisper-server uses localhost instead of service name |

---

## 1. Structure

```
assets/
├── apps/          7 assets  (abs-workstation-console, contract-reviewer-v2, …)
├── core/          4 assets  (ollama, postgresql, whisper-server, qdrant)
├── datasets/     2 assets  (contracts-corpus, ndas-sample)
├── models/       8 assets  (4 LLM + 4 embeddings)
├── tools/        4 assets  (bge-reranker, ocr-service, pdf-parser, text-chunker)
└── registry/
    ├── aliases.yaml   (model name → provider IDs)
    └── assets.json   (index: id, interface, path per section)
```

- **assets.json** paths use forward slashes and match directory layout; all 25 referenced `asset.yaml` files exist.
- **asset_id** in each YAML matches the id used in assets.json (directory names may differ, e.g. `llama3_8b` vs `llama3:8b`).

---

## 2. Hardcoded Paths

- **None.** No absolute filesystem paths (no `C:\`, `/home`, or repo-specific paths) in any `asset.yaml` or registry file.
- **URLs in assets:** `metadata.url` and `endpoints.api_base` / `health` use either:
  - **Service names** (e.g. `http://ollama:11434`, `http://qdrant:6333`, `http://parser:9100`) — correct for Docker.
  - **localhost** (e.g. `http://localhost:8082`, `http://localhost:5200`) — app UI defaults; acceptable.

---

## 3. Schema Consistency (standard_asset_schema_v1.0)

- **ownership.provider:** Spec allows `system | admin | user`. In assets:
  - **platform** — used in 4 embedding models (all-minilm, bge-small, legal-bert, nomic-embed).
  - **abs** — used in abs-workstation-console.
  - Consider extending the schema to allow `platform` and `abs`, or map them to `system`/`admin` for validation.
- Other required fields (asset_id, interface, class, ownership.visibility, etc.) are present and consistent.

---

## 4. Missing or Orphan References

| Item | Where | Issue |
|------|--------|--------|
| **mxbai-embed-large** | apps/contract-reviewer-v2/asset.yaml `policy.allowed_embeddings` | Referenced but no asset in models/ and no alias in aliases.yaml. Either add asset/alias or remove from allowed list. |
| **llama3:70b** | assets.json, models/llama3_70b/asset.yaml | In registry and asset; not in aliases.yaml — add to aliases if runtime resolves by alias. |
| **deepseek-r1:70b** | Same | In registry and asset; not in aliases.yaml — add if needed for resolution. |

---

## 5. Endpoint Consistency

- **whisper-server** (`core/speech/whisper-server/asset.yaml`): `api_base` and `health` use `http://localhost:8001`. Other core services use Docker service names (e.g. `http://ollama:11434`, `http://qdrant:6333`). For consistency in composed stacks, consider `http://whisper-server:8001` (or the actual service name in docker-compose) when run in Docker; keep localhost only for host-only usage.

---

## 6. Registry vs Aliases

- **aliases.yaml** covers: llama3.2:3b, llama3.2:latest, bge-small-en-v1.5, all-minilm, legal-bert, llama4:scout, llama3:8b.
- **Not in aliases:** llama3:70b, deepseek-r1:70b. Add if the gateway or runtimes resolve model names via aliases.
- **bge-small** asset has `policy.served_models: ["bge-m3:latest"]` (ollama tag); alias uses `bge-small-en-v1.5` / ollama `bge-small`. Confirm intended mapping (alias vs ollama tag) for resolution.

---

## 7. Optional Improvements

- **assets/README.md** — Short description of folder layout, role of registry/assets.json and aliases.yaml, and how gateway uses them.
- **Schema / validation** — Optional CI check: validate each asset.yaml against standard_asset_schema_v1.0 and ensure every id in assets.json has a matching file and asset_id in YAML.

---

## 8. Checklist (Quick Verify)

- [x] Every path in assets.json points to an existing asset.yaml.
- [x] Every asset.yaml has asset_id, interface, class, ownership.
- [ ] ownership.provider limited to system|admin|user or schema updated.
- [ ] mxbai-embed-large: add asset/alias or remove from contract-reviewer-v2.
- [ ] whisper-server: consider service-name URL when run in Docker.
- [ ] aliases.yaml: add llama3:70b, deepseek-r1:70b if resolution uses aliases.
