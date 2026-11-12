# SMARTFLOW ODISHA — Frontend

React + TypeScript + Vite dashboard for the GEC Hackathon 2026 (PS-03) Intelligent Traffic & Emergency Management prototype.

## Run

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # production build
```

Backend (FastAPI) expected at `http://127.0.0.1:8000` — see `.env.example`.
Copy `.env.example` to `.env` to change `VITE_API_BASE_URL` / `VITE_WS_URL`.

## Routes

/login · /dashboard · /live-network · /camera · /junctions · /emergency · /analytics · /events · /admin

## Notes

- No Stitch export exists: Google Stitch requires the user's Google sign-in in a browser, so the 8 screens from Stitch PROMPT 01 were implemented directly in code, following the same design brief.
- When the backend is not running, pages show clearly labelled **DEMO DATA** preview fixtures — never presented as real traffic.
- YOLOv8 (COCO) has no ambulance class; emergency priority uses the separate simulated-GPS module.
- Fixed vs adaptive comparison shows only measured backend experiment runs; no invented percentages.
