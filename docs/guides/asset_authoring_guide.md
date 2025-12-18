# ABS AI Fabric – Asset Authoring Guide (v1.0)

**Audience:** Engineers adding or modifying assets
**Scope:** `asset.yaml` authoring only
**Status:** Canonical, opinionated

---

## 1. Golden Rules (Read This First)

### Rule 1: You author **intent**, not runtime state

* ✅ You define **what the asset is**
* ❌ You do NOT control how or when it runs

The Gateway owns:

* `lifecycle.state`
* runtime start/stop
* `_status` metadata

---

### Rule 2: Bind to **interfaces**, never implementations

* Apps depend on **interfaces**
* Runtimes implement interfaces
* Never hardcode containers, ports, or hosts in apps

If you violate this, your asset will be rejected.

---

### Rule 3: Keep assets small and single-purpose

One asset = one responsibility.

If an asset:

* Does more than one thing
* Requires another asset to function internally

→ You probably need **two assets**.

---

## 2. Choosing the Right Asset Category

You MUST choose exactly one category:

```
assets/
├── apps/       → user-facing workflows
├── core/       → shared infrastructure
├── models/     → inference artifacts
├── tools/      → atomic capabilities
├── datasets/   → persistent data
```

### Quick Decision Table

| If it…              | It is…    |
| ------------------- | --------- |
| Has UI / workflow   | `app`     |
| Runs shared infra   | `core`    |
| Is a model          | `model`   |
| Performs one action | `tool`    |
| Stores knowledge    | `dataset` |

Do not invent new categories.

---

## 3. Minimal Required Fields (All Assets)

Every `asset.yaml` MUST define:

```yaml
asset_id: my-asset
display_name: My Asset
version: "1.0.0"

interface: some-interface
interface_version: v1
class: app | service | model | tool | dataset

description: |
  One or two clear sentences explaining purpose.

lifecycle:
  desired: running | on-demand | suspended
```

If any of these are missing, validation will fail.

---

## 4. Lifecycle: What You May (and May Not) Do

### You MAY set:

```yaml
lifecycle:
  desired: on-demand
  auto_sleep_min: 15
```

### You MUST NOT set:

```yaml
lifecycle:
  state: running        # ❌ forbidden
```

Why?

* `state` is observed reality
* The Gateway determines it

---

## 5. Runtime Section (Only If It Actually Runs)

Only include `runtime` if the asset has runtime behavior.

### Correct

```yaml
runtime:
  type: container
  container:
    image: ollama/ollama:latest
```

### Incorrect

```yaml
runtime:
  container:
    image: something
```

Always specify `runtime.type`.

---

## 6. Policy Rules (Be Strict)

### Apps

Use **only**:

```yaml
policy:
  required_models:
    - llama3-8b
```

### Runtimes / Services

Use **only**:

```yaml
policy:
  served_models:
    - llama3-8b
```

❌ Never mix these
❌ Never put model IDs in app runtime config

---

## 7. Resource Declaration (Be Honest)

Declare resources **conservatively**:

```yaml
resources:
  gpu_required: true
  min_vram_gb: 16
  min_ram_gb: 32
  disk_gb: 50
  cold_start_sec: 30
```

These values are used for:

* Scheduling
* Pack budgeting
* UI expectations

Inflated or missing values will be flagged.

---

## 8. Packs: Optional, Not Required

If your asset belongs to an extended pack:

```yaml
pack_id: llm-xl
```

Rules:

* Assets remain first-class
* Packs add governance only
* Core assets usually have no `pack_id`

Do NOT encode pack behavior inside the asset.

---

## 9. Metadata: Use, Don’t Abuse

`metadata` is free-form, but:

### Allowed

```yaml
metadata:
  vendor: Meta
  precision: fp16
```

### Forbidden

```yaml
metadata:
  _status: ...     # ❌ Gateway-owned
```

Anything under `_status` is reserved for the system.

---

## 10. What Will Get Your Asset Rejected

Your asset will fail validation if you:

* Set `lifecycle.state`
* Omit `interface`
* Use the wrong policy field
* Invent new enum values
* Put runtime details in apps
* Bypass interfaces
* Abuse `metadata` for system fields

---

## 11. A Good Asset Is Boring

The best assets:

* Are predictable
* Are small
* Look similar to other assets
* Contain no surprises

> **Creativity belongs in apps, not in asset definitions.**

---

## 12. Final Checklist (Before Commit)

Before submitting an asset:

* [ ] Correct category
* [ ] Interface declared
* [ ] Lifecycle intent only
* [ ] No Gateway-owned fields
* [ ] Resource requirements declared
* [ ] Policy fields correct
* [ ] Valid YAML

If in doubt, copy an existing asset and modify it.

---

**This guide is intentionally strict.**
That’s how ABS AI Fabric stays stable while everything else evolves.
