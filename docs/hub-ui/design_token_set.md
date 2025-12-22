# 🎨 ABS AI Fabric — Design Token Set v1.0

**Theme philosophy:** *Industrial Intelligence*
**Default mode:** Dark-first (enterprise & CES ready)

---

## 0️⃣ Token Structure (How to Read This)

* **Core tokens** → raw values (brand DNA)
* **Semantic tokens** → meaning-based (recommended usage)
* **Component tokens** → buttons, cards, panels
* **Motion tokens** → “alive but calm”
* **CES overrides** → demo-optimized accents

Engineering should **consume semantic & component tokens only**.

---

## 1️⃣ Core Brand Tokens (ABS DNA)

```json
{
  "color": {
    "brand": {
      "primary": "#2563EB",
      "secondary": "#14B8A6"
    },
    "neutral": {
      "black": "#0B0F14",
      "black_soft": "#0F141B",
      "gray_900": "#111827",
      "gray_700": "#374151",
      "gray_500": "#6B7280",
      "gray_300": "#D1D5DB",
      "white": "#F9FAFB"
    }
  }
}
```

**Design intent**

* Blue = authority + compute
* Teal = intelligence + future
* Near-black = reliability, seriousness, “engine room”

---

## 2️⃣ Semantic Color Tokens (MOST IMPORTANT)

> These are what engineers should use.

```json
{
  "color": {
    "background": {
      "app": "#0B0F14",
      "panel": "#0F141B",
      "card": "#111827",
      "overlay": "rgba(0,0,0,0.6)"
    },
    "text": {
      "primary": "#F9FAFB",
      "secondary": "#9CA3AF",
      "muted": "#6B7280",
      "inverse": "#0B0F14"
    },
    "border": {
      "default": "rgba(255,255,255,0.08)",
      "strong": "rgba(255,255,255,0.16)",
      "focus": "#2563EB"
    },
    "action": {
      "primary": "#2563EB",
      "primary_hover": "#1D4ED8",
      "secondary": "#1F2937",
      "danger": "#EF4444"
    },
    "status": {
      "success": "#22C55E",
      "warning": "#F59E0B",
      "error": "#EF4444",
      "info": "#3B82F6",
      "running": "#14B8A6"
    }
  }
}
```

**ABS Principle**

> Color communicates **state**, not decoration.

---

## 3️⃣ Typography Tokens (Trust & Clarity)

```json
{
  "font": {
    "family": {
      "base": "Inter, system-ui, -apple-system, BlinkMacSystemFont",
      "mono": "JetBrains Mono, Menlo, monospace"
    },
    "size": {
      "xs": "12px",
      "sm": "13px",
      "md": "14px",
      "lg": "16px",
      "xl": "18px",
      "xxl": "24px",
      "metric": "28px"
    },
    "weight": {
      "regular": 400,
      "medium": 500,
      "semibold": 600
    },
    "lineHeight": {
      "tight": 1.2,
      "normal": 1.5,
      "loose": 1.75
    }
  }
}
```

**Guidance**

* Metrics (GPU %, VRAM) → `font.size.metric` + mono
* No sci-fi fonts, no thin weights

---

## 4️⃣ Spacing & Layout Tokens (Calm Power)

```json
{
  "spacing": {
    "xs": "4px",
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "24px",
    "xxl": "32px",
    "page_padding": "24px"
  },
  "layout": {
    "max_width": "1440px",
    "grid_gap": "16px"
  }
}
```

> **Whitespace = confidence**
> Crowded UI kills enterprise trust.

---

## 5️⃣ Radius, Border & Elevation (OS-Like)

```json
{
  "radius": {
    "sm": "6px",
    "md": "8px",
    "lg": "12px",
    "xl": "16px"
  },
  "shadow": {
    "none": "none",
    "card": "0 0 0 1px rgba(255,255,255,0.06)",
    "hover": "0 0 0 1px rgba(37,99,235,0.4)",
    "modal": "0 20px 40px rgba(0,0,0,0.6)"
  }
}
```

**Key insight**

* Borders > shadows
* Precision > drama

---

## 6️⃣ Motion & Interaction Tokens (Alive, Not Flashy)

```json
{
  "motion": {
    "duration": {
      "fast": "120ms",
      "normal": "240ms",
      "slow": "360ms"
    },
    "easing": {
      "standard": "cubic-bezier(0.4, 0, 0.2, 1)",
      "emphasis": "cubic-bezier(0.2, 0, 0, 1)"
    }
  }
}
```

**Usage**

* Metrics update → `normal`
* Hover → `fast`
* Page transition → `slow`

---

## 7️⃣ Component Tokens (Mapped to Your UI)

### App Cards

```json
{
  "card": {
    "background": "#111827",
    "border": "rgba(255,255,255,0.08)",
    "radius": "12px",
    "padding": "16px",
    "hover_border": "#2563EB"
  }
}
```

### Buttons

```json
{
  "button": {
    "primary": {
      "bg": "#2563EB",
      "bg_hover": "#1D4ED8",
      "text": "#F9FAFB",
      "radius": "8px"
    },
    "secondary": {
      "bg": "#1F2937",
      "text": "#D1D5DB"
    }
  }
}
```

### Badges (ABS Official, Ready, Local)

```json
{
  "badge": {
    "default": "#1F2937",
    "success": "#22C55E",
    "info": "#3B82F6",
    "running": "#14B8A6"
  }
}
```

---

## 8️⃣ Live Metrics Tokens (Workstation Console)

```json
{
  "metric": {
    "value_color": "#F9FAFB",
    "label_color": "#9CA3AF",
    "active_pulse": "#14B8A6",
    "warning": "#F59E0B",
    "critical": "#EF4444"
  }
}
```

Add **subtle pulse animation** when GPU > 50%.

---

## 9️⃣ CES Demo Mode Overrides (Optional but Recommended)

```json
{
  "ces": {
    "color": {
      "accent_boost": "#3B82F6",
      "metric_glow": "rgba(59,130,246,0.4)"
    },
    "font": {
      "metric": "32px"
    }
  }
}
```

Only **slightly brighter**, never flashy.

---

## 🔟 ABS UX Principles (Pin This for Engineers)

1. **Clarity beats cleverness**
2. **Live systems should feel alive, not noisy**
3. **Dark, calm, precise > bright and loud**
4. **Hardware power is shown through stability**
5. **OS first, marketing second**

---

## ✅ What This Enables Immediately

* CES Demo Theme toggle
* Consistent ABS branding
* Faster UI iteration
* Partner / OEM theming later
* A true **AI OS identity**

