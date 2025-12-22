# ABS AI OS — Design Token Set v1.1

**Status:** Approved (Brand-Locked)
**Applies to:** ABS AI Fabric / Hub UI / CES Demo Mode
**Theme philosophy:** **Industrial Performance Intelligence**
**Default mode:** Dark-first
**Brand alignment:** ABS Official

---

## 0. Purpose & Principles

This token set defines the **single source of truth** for ABS AI OS visual language.

### Core principles

1. **Black-forward, high contrast**
2. **Energy is intentional, not decorative**
3. **Hardware authority > SaaS friendliness**
4. **Motion communicates “alive”, never playful**
5. **Tokens are semantic, not literal**

> ABS AI OS should feel like a **battle-tested control plane**, not a dashboard.

---

## 1. Token Taxonomy

Tokens are layered to prevent UI drift:

1. **Core Brand Tokens** – ABS DNA (never referenced directly in UI)
2. **Semantic Tokens** – meaning-based (used by engineers)
3. **Component Tokens** – cards, buttons, badges
4. **State & Motion Tokens**
5. **CES Demo Overrides**

⚠️ **Engineering rule:**
Use **semantic or component tokens only**, never raw hex values.

---

## 2. Core Brand Tokens (ABS DNA)

> Extracted from official ABS brand palette 

```yaml
brand:
  black: "#111411"        # Neutral Black (Primary)
  navy: "#031D49"         # Deep Navy
  orange: "#FD6120"       # Bright Orange (Energy / Authority)
  indigo: "#503FFF"       # Electric Indigo (High-Tech)
```

---

## 3. Semantic Color Tokens (Primary Consumption Layer)

### 3.1 Backgrounds (Black-Forward)

```yaml
color:
  background:
    app: "#111411"
    panel: "#0E110F"
    card: "#141817"
    elevated: "#181D1B"
    overlay: "rgba(0,0,0,0.65)"
```

**Intent**

* App feels grounded and premium
* Elevated surfaces signal control layers

---

### 3.2 Text

```yaml
color:
  text:
    primary: "#F9FAFB"
    secondary: "#9CA3AF"
    muted: "#6B7280"
    inverse: "#111411"
```

---

### 3.3 Borders & Dividers

```yaml
color:
  border:
    default: "rgba(255,255,255,0.08)"
    strong: "rgba(255,255,255,0.16)"
    divider: "rgba(255,255,255,0.06)"
    focus: "#503FFF"
```

---

### 3.4 Actions & Emphasis

```yaml
color:
  action:
    primary: "#503FFF"          # Electric Indigo
    primary_hover: "#6B5CFF"
    secondary: "#1C1F1E"
    performance: "#FD6120"      # ABS Orange (sparingly)
    danger: "#EF4444"
```

📌 **Rule**

* Indigo = control / navigation
* Orange = performance spike / official authority

---

### 3.5 Status & Runtime States

```yaml
color:
  status:
    success: "#22C55E"
    warning: "#F59E0B"
    error: "#EF4444"
    info: "#503FFF"
    running: "#FD6120"
    idle: "#9CA3AF"
```

---

## 4. Typography Tokens (ABS-Correct Usage)

> Based on ABS typography rules 

```yaml
font:
  family:
    headline: "Barlow Condensed, sans-serif"
    body: "Rajdhani, Inter, system-ui, sans-serif"
    mono: "JetBrains Mono, Menlo, monospace"
```

### Font Sizes

```yaml
font:
  size:
    xs: 12px
    sm: 13px
    md: 14px
    lg: 16px
    xl: 18px
    "2xl": 20px
    xxl: 24px
    metric: 28px
```

### Weights & Letter Spacing

```yaml
font:
  weight:
    regular: 400
    medium: 500
    semibold: 600

  letterSpacing:
    badge: "0.04em"
    label: "0.02em"
    uppercase: "0.06em"
```

**Usage rules**

* **Barlow Condensed** → app titles, section headers, metrics labels
* **Rajdhani** → body copy, descriptions
* **Mono** → metrics, IDs, logs

---

## 5. Spacing & Layout

```yaml
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  xxl: 32px
  page_padding: 24px

layout:
  max_width: 1440px
  grid_gap: 16px
```

> Whitespace = confidence.

---

## 6. Radius, Borders & Elevation

```yaml
radius:
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px

shadow:
  none: none
  card: "0 0 0 1px rgba(255,255,255,0.06)"
  hover: "0 0 0 1px rgba(80,63,255,0.5)"
  modal: "0 24px 48px rgba(0,0,0,0.7)"
```

ABS uses **precision borders**, not fluffy shadows.

---

## 7. Motion Tokens (Alive, Disciplined)

```yaml
motion:
  duration:
    fast: 120ms
    normal: 240ms
    slow: 360ms

  easing:
    standard: "cubic-bezier(0.4, 0, 0.2, 1)"
    emphasis: "cubic-bezier(0.2, 0, 0, 1)"
```

🚫 No bounce
🚫 No elastic
🚫 No RGB cycling

---

## 8. Component Tokens

### 8.1 App Cards

```yaml
component:
  card:
    background: "#141817"
    border: "rgba(255,255,255,0.08)"
    radius: 12px
    padding: 16px
    hover_border: "#503FFF"
```

---

### 8.2 Buttons

```yaml
component:
  button:
    primary:
      bg: "#503FFF"
      bg_hover: "#6B5CFF"
      text: "#F9FAFB"
      radius: 8px

    secondary:
      bg: "#1C1F1E"
      text: "#D1D5DB"
```

---

### 8.3 Trust Badges (Critical for Apps Page)

```yaml
badge:
  trust:
    abs_official: "#FD6120"   # ABS Authority
    partner: "#503FFF"        # Technical Alliance
    community: "#EAB308"
    unverified: "#9CA3AF"
```

📌 Orange here is **intentional and brand-correct**.

---

## 9. Accessibility & States

```yaml
state:
  disabled:
    bg: "#1C1F1E"
    text: "#6B7280"
    border: "rgba(255,255,255,0.04)"

focus:
  ring_color: "#503FFF"
  ring_width: 2px
  ring_offset: 2px
```

WCAG contrast compliance required for all text tokens.

---

## 10. Z-Index Scale (OS-Grade)

```yaml
zIndex:
  base: 0
  dropdown: 100
  sticky: 200
  overlay: 400
  modal: 600
  toast: 800
  tooltip: 1000
```

---

## 11. CES Demo Mode Overrides (Optional Layer)

```yaml
ces:
  accent:
    highlight: "#FD6120"
    glow: "rgba(253,97,32,0.45)"

  font:
    metric: 32px
```

Used only when **CES Demo Mode = ON**.

---

## 12. Non-Negotiable UX Rules (ABS)

1. Black is dominant
2. Orange is earned, not decorative
3. Motion is subtle
4. Hardware metrics must feel “live”
5. OS first, marketing second

---

## 13. Versioning & Evolution

* **v1.1** — Brand-locked
* Deprecated tokens must live for ≥1 minor version
* CES overrides must never affect default mode

---

## 14. Summary

This token set ensures ABS AI OS:

* Looks unmistakably **ABS**
* Feels **powerful and reliable**
* Scales from **CES demo → enterprise deployment**
* Avoids SaaS sameness
* Reinforces ABS as a **pioneer of the AI workstation era**
