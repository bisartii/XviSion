---
name: Terra Vision
colors:
  surface: '#0f131c'
  surface-dim: '#0f131c'
  surface-bright: '#353942'
  surface-container-lowest: '#0a0e16'
  surface-container-low: '#181c24'
  surface-container: '#1c2028'
  surface-container-high: '#262a33'
  surface-container-highest: '#31353e'
  on-surface: '#dfe2ee'
  on-surface-variant: '#bcc9cd'
  inverse-surface: '#dfe2ee'
  inverse-on-surface: '#2c3039'
  outline: '#869397'
  outline-variant: '#3d494c'
  surface-tint: '#4cd7f6'
  primary: '#4cd7f6'
  on-primary: '#003640'
  primary-container: '#06b6d4'
  on-primary-container: '#00424f'
  inverse-primary: '#00687a'
  secondary: '#adc6ff'
  on-secondary: '#002e6a'
  secondary-container: '#0566d9'
  on-secondary-container: '#e6ecff'
  tertiary: '#d0bcff'
  on-tertiary: '#3c0091'
  tertiary-container: '#b395ff'
  on-tertiary-container: '#4900ae'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#acedff'
  primary-fixed-dim: '#4cd7f6'
  on-primary-fixed: '#001f26'
  on-primary-fixed-variant: '#004e5c'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#e9ddff'
  tertiary-fixed-dim: '#d0bcff'
  on-tertiary-fixed: '#23005c'
  on-tertiary-fixed-variant: '#5516be'
  background: '#0f131c'
  on-background: '#dfe2ee'
  surface-variant: '#31353e'
typography:
  display-lg:
    fontFamily: Manrope
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Manrope
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Manrope
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.02em
  headline-sm:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: -0.01em
  subheading:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 22px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  telemetry-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  telemetry-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.04em
  badge-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 12px
    letterSpacing: 0.1em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system defines an AI-powered visual intelligence and security operations command environment. The brand personality balances cinematic spatial depth with disciplined, mission-critical utility. It communicates extreme computational fidelity, situational awareness, and executive clarity without resorting to gamified cyberpunk tropes or generic enterprise SaaS flatness.

The visual style synthesizes **Liquid Spatial Glass** with **Precision Instrument Minimalism**:
- **Controlled Translucency:** Optical glass tiers provide situational stacking, retaining situational visual context under floating inspection overlays.
- **Specular Precision:** Razor-thin light bevels and hairline borders (0.5px to 1px) simulate real-world optical glass edge reflections.
- **Instrument Telemetry:** Monospaced data displays, biometric indicators, and HUD-inspired corner brackets emphasize deterministic real-time computation.
- **Restrained Atmosphere:** Deep slate-navy voids punctuated by disciplined, low-emissivity cyan and violet illumination.

## Colors

The system uses a dark-native palette designed to preserve operator night vision, reduce visual fatigue across 12-hour operational shifts, and let spatial alerts cut through instantly.

### Palette Hierarchy

- **Canvas & Voids:**
  - Base Deep Navy: `#06080D` (Application bedrock)
  - Core Surface Slate: `#0B0F17` (Canvas background)
  - Container Navy: `#111726` (Panel foundations)
  - Elevated Graphite: `#161F30` (Nested interactive modules)
- **Glass Transparency Scales:**
  - `Glass Base`: `rgba(16, 24, 39, 0.65)` with `backdrop-filter: blur(24px)` and `border: 1px solid rgba(255, 255, 255, 0.08)`
  - `Glass Elevated / Floating`: `rgba(22, 33, 54, 0.75)` with `backdrop-filter: blur(32px)`, `border: 1px solid rgba(255, 255, 255, 0.14)`, and inner highlight `inset 0 1px 0 rgba(255, 255, 255, 0.12)`
  - `Glass Subdued / Inset`: `rgba(10, 15, 26, 0.50)` with `backdrop-filter: blur(12px)` and `border: 1px solid rgba(255, 255, 255, 0.04)`
- **Accents:**
  - Primary Visual Intelligence: `#06B6D4` (Cyan Glow) / `#22D3EE` (Interactive state)
  - Neural Processing Blue: `#3B82F6` (Electric Royal) / `#60A5FA` (Active focus)
  - Spatial Violet: `#8B5CF6` (Atmospheric depth & model clustering)
- **Status & Diagnostics:**
  - Verified / Nominal Track: `#10B981` (Emerald) with `#059669` (Pulse beacon)
  - Suspect / High Uncertainty: `#F59E0B` (Amber Warning)
  - Threat / Positive Match Alert: `#EF4444` (Crimson Coral)
  - Pipeline Ingest / Inference: `#06B6D4`
- **Text Layers:**
  - High Emphasis: `#F8FAFC` (Pure Titanium White)
  - Secondary Readouts: `#94A3B8` (Cool Slate)
  - Microdata & Muted Grids: `#64748B` (Steel Monospace)

## Typography

The typography architecture uses a dual-purpose strategy:
1. **Manrope** provides contemporary structural authority for viewport titles, biometric profile banners, and camera zone headers.
2. **Geist** delivers neutral legibility across tabular records, event streams, and density-driven audit trails.
3. **JetBrains Mono** powers real-time metrics (FPS, inference ms, neural confidence percentages, GPS coordinates, and frame hashes), preventing layout jitter during high-frequency telemetry updates.

All uppercase badge text must strictly enforce `badge-caps` with high tracking (`letter-spacing: 0.1em`) to ensure legibility on dark glass surfaces under low-light control room environments.

