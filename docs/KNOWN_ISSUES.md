# KNOWN ISSUES & LIMITATIONS
**Project:** SMARTFLOW ODISHA  
**Date:** 2026-11-12  

---

## 1. Local Pretrained YOLO Model Scope
- **Finding:** The default COCO pretrained YOLOv8 model detects standard vehicle classes (cars, buses, trucks, motorcycles) but does not have a distinct class for Odisha ambulances.
- **Handling:** Ambulance emergency priority tracking uses the dedicated GPS simulation module and TraCI vehicle injector rather than raw video feeds.

## 2. TraCI Single-Client Architecture
- **Finding:** Eclipse SUMO's TraCI server only supports one active client connection per port label by default.
- **Handling:** All FastAPI endpoints delegate simulation requests to `SimulationManager`, which serializes TraCI commands over an async queue to avoid multiple threads attaching simultaneously.

## 3. Large Video Uploads & Memory
- **Finding:** Processing high-resolution video streams concurrently with full SUMO-GUI may strain machines with less than 8 GB RAM.
- **Recommendation:** Run SUMO in headless mode (default in `SimulationManager`) for maximum throughput.
