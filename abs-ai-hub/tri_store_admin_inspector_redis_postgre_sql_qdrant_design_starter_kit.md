# Tri‑Store Admin Inspector (Redis + PostgreSQL + Qdrant)

A lightweight admin tool to **query, compare, and diagnose** a document across Redis, PostgreSQL, and Qdrant by **doc_id**.

---

## 1) Goals & Non‑Goals

**Goals**
- Given a `doc_id`, fetch its records from **Redis**, **PostgreSQL**, and **Qdrant** in one call.
- Normalize the payloads into a common schema and **compute a diff** (fields, timestamps, checksums).
- Flag **missing/inconsistent** entries, TTL risks, and schema/version drift.
- Provide **safe utilities** (copy to clipboard, CSV/JSON export) and **optional soft‑repair** actions (disabled by default).

**Non‑Goals (v1)**
- Full CRUD admin for underlying stores.
- Arbitrary SQL/Vector search console (can be added later).

---

## 2) Canonical Data Model (Admin View)

```ts
// What the UI/API returns for a single doc_id
interface TriStoreSnapshot {
  doc_id: string;
  requested_at: string;               // ISO time
  env: 'dev' | 'staging' | 'prod';

  postgres?: {
    found: boolean;
    table: string;                     // e.g., public.documents
    pk: string;                        // e.g., id
    row?: Record<string, any>;
    updated_at?: string;               // from row
    checksum?: string;                 // sha256 of stable subset
  };

  redis?: {
    found: boolean;
    key: string;                       // e.g., doc:{doc_id}
    type: 'hash' | 'string' | 'json' | 'zset' | 'list' | 'set';
    ttl_seconds?: number | null;
    payload?: Record<string, any> | string;
    updated_at?: string;               // custom field if present
    checksum?: string;
  };

  qdrant?: {
    found: boolean;
    collection: string;                // e.g., documents
    point_id?: string | number;        // usually same as doc_id or hash
    payload?: Record<string, any>;
    vector_dims?: number;
    vector_hash?: string;              // e.g., xxhash of vector for quick compare
    updated_at?: string;               // if carried in payload
    checksum?: string;
  };

  consistency: {
    status: 'OK' | 'WARNING' | 'ERROR';
    problems: Array<{
      code: string;                    // e.g., MISSING_IN_REDIS, STALE_PG
      store?: 'postgres' | 'redis' | 'qdrant';
      message: string;
      hint?: string;
    }>;
    fieldDiff?: Array<{
      field: string;                   // canonical field name
      postgres?: any;
      redis?: any;
      qdrant?: any;
    }>;
  };
}
```

**Checksum policy (suggested)**
- Choose a **stable subset** of fields (e.g., `title`, `content`, `lang`, `version`) and compute `sha256(JSON.stringify(sortedSubset))` per store.
- For vectors, do not hash entire float array for performance; hash the first N dims (e.g., 256) after rounding to 6 decimals, or compute a murmur/xxhash of the bytes.

---

## 3) Store Conventions (Recommended)

**PostgreSQL**
- Table: `public.documents`
- PK: `id` (UUID or text)
- Columns (min): `id`, `title`, `content`, `lang`, `version`, `updated_at`, `embedding` (optional float[]), `meta` (jsonb)

**Redis**
- Key: `doc:{doc_id}`
- Type: `HASH` or `JSON` (if using RedisJSON)
- Fields: mirror a subset for fast read (`title`, `lang`, `updated_at`, `version`, `status`)
- Optional: maintain `doc:idx:updated_at` (ZSET) for recency checks

**Qdrant**
- Collection: `documents`
- `point.id` = `doc_id` (string) **or** numeric hash of `doc_id`
- `payload` mirrors canonical subset (`title`, `lang`, `version`, `doc_id`, timestamps, meta)
- `vector` is the embedding used for vector search

---

## 4) API (FastAPI Example)

> Swap to NestJS/Express if your team prefers TypeScript. Interfaces remain the same.