## Layout & Spacing

The layout is built around a persistent, responsive mission-control grid:
- **Structural Blueprint:**
  - Left: Permanent Tool Rail (64px icon-only, expanding to 240px contextual drawer on user toggle).
  - Top: Fixed 56px Global Telemetry Header containing edge health indicators, GPU workload meters, and universal search.
  - Center/Right: Fluid multi-panel visual mosaic adhering to a 12-column dynamic layout. Element cards can span 3, 4, 6, 8, or 12 columns.
- **Rhythm & Padding:**
  - Consistent 8pt coordinate system.
  - Component gaps and viewport padding use `space-md` (16px) or `space-lg` (24px) to preserve breathability between dense live video feeds and target attribute tables.
- **Responsive Adaptations:**
  - **Desktop (>1440px):** Simultaneous multi-feed video matrix (4x4 or 2x2 with deep target drilldown panel).
  - **Tablet (768px - 1439px):** Split-view with collapsable target queue; telemetry collapsed into popover triggers.
  - **Mobile (<768px):** Single-feed focus viewport with swipeable floating bottom drawer for matched faces and live threat notifications.

## Elevation & Depth

Spatial depth is conveyed via chromatic refraction, specular rim lights, and soft occlusion shadowing:

- **Level 0 (Bedrock Canvas):**
  - Dark base `#06080D` layered with two soft ambient radial lights: `radial-gradient(circle at 10% 20%, rgba(6, 182, 212, 0.04) 0%, transparent 40%)` and `radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.04) 0%, transparent 40%)`.
- **Level 1 (Docked Structural Units):**
  - Background: `rgba(16, 24, 39, 0.65)`.
  - Border: 1px solid `rgba(255, 255, 255, 0.08)`.
  - Blur: 20px blur with `backdrop-filter`.
- **Level 2 (Active Panels, Target Dossiers & Video Cards):**
  - Background: `rgba(22, 33, 54, 0.75)`.
  - Edge treatment: 1px solid `rgba(255, 255, 255, 0.14)` with an inner specular line `box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.12)`.
  - Ambient shadow: `0 12px 32px -4px rgba(0, 0, 0, 0.6)`.
- **Level 3 (Modal Alerts, Floating Command Palettes, Target Tooltips):**
  - Background: `rgba(26, 38, 64, 0.88)`.
  - Edge treatment: 1px solid `rgba(34, 211, 238, 0.35)`.
  - Outer glow: `0 0 24px -2px rgba(6, 182, 212, 0.25), 0 20px 48px rgba(0, 0, 0, 0.75)`.

## Shapes

The design uses balanced, modern geometry (`roundedness: 2`):
- Standard interactive elements, panels, and card viewports apply `0.75rem` (12px) to `1rem` (16px) corner radiuses.
- Embedded telemetry badges, live status dots, and pill buttons use full circular rounds (`9999px`).
- Targeting reticles, facial recognition bounding boxes, and camera corner brackets feature sharp 90-degree framing hooks overlaid across rounded media masks to create tactical visual tension.

## Components

### Buttons & Interactive Triggers
- **Primary Cyber Accent:** Cyan gradient surface (`linear-gradient(135deg, #06B6D4, #0891B2)`), white text (`#FFFFFF`), with an inner specular top edge (`inset 0 1px 0 rgba(255, 255, 255, 0.25)`) and hover glow (`box-shadow: 0 0 16px rgba(6, 182, 212, 0.4)`).
- **Secondary Glass Action:** Translucent fill (`rgba(255, 255, 255, 0.05)`), border 1px solid `rgba(255, 255, 255, 0.12)`. On hover: `rgba(255, 255, 255, 0.1)` with slate-100 text.
- **Icon Utility Button:** 36x36px square with 8px radius, glass inset backdrop, centered 18px vector icon.

### Form Inputs & Query Fields
- **Search & Filter Bars:** Subdued glass fill (`rgba(10, 15, 26, 0.55)`), border 1px solid `rgba(255, 255, 255, 0.08)`, text in `#F8FAFC`.
- **Focus State:** Hairline border illuminates to `#22D3EE` with a subtle focus ring (`0 0 0 1px rgba(6, 182, 212, 0.3)`). Monospace shortcut hint (e.g., `⌘K`) pinned right in `#64748B`.

### Live Feeds & Bounding Boxes
- **Camera Viewport:** 12px rounded glass enclosure with 1px top highlight. Overlaid HUD telemetry displays camera node ID, real-time FPS, and stream timestamp in top-left/top-right corners.
- **Biometric Target Box:** Vector bounding reticle tinted according to track state:
  - Cyan (`#06B6D4`) for active tracked subject.
  - Emerald (`#10B981`) for confirmed whitelist match (>98%).
  - Coral (`#EF4444`) for security anomaly or watchlist flag.
- **Reticle Tag:** Anchored pill showing `[NAME / IDENTIFIER] [99.4%]` rendered in JetBrains Mono with 70% opacity blurred background.

### Cards & Telemetry Panels
- **Match Dossier Card:** 14px rounded glass surface with target headshot snapshot (left), biometric metadata vectors (center), and match score gauge ring (right).
- **Metric Micro-Card:** Clean slate background, small uppercase label in `#64748B`, large crisp numeric output in `Manrope` 22px, paired with small delta badge (+2.4%).

### Segmented Glass Controls & Tabs
- Encapsulated pills inside an inset dark trench (`rgba(0, 0, 0, 0.4)`). Active state renders as an elevated frosted glass pill with cyan-tinted active text.