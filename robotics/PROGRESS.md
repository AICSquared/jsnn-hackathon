# Robotics that Responds: progress and evidence

Team: Alex Williams (arm) and Brandon Townsend (reactor + OD data). Times are local (ET), Nov 7, 2026.
Hardware: the organisers' Pioreactor cluster (leader `oliveirapioreactor01`, worker `oliveirapioreactor02`) and a myCobot 320 Pi arm.

| # | Objective | Status | Evidence |
|---|---|---|---|
| 1 | Assemble and set up the Pioreactor | ✅ Assembled and powered on. The SD card came pre-flashed (hostname `oliveirapioreactor02`, a worker). We found it on the network at 192.168.8.229, discovered it needs its leader (`oliveirapioreactor01`), and powered the leader on at 192.168.8.230 | Photos: [`03-assembled_reactor.jpg`](evidence/reactor/03-assembled_reactor.jpg) (Pioreactor 20 ml on its Raspberry Pi), [`08-vial.jpg`](evidence/reactor/08-vial.jpg). Screenshots: `evidence/pioreactorSETTINGS.png`, `pioreactorOD_OFF.png` |
| 2 | Connect to the API, find the experiment, retrieve data | ✅ `od.py` finds experiment `bioreactor_robot` via `/api/experiments/latest` and pulls `/time_series/od_readings` (series `oliveirapioreactor01-2`) | `evidence/reactor/od_log.csv` (every reading fetched) |
| 3 | Display live, timestamped OD | ✅ OD reading started in the UI. A new reading every 5 s, OD ≈ 0.0048, streamed and plotted in the notebook (live table and chart in `robotics.ipynb`, 20:00 ET run). Handles the leader's wrong clock (it reads 2025-10-01) by taking the newest point at or before the leader's own time | `robotics.ipynb` (Part A stream), `od_log.csv` (214 live rows from today; the rest are an earlier run), screenshot [`pioreactorOD_ON.png`](evidence/pioreactorOD_ON.png) |
| 4 | Connect and control the myCobot 320 | ✅ Official `Server_320.py` on the arm's Pi, port 9000. `MyCobot320Socket` from the laptop. Test movement (base ±20°, wrist ±20°, back to start) at 30% speed: every pose reached within about 1° | `evidence/arm/obj4_test_movement_real_arm.ipynb` (table of target vs reached angles), video [`obj4_obj5_timelapse_test_movement_and_vial_trigger.mp4`](evidence/arm/obj4_obj5_timelapse_test_movement_and_vial_trigger.mp4), photo [`obj4_arm_with_gripper.jpg`](evidence/arm/obj4_arm_with_gripper.jpg), arm server [`sshwindow.png`](evidence/sshwindow.png) |
| 5 | Arm responds to an OD threshold | ✅ Threshold = live baseline + 4 sd (minimum +0.0002), hysteresis re-arm below it, one move per crossing. **Run 1 (cell-medium vial):** baseline 0.00498, threshold 0.00518. Inserting the vial drove OD to 0.031 → arm responded. OD stayed high with no re-fire, re-armed at 0.00504, then a second insertion to 0.055 → responded again. **2 crossings → exactly 2 responses.** **Run 2 (denser vial):** OD 0.00498 → 0.30–0.39 → responded once, no re-fire while high. (Run 0 crashed on a −1 reply from the arm, which was fixed by retrying angle reads.) | `evidence/arm/obj5_run1_cell_medium_vial.txt` and `_trigger_log.csv`, `obj5_run2_dense_vial.txt` and `_trigger_log.csv`, `obj5_run0_crashed_before_fix.txt`, video [`obj4_obj5_timelapse_test_movement_and_vial_trigger.mp4`](evidence/arm/obj4_obj5_timelapse_test_movement_and_vial_trigger.mp4) |

## Repeatability (the tie-breaker)
- All arm moves are relative to the arm's current pose, at a fixed speed, waiting until each move finishes, so the same command gives the same motion every run.
- The trigger is a hysteresis switch: noise around the threshold can't re-fire it, and each upward crossing gives exactly one response (self-check: 2 crossings in noisy data → exactly 2 triggers).
- Every trigger is logged with time, OD, threshold and the pose reached.

## Problems we hit and solved
- **Live API down (Cloudflare 1033/530):** the reactor behind `api.environnets.com` was off. We read the API routes from the Pioreactor open-source code and built record/replay so work could continue offline.
- **"Not the leader":** our reactor was a cluster worker; its config named `oliveirapioreactor01` as leader. Powering that unit on brought the public API up.
- **Stale "newest" reading:** the leader's clock reads 2025-10-01, so new readings sorted before this morning's. Fixed by using the leader's own clock (`/unit_api/health`).
- **Arm connection:** the arm's Pi had an older pymycobot without `Server_320.py`; we fetched the official script. We avoided a 92° swing to an absolute zero pose by making all moves relative.
