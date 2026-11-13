# SUMO INSTALLATION & ENVIRONMENT REPORT
**Project:** SMARTFLOW ODISHA  
**Platform:** Windows 10/11 x64  
**Date:** 2026-11-12  

---

## 1. Downloaded Package Inspection
- **Location:** `C:\Users\91720\Downloads`
- **Filename:** `sumo-win64extra-1.28.0.msi`
- **File Type:** Windows Installer Package (.msi)
- **Size:** 265,990,906 bytes (~253.6 MB)
- **Version:** Eclipse SUMO 1.28.0

---

## 2. Installation Verification
- **Status:** Already installed on Windows system.
- **Root Directory:** `C:\Program Files (x86)\SUMO`
- **Subdirectories:**
  - `C:\Program Files (x86)\SUMO\bin` (Contains executables and required DLLs)
  - `C:\Program Files (x86)\SUMO\tools` (Contains bundled TraCI and sumolib Python libraries)
  - `C:\Program Files (x86)\SUMO\data` (Typemaps and styles)

---

## 3. Detected Executables & Versions
All core binaries verified via `--version`:

1. **`sumo.exe`:**
   - Path: `C:\Program Files (x86)\SUMO\bin\sumo.exe`
   - Version: `Eclipse SUMO sumo 1.28.0` (Build: Windows AMD64 MSVC Release)
2. **`sumo-gui.exe`:**
   - Path: `C:\Program Files (x86)\SUMO\bin\sumo-gui.exe`
   - Version: `Eclipse SUMO GUI 1.28.0`
3. **`netgenerate.exe`:**
   - Path: `C:\Program Files (x86)\SUMO\bin\netgenerate.exe`
   - Version: `Eclipse SUMO netgenerate 1.28.0`

---

## 4. Environment Variables Configuration
To ensure permanent, non-destructive configuration:
- **`SUMO_HOME` (User registry):** `C:\Program Files (x86)\SUMO` (set safely via .NET API without touching system PATH).
- **`SUMO_HOME` (System registry):** `C:\Program Files (x86)\SUMO\`
- **Path configuration:** Safe from PATH clobbering; backend also supports direct path resolution via `.env`.

---

## 5. Python TraCI & sumolib Verification
Verified inside backend virtual environment `smartflow-odisha/backend/.venv`:
- **TraCI Path:** `C:\Program Files (x86)\SUMO\tools\traci\__init__.py`
- **sumolib Path:** `C:\Program Files (x86)\SUMO\tools\sumolib\__init__.py`
- **Version Matching:** Bundled with Eclipse SUMO 1.28.0, preventing version drift or network protocol mismatches.
- **Import Status:** 100% verified importable and functional.

---

## 6. Backend Integration Configuration
Configured in `smartflow-odisha/backend/.env`:
```env
SUMO_HOME="C:\Program Files (x86)\SUMO"
SUMO_BINARY="C:\Program Files (x86)\SUMO\bin\sumo.exe"
SUMO_GUI_BINARY="C:\Program Files (x86)\SUMO\bin\sumo-gui.exe"
SUMO_CONFIG="simulation/sumo/config/smartflow.sumocfg"

SIMULATION_MODE=sumo
SUMO_GUI_ENABLED=true
```
Matching placeholder entries updated in `smartflow-odisha/backend/.env.example`.
