# 🧩 ABS Workstation Console – Attract Mode

## UI Wireframe Specification (v1.0)

---

## 1️⃣ Overall Layout (Full-Screen, OS-Native)

![Image](https://cdn.dribbble.com/userupload/15813489/file/original-9784c3910b8ae034233dc1730426afbd.jpeg?resize=400x0\&utm_source=chatgpt.com)

![Image](https://miro.medium.com/v2/resize%3Afit%3A1400/1%2AKtP5GW1BzOvzYFBbOyHUbg.png?utm_source=chatgpt.com)

![Image](https://media.easy-peasy.ai/27feb2bb-aeb4-4a83-9fb6-8f3f2a15885e/8016b597-ead6-4653-99b6-8e1842d60dca.png?utm_source=chatgpt.com)

![Image](https://cdn.dribbble.com/userupload/2847113/file/original-d631044efbeed0b9b4a3220079411c76.png?resize=400x0\&utm_source=chatgpt.com)

**Canvas**

* Full-screen takeover inside **ABS Workstation Console**
* No browser chrome
* No navigation
* Esc / input exits immediately

```
┌─────────────────────────────────────────────┐
│  ABS Workstation Console        ● LIVE LOCAL │
│                                             │
│  [ A ] LIVE SYSTEM METRICS (HERO)            │
│                                             │
│  [ B ] AI VISUAL DEMO (CENTER STAGE)         │
│                                             │
│  [ C ] BRAND + STATUS STRIP (SUBTLE)         │
└─────────────────────────────────────────────┘
```

---

## 2️⃣ Wireframe A — Entry State (Idle → Fade In)

**Trigger**

* No input for X seconds
* Smooth fade from normal console view

### Visual Behavior

* Background darkens slightly
* Metrics fade in first
* Visual demo loads after metrics are stable

```
[ Fade-in overlay 300ms ]
```

📌 **Rule**

> Attract Mode must *feel intentional*, not like a screensaver snapping on.

---

## 3️⃣ Wireframe B — Live System Metrics (Always Visible)

![Image](https://developer-blogs.nvidia.com/wp-content/uploads/2024/05/nvdashboard-dark.png?utm_source=chatgpt.com)

![Image](https://assets.justinmind.com/wp-content/uploads/2020/02/dashboard-layout-hierarchy.png?utm_source=chatgpt.com)

![Image](https://imgproxy.epicpxls.com/rkv3VuBHAcZFipAJYIJihgj8luyNxc0-14Jfh4jJ6H0/rs%3Afill%3A800%3A600%3A0/g%3Ano/aHR0cHM6Ly9pdGVt/cy5lcGljcHhscy5j/b20vdXBsb2Fkcy9w/aG90by8wNGQ2MTA3/Yjc4MTRiOTZmN2Ez/ODNhZmQxZjhjMGVi/Yg.jpg?utm_source=chatgpt.com)

### Placement

**Top-left to center-left** (eye naturally starts here)

```
┌───────────────┬───────────────┐
│ GPU UTIL (%)  │ VRAM (GB)     │
│  68%          │  36 / 48      │
├───────────────┼───────────────┤
│ CPU LOAD      │ RAM           │
│  24%          │  82 / 128     │
├───────────────┴───────────────┤
│ RTX Pro 6000 • Uptime 02:14:32│
└───────────────────────────────┘
```

### Style

* Large numerals
* Slow number interpolation
* No flicker
* GPU tile slightly larger than others

### CES Accent (CES_MODE)

* Thin ABS Orange underline on GPU tile
* Subtle pulse when GPU > 50%

---

## 4️⃣ Wireframe C — AI Visual Demo (Center Stage)

![Image](https://previews.123rf.com/images/maylim33/maylim332305/maylim33230503295/205025909-ai-generated-illustration-of-big-data-visualization-abstract-graphic-consisting-of-blured-points.jpg?utm_source=chatgpt.com)

![Image](https://miro.medium.com/1%2AaNK3BEFslxcyjvM4bi0tAQ.png?utm_source=chatgpt.com)

![Image](https://www.dasca.org/Content/images/main/ai-in-advancing-data-visualization.jpg?utm_source=chatgpt.com)

### Placement

**Center / right side**, dominant visual

```
┌───────────────────────────────────────────┐
│                                           │
│   [ LIVE AI VISUAL ]                       │
│                                           │
│   - Image generation OR                   │
│   - System visualization                  │
│                                           │
│   Subtle progress indicator               │
│                                           │
└───────────────────────────────────────────┘
```

### Visual Types

* SDXL image generation (fade between images)
* Abstract compute visualization (WebGL)
* Optional LLM token stream (lower opacity)

### Rules

* Only **one** visual at a time
* No sharp cuts
* Cross-fade transitions (500–800ms)

---

## 5️⃣ Wireframe D — Branding & Messaging Strip

![Image](https://miro.medium.com/1%2AdjOWBfUNhFUPeDHchV9cEQ.jpeg?utm_source=chatgpt.com)

![Image](https://s3-alpha.figma.com/hub/file/2163443664890793915/38a9488f-701c-4c6a-ad1b-bce540c7120e-cover.png?utm_source=chatgpt.com)

![Image](https://cdn.worldvectorlogo.com/logos/enterprise-systems.svg?utm_source=chatgpt.com)

### Placement

**Bottom-right or bottom-center**

```
⚡ Powered by ABS Workstation
LIVE • LOCAL • ENTERPRISE
```

### Rules

* Small
* Semi-transparent
* Never competes with visuals
* No links
* No QR codes

This reinforces brand **without selling**.

---

## 6️⃣ Exit Interaction Wireframe (Critical)

### On ANY input:

* Mouse move
* Key press
* Click
* Touch

**Behavior**

```
[ Immediate fade out 150ms ]
→ Return to previous console view
→ No reload
→ No state loss
```

📌 This must feel *instant* and respectful.

---

## 7️⃣ Motion & Timing Spec (Locked)

| Element             | Duration  |
| ------------------- | --------- |
| Attract entry fade  | 300ms     |
| Metric value change | 240ms     |
| Visual cross-fade   | 600–800ms |
| Exit fade           | ≤150ms    |

**Easing**

* `cubic-bezier(0.4, 0, 0.2, 1)`
* No bounce
* No elastic

---

## 8️⃣ Color & Typography (From Token Set v1.1)

* Background: ABS Black
* Primary accent: Electric Indigo
* Performance highlight: ABS Orange (GPU only)
* Font:

  * Headings / metrics: **Barlow Condensed**
  * Labels: **Rajdhani**
  * Numbers: **Mono**

---

## 9️⃣ CES-Specific Enhancements (Optional)

When `CES_MODE=true`:

* Metrics font +15–20%
* Slower visual rotation
* Orange accent enabled
* Overlay text allowed:

  ```
  LIVE AI • NO CLOUD • RTX PRO 6000
  ```

---

## 🔟 What This Wireframe Achieves

✔ Feels **alive**, not noisy
✔ Clearly shows **real compute**
✔ Respects **enterprise seriousness**
✔ Works from **10 feet away**
✔ Reinforces ABS as **AI pioneer**