```py
# app/main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import asyncio

app = FastAPI(title="Tri-Store Admin Inspector")

class InspectResponse(BaseModel):
    # match TriStoreSnapshot shape (shortened here)
    doc_id: str
    requested_at: str
    postgres: dict | None
    redis: dict | None
    qdrant: dict | None
    consistency: dict

@app.get("/inspect/{doc_id}", response_model=InspectResponse)
async def inspect(doc_id: str, env: str = Query('prod')):
    # parallel gather from 3 stores
    pg, rd, qd = await asyncio.gather(
        fetch_postgres(doc_id, env),
        fetch_redis(doc_id, env),
        fetch_qdrant(doc_id, env)
    )
    snapshot = build_snapshot(doc_id, env, pg, rd, qd)
    return snapshot

@app.get("/diff/{doc_id}")
async def diff(doc_id: str, env: str = Query('prod')):
    snap = await inspect(doc_id, env)  # reuse
    return snap.consistency

@app.post("/repair/{doc_id}")
async def repair(doc_id: str, env: str = Query('prod'), strategy: str = Query('noop')):
    # strategies: noop | sync-to-pg | sync-to-redis | sync-to-qdrant | sync-majority
    # v1 keep disabled behind feature flag
    raise HTTPException(403, "Repair actions disabled in v1. Enable via config.")
```

**Connector stubs** (illustrative)
```py
# app/connectors.py
import asyncpg, aioredis, qdrant_client

async def fetch_postgres(doc_id, env):
    # query row and compute checksum
    # SELECT * FROM public.documents WHERE id=$1
    ...

async def fetch_redis(doc_id, env):
    # HGETALL doc:{doc_id} or JSON.GET
    ...

async def fetch_qdrant(doc_id, env):
    # client.retrieve(collection_name, ids=[doc_id])
    ...
```

**Consistency evaluator**
```py
# app/consistency.py
from hashlib import sha256

def stable_checksum(obj: dict, fields: list[str]):
    subset = {k: obj.get(k) for k in sorted(fields)}
    return sha256(str(subset).encode()).hexdigest()

def build_snapshot(doc_id, env, pg, rd, qd):
    problems = []
    field_diff = []

    # Presence checks
    for name, store in [("postgres", pg), ("redis", rd), ("qdrant", qd)]:
        if not store or not store.get("found"):
            problems.append({"code": f"MISSING_{name.upper()}", "store": name, "message": f"{name} has no record for {doc_id}"})

    # Example field compare (title, lang, version)
    fields = ["title", "lang", "version"]
    for f in fields:
        vals = {
            "postgres": pg.get("row", {}).get(f) if pg else None,
            "redis": (rd.get("payload", {}).get(f) if isinstance(rd.get("payload"), dict) else None) if rd else None,
            "qdrant": qd.get("payload", {}).get(f) if qd else None
        }
        if len({v for v in vals.values() if v is not None}) > 1:
            field_diff.append({"field": f, **vals})

    status = 'OK' if not problems and not field_diff else ('WARNING' if not problems else 'ERROR')

    return {
        "doc_id": doc_id,
        "requested_at": __import__("datetime").datetime.utcnow().isoformat()+"Z",
        "env": env,
        "postgres": pg,
        "redis": rd,
        "qdrant": qd,
        "consistency": {"status": status, "problems": problems, "fieldDiff": field_diff}
    }
```

---

## 5) Minimal SQL / Redis / Qdrant Samples

**PostgreSQL**
```sql
-- Core table
CREATE TABLE IF NOT EXISTS public.documents (
  id TEXT PRIMARY KEY,
  title TEXT,
  content TEXT,
  lang TEXT,
  version INT DEFAULT 1,
  updated_at TIMESTAMPTZ DEFAULT now(),
  embedding REAL[],
  meta JSONB
);

-- Fetch one
SELECT * FROM public.documents WHERE id = $1;
```

**Redis (Hash)**
```
HGETALL doc:{doc_id}
TTL doc:{doc_id}
```

**Qdrant (HTTP)**
```http
POST /collections/documents/points/retrieve
{
  "ids": ["{doc_id}"],
  "with_payload": true,
  "with_vector": false
}
```

---

## 6) Admin UI (Vue 3 + Tailwind, Composition API)

