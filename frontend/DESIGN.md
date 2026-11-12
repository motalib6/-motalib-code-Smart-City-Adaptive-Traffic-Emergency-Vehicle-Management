# SMARTFLOW ODISHA — Design System

Derived from the Google Stitch PROMPT 01 brief (implemented directly in code; Stitch needs a Google sign-in in a browser, so no export was available).

## Tokens

| Token | Value | Use |
|---|---|---|
| Background | `#0B1220` | App background |
| Panel | `#111A2E` | Cards |
| Panel 2 | `#16223A` | Nested surfaces, table rows |
| Line / border | `#1E2C47` | Borders, dividers |
| Primary teal | `#15C6B3` | Primary actions, active nav, charts |
| Secondary cyan | `#38BDF8` | Secondary accents, car markers |
| Text primary | `#F1F5F9` | Headings, values |
| Text secondary | `#94A3B8` | Labels, captions |
| Danger | `#F87171` | Emergency, errors, ambulance |
| Amber | `#FBBF24` | Warnings, yellow signal, bus |
| Success | `#34D399` | OK states, green signal |

## Typography

- Font: **Inter** (Google Fonts), system-ui fallback.
- Scale: page titles 18–20px bold; card titles 16px semibold; body 14px; labels 12px uppercase tracking-wide; values 24–32px bold, tabular numerals for timers.

## Components

- **Sidebar** (256px, fixed on desktop, slide-over on mobile), **Topbar** (60px sticky) with connection status.
- **StatCard**: icon chip, label, large value, sub-caption.
- **TrafficSignal**: two 3-lamp stacks (N–S / E–W) + phase name + countdown seconds.
- **JunctionCard / TrafficNetworkMap**: 2×2 SVG network (J1–J4), dashed emergency route J1→J2→J4, colour-coded vehicle dots.
- **CameraPreview**: 16:9 frame with YOLO bounding-box overlays (label + confidence + lane).
- **EventTable**: filter select + CSV export, severity pills.
- **AnalyticsChart**: Recharts line chart, teal/cyan series.

## Accessibility & responsiveness

- Minimum touch target 44px; visible teal focus outline on all interactive elements.
- Contrast: white `#F1F5F9` on `#0B1220` ≈ 15:1; slate `#94A3B8` on panel ≈ 7:1 — above 4.5:1.
- `prefers-reduced-motion` disables vehicle/pulse animations.
- Breakpoints: 375px (single column), 768px (2-col stats), 1024px (sidebar static at lg), 1440px (max content width, 6-col stats). No horizontal scroll: tables scroll inside their card only.
- Icons: Lucide React only; no emoji used as icons.

## Data honesty

- Any fixture shown while the backend is disconnected is labelled **DEMO DATA** with an amber banner.
- Simulated GPS is labelled **SIMULATED GPS**; never presented as live.
- Analytics comparison renders only measured experiment runs from the backend.
