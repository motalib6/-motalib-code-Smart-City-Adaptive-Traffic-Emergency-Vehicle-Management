# SUMO NETWORK STATUS REPORT
**Project:** SMARTFLOW ODISHA  
**Network File:** `simulation/sumo/network/smartflow.net.xml`  
**Configuration File:** `simulation/sumo/config/smartflow.sumocfg`  
**Date:** 2026-11-12  

---

## 1. Network Topology (2x2 Controlled Grid)
Generated using SUMO `netgenerate --grid --grid.x-number=2 --grid.y-number=2 --grid.x-length=300 --grid.y-length=300 --grid.attach-length=150`:
- **Total Junctions:** 12 (4 controlled internal junctions + 8 boundary attach nodes)
- **Lanes:** 2 lanes per approach (N, S, E, W)
- **Controlled Intersections:** 4

---

## 2. Verified Junction & Traffic Light IDs
All 4 internal intersections are fully controlled with individual static/adaptive traffic light logic:

| App Label | SUMO Junction ID | SUMO TLS ID | Grid Coordinate (m) | Location in Bhubaneswar | Approaches |
|---|---|---|---|---|---|
| **J1** | `A0` | `A0` | (150.0, 150.0) | **Rasulgarh** | `A1A0`, `B0A0`, `bottom0A0`, `left0A0` |
| **J2** | `A1` | `A1` | (150.0, 450.0) | **Vani Vihar** | `A0A1`, `B1A1`, `left1A1`, `top0A1` |
| **J3** | `B0` | `B0` | (450.0, 150.0) | **Master Canteen** | `A0B0`, `B1B0`, `bottom1B0`, `right0B0` |
| **J4** | `B1` | `B1` | (450.0, 450.0) | **Khandagiri** | `A1B1`, `B0B1`, `right1B1`, `top1B1` |

---

## 3. Signal Programs
Each junction has 4 phases defined in `tlLogic`:
- Phase 0: North-South Green (`G`), East-West Red (`r`)
- Phase 1: North-South Yellow (`y`), East-West Red (`r`)
- Phase 2: North-South Red (`r`), East-West Green (`G`)
- Phase 3: North-South Red (`r`), East-West Yellow (`y`)

---

## 4. Vehicle Classes & Fleet
Defined in `routes/vehicles.add.xml` and loaded in routes:
- `car` (Passenger vehicles)
- `motorcycle` (Two-wheelers)
- `bus` (Public transport)
- `truck` (Heavy logistics)
- `ambulance` (Emergency response vehicle with priority shape and siren status)

---

## 5. Test Evidence
- **XML Validation:** Passed (4 traffic light junctions detected, 4 tlLogics validated).
- **Headless Run:** `sumo -c smartflow.sumocfg --end 10` executed cleanly with 0 errors.
- **TraCI Control:** `traci.simulationStep()` verified with live vehicle tracking and phase transitions.