```html
<!-- InspectorCard.vue (snippet) -->
<template>
  <div class="p-4 rounded-2xl shadow bg-white dark:bg-zinc-900">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-semibold">Inspector</h2>
      <select v-model="env" class="border rounded px-2 py-1">
        <option value="dev">dev</option>
        <option value="staging">staging</option>
        <option value="prod">prod</option>
      </select>
    </div>

    <div class="mt-4 flex gap-2">
      <input v-model="docId" placeholder="Enter doc_id" class="flex-1 border rounded px-3 py-2" />
      <button @click="inspect" class="px-4 py-2 rounded bg-black text-white">Inspect</button>
    </div>

    <div v-if="data" class="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
      <StorePanel title="PostgreSQL" :store="data.postgres" />
      <StorePanel title="Redis" :store="data.redis" />
      <StorePanel title="Qdrant" :store="data.qdrant" />
    </div>

    <div v-if="data" class="mt-6">
      <h3 class="text-lg font-medium">Consistency</h3>
      <Badge :status="data.consistency.status" />
      <ul class="mt-3 list-disc pl-5" v-if="data.consistency.problems.length">
        <li v-for="p in data.consistency.problems" :key="p.code">{{ p.message }}</li>
      </ul>
      <table v-if="data.consistency.fieldDiff?.length" class="mt-4 w-full text-sm border">
        <thead><tr><th class="p-2 border">Field</th><th class="p-2 border">Postgres</th><th class="p-2 border">Redis</th><th class="p-2 border">Qdrant</th></tr></thead>
        <tbody>
          <tr v-for="d in data.consistency.fieldDiff" :key="d.field">
            <td class="p-2 border">{{ d.field }}</td>
            <td class="p-2 border">{{ fmt(d.postgres) }}</td>
            <td class="p-2 border">{{ fmt(d.redis) }}</td>
            <td class="p-2 border">{{ fmt(d.qdrant) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const env = ref('prod')
const docId = ref('')
const data = ref<any>(null)

function fmt(v:any){ return typeof v === 'object' ? JSON.stringify(v) : v }

async function inspect(){
  const res = await fetch(`/inspect/${encodeURIComponent(docId.value)}?env=${env.value}`)
  data.value = await res.json()
}
</script>
```

---

## 7) Docker Compose (Local Integration Sandbox)

```yaml
version: '3.9'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: postgres
    ports: ["5432:5432"]
  redis:
    image: redis:7
    ports: ["6379:6379"]
  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333", "6334:6334"]
  api:
    build: ./api
    environment:
      PG_DSN: postgresql://postgres:postgres@postgres:5432/postgres
      REDIS_URL: redis://redis:6379
      QDRANT_URL: http://qdrant:6333
      FEATURE_REPAIR: "false"
    ports: ["8080:8080"]
    depends_on: [postgres, redis, qdrant]
  ui:
    build: ./ui
    ports: ["5173:5173"]
    depends_on: [api]
```

---

## 8) Security, Auditing & Safety Rails

- **Auth**: SSO (OAuth/OIDC) with **Admin** role; restrict to office IPs / VPN.
- **RBAC**: `viewer` (inspect only), `operator` (export), `maintainer` (enable repair gates).
- **Audit log**: Log every inspect/export/repair to `admin_activity_log` with `who`, `when`, `doc_id`, `env`, `action`, `before/after checksums`.
- **Rate limit**: e.g., 120 inspect/min/admin.
- **Redaction**: Mask PII fields (`email`, `phone`) in UI by default; toggle with permission.

---

## 9) Test Matrix (Smoke)

1. **Presence**: Only in PG; only in Redis; only in Qdrant; all present.
2. **TTL**: Redis key nearing expiry (< 1h), flag WARNING.
3. **Field mismatch**: `version` diverges (PG=3, Redis=2, Qdrant=3) ⇒ fieldDiff.
4. **Embedding mismatch**: vector hash differs ⇒ WARNING.
5. **Staleness**: `updated_at` skew > 5 min ⇒ WARNING.
6. **Schema drift**: payload missing `lang` in Redis ⇒ WARNING + hint.

---

## 10) Optional Repair Strategies (v2)

- **sync-to-pg**: Write missing/older stores from Postgres as source of truth.
- **sync-majority**: If 2/3 stores agree on checksum/version, align the 3rd.
- **re-embed**: If payload changed but vector hash stale, recompute embedding.
- **re-key Redis**: Recreate Redis hash/json with fresh TTL.

> All repair ops **must** be idempotent, dry‑run first, and behind a feature flag + dual‑control approval.

---

## 11) Developer Notes & Conventions

- Normalize timestamps to **UTC ISO**.
- Prefer **store-specific timeouts** (e.g., 200–500ms) and surface partial results.
- Use **circuit breakers** to avoid cascading failures when a store is down.
- Put store settings under `/config/{env}.yaml` and let API select via `?env=`.

