# SMARTFLOW ODISHA — Google Stitch prompts (paste-ready)

User will sign in to Google Stitch themselves — Muse cannot sign in as the user.
Steps for the user:
1. Open https://stitch.withgoogle.com/ and sign in with Google.
2. New project: `SMARTFLOW ODISHA — Intelligent Traffic Management`.
3. Paste PROMPT 01 below, generate, check all 8 screens.
4. Then paste PROMPT 02 to refine.
5. Export / download the generated code into `frontend/` (or keep the React code
   already built in this repo — it implements the same 8 screens and design tokens).

Design identity (do not change): dark navy background #0B1220, primary teal #15C6B3,
secondary cyan #38BDF8, white text, slate secondary text, Inter typography,
desktop-first control-room dashboard. Sample data must be labelled simulation/demo data.

## PROMPT 01 — Full application UI

```
Act as a world-class senior UI/UX designer specializing in intelligent transportation systems.

Design a premium, complete web application called:

SMARTFLOW ODISHA

Subtitle:
Smart City – Adaptive Traffic & Emergency Vehicle Management.

Purpose:
An AI-assisted traffic management prototype that detects vehicles from video, estimates traffic density, adapts traffic signals, safely prioritizes ambulances and coordinates connected junctions.

This is for GEC HACKATHON 2026 — Problem Statement 03.

DESIGN IDENTITY:

- Professional intelligent city control room.
- Dark navy background #0B1220.
- Primary teal #15C6B3.
- Secondary cyan #38BDF8.
- White text and slate secondary text.
- Premium modern typography.
- Clear information hierarchy.
- High-quality traffic illustrations.
- Clean charts and readable statistics.
- Responsive desktop-first design.
- Avoid generic admin dashboard templates.

CREATE THESE 8 COMPLETE SCREENS:

SCREEN 1 — LOGIN
- SMARTFLOW ODISHA branding.
- Admin, operator and viewer login experience.
- Secure login form.
- Connection status.

SCREEN 2 — COMMAND DASHBOARD
- Total simulated vehicles.
- Active intersections.
- Average vehicle waiting time.
- Congestion status.
- Active emergencies.
- Live density graph.
- Connected junction status.
- Recent system events.
- Camera connection and simulation mode indicators.

SCREEN 3 — LIVE TRAFFIC NETWORK
- Large connected network visualization.
- Four intersections: J1, J2, J3, J4.
- North, South, East and West approaches.
- Animated cars, buses, motorcycles and ambulance.
- Four-way signal visualization.
- Vehicle counts per lane.
- Queue lengths.
- Current phase and countdown.
- Start, pause, reset buttons.
- Normal, rush-hour and heavy-traffic scenarios.

SCREEN 4 — AI CAMERA MONITORING
- Local camera/video input panel.
- Video upload control.
- Camera connection status.
- YOLO detection boxes.
- Class-wise vehicle detection counts.
- Lane-wise traffic density.
- Detection confidence.
- Processed frame preview.
- Data source status.

SCREEN 5 — ADAPTIVE JUNCTION CONTROL
- Select J1, J2, J3 or J4.
- Current signal phase.
- Traffic demand by approach.
- Recommended green duration.
- Actual green duration.
- Yellow countdown.
- All-red countdown.
- Signal history.
- AI decision explanation.

SCREEN 6 — EMERGENCY VEHICLE MANAGEMENT
- Ambulance ID.
- Emergency request creation.
- Current junction.
- Destination.
- Route path.
- GPS-like location updates.
- Estimated arrival time.
- Priority status.
- Next junction preparation.
- Emergency completion status.
- Emergency event timeline.

SCREEN 7 — ANALYTICS AND EVENTS
- Average waiting time.
- Traffic throughput.
- Congestion history.
- Emergency response duration.
- Fixed-time vs adaptive comparison.
- Signal transition logs.
- Event filtering.
- CSV export.
- Simulation run history.

SCREEN 8 — ADMINISTRATION
- User and role management.
- Signal safety configuration.
- Junction configuration.
- Minimum and maximum green duration.
- Yellow and all-red durations.
- Simulation configurations.
- Security settings.

INTERACTIONS:

Create working screen navigation.
Buttons should have clear intended actions.
Use sample data only for the initial UI preview.
Label all sample data as simulation/demo data.
Do not show invented performance improvements.

GLOBAL DESIGN:
Create a professional left sidebar, a clean top navigation,
responsive cards, consistent spacing and reusable components.

This UI must be ready for React + TypeScript + FastAPI integration.

The UI should look like a real intelligent transportation management product, not a basic college project.
```

## PROMPT 02 — Improve the Stitch UI

```
Review the complete SMARTFLOW ODISHA design you just created.

Do not remove or change the project identity.

Improve the following:

1. Make the traffic map the main visual focus.
2. Show four connected working junctions.
3. Make vehicles and traffic signals easy to understand.
4. Highlight ambulance emergency routes in a distinctive color.
5. Show signal transitions clearly.
6. Make YOLO bounding boxes visually realistic.
7. Create consistent UI components.
8. Improve typography and spacing.
9. Improve desktop responsiveness.
10. Ensure all 8 screens have consistent navigation.

Create a reusable design system.

Export a DESIGN.md file describing:
- Colors.
- Fonts.
- Typography.
- Spacing.
- Buttons.
- Cards.
- Navigation.
- Charts.
- Signal indicators.
- Status indicators.

Keep data placeholders visibly marked as sample simulation data.

Prepare the project for development in Google Antigravity.
```
