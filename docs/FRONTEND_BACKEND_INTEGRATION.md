# FRONTEND & BACKEND INTEGRATION REPORT
**Project:** SMARTFLOW ODISHA  
**Stack:** React 19 + Vite 8.3 + TypeScript, FastAPI + SQLModel, Eclipse SUMO 1.28.0  
**Date:** 2026-11-12  

---

## 1. Connected Data Flows

### A. Dashboard (`/`)
- **Telemetry Source:** Real-time data from SUMO via `/api/v1/telemetry/metrics` and WebSocket `/ws/telemetry`.
- **Vehicle Count & Speeds:** Extracted directly from SUMO vehicle IDs without synthetic generators.
- **Signal States:** Active signal phase for J1–J4 displayed with true NEMA transitions.
- **Waiting Times & Queues:** Extracted from TraCI lane statistics.

### B. Live Network Map (`/network`)
- **Road & Node Mapping:** Mapped to SUMO network coordinates for Rasulgarh (J1), Vani Vihar (J2), Master Canteen (J3), and Khandagiri (J4).
- **Live Positions:** Real-time $(x, y)$ coordinate plotting of SUMO vehicles.

### C. Junction Control (`/junctions`)
- **Phase Status:** Green/Yellow/Red live indicators for each approach (N, S, E, W).
- **Adaptive Control:** Signal timing dynamically responsive to approach densities.

### D. Emergency Response (`/emergency`)
- **Ambulance Tracking:** Displayed with simulation corridor priority status.
- **Preemption Wave:** Automated Yellow -> All-Red -> Green corridor sequence.

### E. WebSocket Service (`src/services/websocket.ts`)
- **Endpoint:** `ws://127.0.0.1:8000/ws/telemetry`
- **Resilience:** Automatic reconnection with exponential backoff.
- **Deduplication:** Frame hashing to eliminate redundant re-renders.

---

## 2. Permissions & RBAC
- **ADMIN / OPERATOR:** Can start, pause, reset simulation, inject traffic, and trigger emergency priority.
- **VIEWER:** Read-only access to dashboard, live network, and telemetry logs.

---

## 3. Verification & Build Status
- **Frontend Build (`npm run build`):** Passed with 0 errors. PWA service worker generated cleanly.
- **Backend Smoke Test:** Full end-to-end cycle (Login -> Sim Start -> Telemetry -> Junctions -> WebSocket -> Pause -> Reset) passed.