---

## 12) Quick Start (Pseudo)

1. `docker compose up -d`
2. Seed sample data: insert PG row; set Redis hash; upsert Qdrant point.
3. Open UI → input a known `doc_id` → review panels and diff table.

---

## 13) Future Enhancements

- **Multi-ID batch mode** with CSV upload and downloadable inconsistency report.
- **Vector neighborhood** preview: show top‑k neighbors to validate embedding.
- **Anomaly alerts**: webhook when inconsistency exceeds threshold.
- **Playbooks**: one‑click runbook links for common incidents.

---

## 14) Pluggable Architecture for Multi‑Store + Multi‑Embedding

To make the tool future‑proof (swap vector DBs, add new stores, run multiple embedding models), adopt a **provider‑plugin architecture** with a thin **core** and **adapters**.

### 14.1 Core Concepts
- **Provider**: Implements a minimal interface for a storage backend (Postgres, Redis, Qdrant, Pinecone, Weaviate, OpenSearch, Elasticsearch, Mongo, etc.).
- **Registry**: Runtime registry that maps a provider key (e.g., `qdrant`, `weaviate`) to an instance.
- **ConnectorConfig**: Typed config (host, creds, timeouts) with feature flags.
- **Normalizer**: Converts provider‑specific payloads to the **Canonical Admin View**.
- **Comparator**: Store‑agnostic diff engine that operates on the canonical view.

### 14.2 Provider Interfaces (Python, FastAPI backend)
```py
# app/providers/base.py
from typing import Protocol, Optional, Any

class StoreProvider(Protocol):
    name: str  # 'postgres' | 'redis' | 'qdrant' | 'weaviate' | 'pinecone' ...
    async def get_by_doc_id(self, doc_id: str) -> dict:
        """Return {found, payload, metadata} in provider-native shape."""
    async def health(self) -> dict: ...

class VectorProvider(StoreProvider, Protocol):
    async def retrieve_point(self, doc_id: str) -> dict:
        """Return vector dims/hash + payload if available."""

class KVProvider(StoreProvider, Protocol):
    async def ttl(self, key: str) -> Optional[int]: ...

class RelationalProvider(StoreProvider, Protocol):
    async def select_one(self, table: str, pk: str, value: Any) -> dict: ...
```

**Registry**
```py
# app/providers/registry.py
REGISTRY: dict[str, StoreProvider] = {}

def register(provider: StoreProvider):
    REGISTRY[provider.name] = provider

def get(name: str) -> StoreProvider:
    return REGISTRY[name]
```

**Usage in /inspect** (store‑agnostic)
```py
stores = [get(n) for n in cfg.enabled_providers]
results = await asyncio.gather(*[s.get_by_doc_id(doc_id) for s in stores])
# Normalize each result to canonical view entries then diff.
```

### 14.3 TypeScript option (if using Node/Nest)
```ts
export interface StoreProvider {
  name: string
  getByDocId(docId: string): Promise<{ found: boolean; payload?: any; meta?: any }>
  health(): Promise<any>
}

export interface VectorProvider extends StoreProvider {
  retrievePoint(docId: string): Promise<{ dims: number; vectorHash?: string; payload?: any }>
}
```

### 14.4 Config‑Driven Wiring
```yaml
# config/prod.yaml
providers:
  - type: postgres
    name: pg
    dsn: postgresql://...
  - type: redis
    name: redis
    url: redis://...
  - type: qdrant
    name: qdrant
    url: http://qdrant:6333
  - type: weaviate
    name: weaviate
    url: https://...
    api_key: ${WEAVIATE_API_KEY}

collections:
  documents:
    id_field: id
    vector:
      providers: [qdrant, weaviate]        # multiple vector stores supported
      embedding_models: [text-ada-002, e5-base, jina-v2]
      dims:
        text-ada-002: 1536
        e5-base: 768
        jina-v2: 1024
    ttl:
      redis_key_format: "doc:{id}"
      default_seconds: 2592000
```

### 14.5 Canonical Model Changes for Multi‑Embedding

Add an **Embeddings index** in Postgres to track per‑model vectors regardless of which vector DB stores them.

