# 🧭 Document Library - Wireframe Layout

## 1. Overview
The Document Library UI mirrors the modern, clean style of **Contract Reviewer v2** while introducing directory management and document indexing views.

---

## 2. Page Layout Structure

```
──────────────────────────────────────────────────────────────
🧾  CONTRACT REVIEWER v2                         [User ⚙️]
──────────────────────────────────────────────────────────────
📁 Document Review | 📚 Document Library | 🕓 Review History
──────────────────────────────────────────────────────────────

📂 Document Library
──────────────────────────────────────────────────────────────
│ [ + Add Directory ]   [ ⟳ Scan All ]   [ ⚙ Settings ]
│────────────────────────────────────────────────────────────
│ 📂 Watch / Library Locations
│────────────────────────────────────────────────────────────
│ ▸ /shared/contracts/incoming     [Active] [12 files]
│    Last Scan: 5m ago   Status: ✅ OK
│ ▸ /archive/contracts/2022        [Library] [103 files]
│    Last Scan: 2h ago   Status: ⏳ Scanning...
│ ▸ /external/legal/share          [Inactive]
│    Last Scan: —       Status: ⚠️ Access denied
│────────────────────────────────────────────────────────────
│
│ 📄 Files in Selected Directory (/shared/contracts/incoming)
│────────────────────────────────────────────────────────────
│ 🔍 [ Search files... ]  [Status ▾] [Type ▾] [Date ▾]
│────────────────────────────────────────────────────────────
│ ▣ sample_agreement.docx   [Analyzed]   38 KB   🔗 View
│ ▣ nda_template.docx       [New]        56 KB   ▶ Analyze Now
│ ▣ terms_2025.docx         [Processing] 72 KB   ⏳ In Progress
│────────────────────────────────────────────────────────────
│ 📊 Directory Stats
│────────────────────────────────────────────────────────────
│ Total: 120 | Analyzed: 85 | Pending: 30 | Failed: 5
│ Last Scan: 2025-10-26 08:15 AM
│ [Auto Scan ▢]  [ Scan Now ]  [ Edit Directory ]
│────────────────────────────────────────────────────────────
│ 📈 Global Library Stats
│────────────────────────────────────────────────────────────
│ Directories: 4 | Files Indexed: 720 | Analyzed: 615
│ Avg Analysis Time: 42 sec | Space: 1.2 GB
──────────────────────────────────────────────────────────────
```

---

## 3. Layout Sections

### A. Header
- Shared with Contract Reviewer (same blue navbar)
- Tabs: **Document Review | Document Library | Review History**

### B. Directory List
- Left column showing all configured directories
- Each directory shows:
  - Path name
  - Status icon
  - File count
  - Last scan timestamp

### C. File Table
- Center panel listing detected documents
- Columns: Filename | Type | Size | Status | Actions

### D. Stats & Actions Panel
- Right column with scan statistics
- Buttons: “Scan Now”, “Auto Scan”, “Edit Directory”

### E. Global Library Stats
- Bottom summary bar showing aggregated library info

---

## 4. Interactions
| Action | Result |
|--------|---------|
| **+ Add Directory** | Opens modal for path, recursion, and filters |
| **Scan Now** | Manually triggers directory scan |
| **Analyze Now** | Opens Document Review for the selected document |
| **View Analysis** | Navigates to existing review context |
| **Toggle Auto Scan** | Enables/disables background monitoring |

---

## 5. Responsive Design
| View | Adjustment |
|------|-------------|
| Desktop | 3-column layout (Directories, Files, Stats) |
| Tablet | Collapsible Stats column |
| Mobile | Stack panels vertically |

---

## 6. Notes for Frontend Implementation
- Framework: Alpine.js / Vue (consistent with Contract Reviewer v2)
- Styling: TailwindCSS
- Components: `DirectoryList`, `FileTable`, `LibraryStatsPanel`
- Integrates with `/api/watch-directories` and `/api/library/files`
