# 📘 Document Library - Feature Specification

## 1. Purpose
The **Document Library** acts as a unified repository for all documents accessible by the Contract Reviewer system. It combines manual uploads and automated discovery through configured watch directories, enabling seamless access, management, and analysis.

---

## 2. Objectives
- Provide a central hub for browsing, organizing, and managing documents.
- Integrate file ingestion from multiple sources: **Upload**, **Watch**, and **Library**.
- Enable manual and automatic scanning of file locations.
- Facilitate seamless transition between **Document Library** and **Document Review**.

---

## 3. Source Type Definitions
| Source Type | Description | Trigger | Processing Behavior |
|--------------|-------------|----------|----------------------|
| `upload` | Manually uploaded documents from the UI | User uploads via Document Review | Immediate or manual analysis |
| `watch` | Automatically monitored directories | Real-time watcher detects changes | Automatic ingestion & analysis |
| `library` | Indexed but not automatically processed | Manual or scheduled scanning | Metadata-only indexing until user triggers analysis |

---

## 4. User Interface Overview
### Tabs in Top Navigation
**Document Review | Document Library | Review History**

### Key Sections
- **Left Panel:** List of configured directories (local, network, or cloud)
- **Main Panel:** Display of files within the selected directory
- **Right Panel:** Statistics, scan settings, and actions

---

## 5. Core Features

### 🧩 Directory Management
- Add new directories (path, recursion, file filters)
- Toggle auto-scan or manual-only mode
- Edit and remove directories
- Display directory health (active, inactive, error)

### 📄 File Listing
- Show all files detected within selected directory
- Metadata: filename, size, type, modified date, status, source
- File actions: “Analyze Now”, “View Analysis”, “Delete from Library”

### 📊 Statistics and Insights
- Per-directory stats (total, analyzed, pending, failed)
- Global library metrics (total docs, analysis time, storage usage)
- Scan history and performance tracking

### 🔍 Search and Filter
- Full-text and metadata search
- Filters by date, file type, and status
- “Show only unreviewed” toggle

### 💬 Integration
- Library files appear in Global Chat (“All Docs” mode)
- Document Review page includes “Select from Library” option

---

## 6. Backend Design

### Entities
- `watch_directories` → Directory configuration and status
- `library_files` → Indexed files metadata
- `documents` → Links to analysis data

### New Field in Documents Table
```sql
ALTER TABLE documents ADD COLUMN source_type VARCHAR(20) DEFAULT 'upload';
```

### API Endpoints (reference only)
| Endpoint | Purpose |
|-----------|----------|
| `GET /api/watch-directories` | List watch or library directories |
| `POST /api/watch-directories` | Add directory |
| `PATCH /api/watch-directories/{id}` | Edit directory |
| `POST /api/watch-directories/{id}/scan` | Trigger manual scan |
| `GET /api/library/files` | List all library files |
| `GET /api/library/stats` | Get aggregated library stats |

---

## 7. Integration Flow
1. User adds a directory via UI → stored in DB
2. WatchDirectoryService or LibraryScanService indexes or processes files
3. Files appear in Document Library list
4. User can analyze or open documents directly in Contract Reviewer