```sql
CREATE TABLE IF NOT EXISTS public.embeddings (
  doc_id TEXT NOT NULL,
  model_name TEXT NOT NULL,                 -- e.g., e5-base, text-3-large
  model_version TEXT,                       -- semantic model version if applicable
  store_provider TEXT NOT NULL,             -- qdrant | weaviate | pinecone | opensearch
  point_id TEXT,                            -- external id
  vector_dim INT NOT NULL,
  vector_hash TEXT,                         -- quick compare + drift detection
  updated_at TIMESTAMPTZ DEFAULT now(),
  meta JSONB,
  PRIMARY KEY (doc_id, model_name)
);
CREATE INDEX IF NOT EXISTS embeddings_provider_idx ON public.embeddings(store_provider);
```

**Why?**
- Lets you:
  - run **multiple models per doc** (A/B testing, domain‑specific vs general).
  - **migrate providers** gradually (dual‑write, comparehashes, cutover, decommission).
  - detect **embedding drift** when model upgrades.

### 14.6 Normalizer & Comparator for Many Sources

- Normalizer produces a map by **(store_name → canonical entry)**.
- Comparator supports **N>3 stores**, producing a matrix diff, and summary:
  - **Presence**: per store bool.
  - **Checksums**: per store stable checksum for content.
  - **Embeddings**: per `(model_name, store_provider)` pair show `vector_dim`, `vector_hash`.

**Canonical diff example**
```json
{
  "consistency": {
    "status": "WARNING",
    "problems": [
      {"code":"MISSING", "store":"weaviate", "message":"No point for doc:123"},
      {"code":"EMBEDDING_DRIFT", "store":"qdrant", "message":"hash mismatch for model e5-base"}
    ],
    "fieldDiff": [
      {"field":"version","postgres":3,"redis":2,"qdrant":3,"weaviate":3}
    ],
    "embeddings": [
      {"model":"e5-base","provider":"qdrant","dim":768,"hash":"a1b2"},
      {"model":"e5-base","provider":"weaviate","dim":768,"hash":"a1b2"},
      {"model":"text-3-large","provider":"qdrant","dim":3072,"hash":"c9d0"}
    ]
  }
}
```

### 14.7 Dual‑Write & Migration Playbook (Vector DB swap)
1. **Enable dual‑write**: On embed/upsert, write to both old and new providers.
2. **Backfill**: Stream historic doc_ids, compute missing vectors (per model), upsert to new provider.
3. **Verify**: Use this Inspector’s **embeddings matrix** to spot gaps and hash mismatches.
4. **Shadow read**: % of reads hit new provider; compare search results offline.
5. **Cutover**: Flip search traffic; keep dual‑write for 1–2 weeks.
6. **Decommission**: Disable writes to old provider; archive metadata.

### 14.8 UI Changes (N‑store aware)
- Left panel: **Stores** (multi‑select) and **Embedding Models** (multi‑select).
- Embeddings tab: table grouped by **model** → rows per **provider** showing dim/hash/updated_at.
- Export: JSON/CSV includes embeddings matrix for audits.

### 14.9 Observability & Policy
- Per‑provider **SLOs** (latency, error rate); circuit‑break per instance.
- **Feature flags** per provider (`read`, `write`, `dual_write`, `shadow_read`).
- **Version pinning** for embedding models; warn if model version changed but vectors not recomputed.

---

## 15) Example: Adding a New Vector Provider (Weaviate)

**Adapter skeleton**
```py
# app/providers/weaviate_adapter.py
from .base import VectorProvider
class WeaviateProvider(VectorProvider):
    name = 'weaviate'
    def __init__(self, url: str, api_key: str):
        self.client = ...
    async def get_by_doc_id(self, doc_id: str) -> dict:
        # fetch object + payload
        return {"found": True, "payload": {...}, "meta": {...}}
    async def retrieve_point(self, doc_id: str) -> dict:
        # fetch vector dims/hash and metadata
        return {"dims": 768, "vectorHash": "...", "payload": {...}}
    async def health(self) -> dict:
        return {"ok": True}
```

**Wire it in**
```py
from app.providers.registry import register
from app.providers.weaviate_adapter import WeaviateProvider

register(WeaviateProvider(url=CFG.WEAVIATE_URL, api_key=CFG.WEAVIATE_API_KEY))
```

This lets the **Inspector** work unchanged while supporting multiple vector DBs and multiple embedding models for the same document.

