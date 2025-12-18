## ABS AI Fabric – Asset Management Architecture (v1.0)

```mermaid
flowchart TB
    %% =========================
    %% Users & Apps
    %% =========================
    User[User / Developer]
    App[Application Asset<br/>apps/*]

    %% =========================
    %% Hub UI
    %% =========================
    UI[Hub UI<br/>Assets · Packs · Admin]

    %% =========================
    %% Gateway (Control Plane)
    %% =========================
    subgraph Gateway["ABS AI Fabric Gateway (Control Plane)"]
        Resolver[Interface Resolver]
        AssetMgr[Asset Manager]
        PackMgr[Pack Manager]
        Lifecycle[Lifecycle Controller]
        Status[Status Collector]
        Policy[Policy Enforcement]
    end

    %% =========================
    %% Registry & Definitions
    %% =========================
    subgraph Registry["Asset Definitions (Git / FS)"]
        Reg[assets/registry/assets.json]
        AssetsYaml[asset.yaml<br/>(apps · core · models · tools · datasets)]
        PacksYaml[pack.yaml<br/>(extended packs)]
        Interfaces[core-interfaces/*]
    end

    %% =========================
    %% Runtime / Data Plane
    %% =========================
    subgraph Runtime["Runtime / Data Plane"]
        CoreServices[Core Services<br/>LLM Runtime · Vector DB · Cache · DB]
        Models[Models<br/>7B–70B]
        Tools[Tools<br/>OCR · Parser · Reranker]
        Datasets[Datasets<br/>RAG · Corpora]
    end

    %% =========================
    %% Relationships
    %% =========================
    User --> UI
    UI -->|REST| Gateway

    App -->|Interface Calls| Gateway

    Gateway --> Resolver
    Resolver --> Interfaces

    Gateway --> AssetMgr
    AssetMgr --> Reg
    AssetMgr --> AssetsYaml

    Gateway --> PackMgr
    PackMgr --> PacksYaml

    Gateway --> Policy
    Gateway --> Lifecycle
    Lifecycle --> CoreServices
    Lifecycle --> Tools

    Gateway --> Models
    Gateway --> Datasets

    Gateway --> Status
    Status --> UI

    %% =========================
    %% Notes
    %% =========================
    classDef control fill:#e3f2fd,stroke:#1e88e5,stroke-width:1px;
    classDef data fill:#f1f8e9,stroke:#558b2f,stroke-width:1px;
    classDef runtime fill:#fff3e0,stroke:#ef6c00,stroke-width:1px;

    class Gateway,Resolver,AssetMgr,PackMgr,Lifecycle,Policy,Status control
    class Reg,AssetsYaml,PacksYaml,Interfaces data
    class CoreServices,Models,Tools,Datasets runtime
```

---

## How to Read This Diagram (1-Minute Guide)

### 1️⃣ Control Plane vs Data Plane

* **Gateway** is the **only control plane**
* Core services, models, tools, datasets are **runtime assets**
* Apps never touch Docker, containers, or runtimes directly

---

### 2️⃣ Assets Are Declarative

* All assets are defined via `asset.yaml`
* Registry (`assets.json`) is an **index only**
* Packs (`pack.yaml`) apply **policy + governance**, not runtime logic

---

### 3️⃣ Interfaces Are the Contract

* Apps bind to **interfaces**
* Resolver selects implementations
* Implementations are swappable (Ollama ↔ vLLM)

---

### 4️⃣ Packs Are Orthogonal

* Packs group assets across categories
* Approval, limits, GPU cost enforced at Gateway
* Assets remain first-class

---

## Why This Diagram Matters

This architecture:

✔ Separates **what exists** from **what runs**
✔ Enables **safe upgrades and parallel runtimes**
✔ Keeps **UI simple and honest**
✔ Scales from **single workstation → team → cluster**
✔ Avoids Kubernetes / CRD complexity entirely

> This is an **AI operating fabric**, not an app launcher.
