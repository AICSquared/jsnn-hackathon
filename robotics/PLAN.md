# Plan: Challenge 3, Robotics that Responds

**Goal:** connect live Pioreactor optical density (OD) readings to a myCobot 320 arm, so the arm moves when OD crosses a threshold.
**Where:** this repo, folder `robotics/`, next to `digital-twin/` and `biofilm/`. The same workflow applies: issue → branch → PR, and a board post on every commit.
**Time budget:** 1 hour. **Complexity:** Medium. The software is small; the risk is in the hardware.
**Owners:** split into two independent tracks (below). Hardware details are unknown, so the plan covers every case.

## 1. The challenge in brief

### Five objectives (each earns bonus credit on its own)
1. **Assemble and set up the Pioreactor** (hardware assembly + software setup guide).
2. **Connect to the Pioreactor API:** find the running experiment and retrieve its data.
3. **Display live OD:** a stream of timestamped OD readings.
4. **Connect and control the myCobot 320:** a predefined test movement.
5. **Make the arm respond to OD:** pick an OD threshold, and have crossing it trigger the arm.

### Scoring
- Bonus credit per demonstrated milestone, **including assembly and setup**.
- **Partial credit for working components and documented progress**, so we document every step as we go even if we never reach the arm.
- **Repeatability breaks ties**: the same OD crossing must give the same arm response every time.

### Deliverables (our choice)
- **`robotics/robotics.ipynb`**: one notebook that runs anywhere, in Colab, on our laptop or on a judge's computer:
  - live OD stream (objectives 2–3) from the API;
  - arm section that drives the **real arm** when one is connected and otherwise runs in **dry-run mode** (prints and draws each move), so it still runs on a judge's machine;
  - an evidence log: photos and short videos of assembly, setup, and the arm moving.
- A Colab notebook can't reach an arm plugged into our laptop, so the live arm demo runs the **same notebook locally** on the laptop next to the arm.

### Data and API (read from the Pioreactor source, v. Nov 4 2026)
| Call | Returns |
|---|---|
| `GET https://api.environnets.com/api/experiments/latest` | the running experiment: `{experiment, created_at, …}` |
| `GET /api/experiments` | all experiments, newest first |
| `GET /api/experiments/{experiment}/time_series/od_readings?lookback=2` | the last 2 hours of raw OD for every unit and channel: series labels plus lists of points (timestamp, value) |

- No authentication in the code we read.
- **Status at planning time: the live URL returns Cloudflare error 1033**, which means the tunnel to the Pioreactor is down: the reactor is off or not set up yet. It may be the very reactor we assemble. The notebook therefore has a **replay mode**: it records readings whenever the API is up and replays them when it isn't.
- **Verify the moment the API is up:** the exact JSON keys (`series`/`data`, and `x` or `timestamp` with `y`).

### myCobot 320 (via the `pymycobot` package; verify on the hardware)
| Version | How it connects | Python |
|---|---|---|
| **320 M5** | USB cable to the laptop | `MyCobot320("/dev/tty.usbserial-…", 115200)` |
| **320 Pi** | its own Raspberry Pi; WiFi or Ethernet | `MyCobotSocket("<arm ip>", 9000)`, after starting the socket server on the arm |

Core calls: `power_on()`, `send_angles([j1…j6], speed)`, `get_angles()`, `is_moving()`, `release_all_servos()`.

## 2. The split: two tracks, no shared files

The tracks meet at **one function signature** only, so neither waits for the other:

```python
def latest_od(experiment) -> tuple[str, float] | None:   # (ISO timestamp, OD value) of the newest reading
```

The arm track develops against a **fake OD source** that steps from low to high, and switches to `latest_od` at the end.

| Track | Objectives | Owner (proposed) | Files (each person edits only their own) |
|---|---|---|---|
| **A: Reactor + data** | 1, 2, 3 | **Brandon** (free now that biofilm is done) | `robotics/od.py`, `robotics/evidence/reactor/` |
| **B: Arm** | 4, 5 | **Alex** | `robotics/arm.py`, `robotics/evidence/arm/` |
| Shared (built last, together) | — | Alex | `robotics/build_notebook.py` (joins `od.py` then `arm.py` into `robotics.ipynb`), `robotics/PROGRESS.md` |

Both `.py` files are percent-format notebook source (`# %%` cells), the same pattern as `digital-twin/`. Each person commits only their own file, so there are no merge conflicts.

**Dependency:** only objective 5 needs both tracks. Objectives 1–4 are fully independent.

## 3. What each track builds

### Track A: reactor and live OD (Brandon)
1. **Assemble** the Pioreactor from the hardware guide, and **photograph each stage** (credit for assembly).
2. **Software setup:** flash the SD card, connect WiFi, open the web UI, start an experiment with OD reading. Screenshot it.
3. In `od.py`: `get_latest_experiment()`, `latest_od(experiment)`, and `stream_od(seconds, every=5)`, which prints a timestamped table and updates a live plot. Add a **record/replay** fallback: save every reading to `robotics/evidence/od_log.csv`, and replay it if the API fails.
4. Point it at the organisers' API (or our own reactor's address), capture a minute of live readings, and commit the log.

### Track B: arm and response (Alex)
1. In `arm.py`: `connect_arm()` tries USB (M5), then socket (Pi), then falls back to **dry-run**, which prints each command and draws a 2D stick figure of the joint angles.
2. **Test movement (objective 4):** home → wave (joint 1 ±30°) → home, at a fixed speed, waiting until each move finishes.
3. **Response (objective 5):** a polling loop with a **threshold and hysteresis**. The arm triggers once when OD rises above `THRESHOLD` and re-arms only when OD drops below `THRESHOLD − margin`. That gives one move per crossing and stops jitter from triggering repeatedly (repeatability). Each trigger is logged with timestamp, OD and pose.
4. **Choosing the threshold:** just above the current OD (e.g. latest + 0.02) for a live demo, or a value from the recorded log, documented in the notebook.

## 4. Time budget (60 min)

| Time | Track A (Brandon) | Track B (Alex) |
|---|---|---|
| 0:00–0:05 | Confirm split on the board; create branch `<issue>-robotics-od` | Create branch `<issue>-robotics-arm`; finish the Digital Twin Colab check |
| 0:05–0:30 | **Assemble + set up the Pioreactor** (photos). Agent writes `od.py` in parallel | Agent writes `arm.py` with dry-run + fake OD; **identify the arm version** when you reach it |
| 0:30–0:45 | Live API: experiment, OD stream, record log | Real arm: test movement (objective 4), video |
| 0:45–0:52 | Hand `latest_od` over (it's already in `od.py`) | Wire the response loop to live or replayed OD; demo the trigger 3 times (repeatability), video |
| 0:52–1:00 | Build `robotics.ipynb` together; run it in dry-run mode; write `PROGRESS.md`; commit; post on the board; update README |  |

**Cut lines:**
- No arm by 0:45: demo objective 5 in **dry-run** (documented, partial credit) and record what blocked us.
- Pioreactor not assembled by 0:30: keep documenting assembly, and use the **organisers' API** for objectives 2–3 if it comes up.
- API still down: use **replay** of any reading we captured. If we have none, say so plainly in `PROGRESS.md`.

## 5. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Live API tunnel down (it is right now) | High | Replay mode; check every few minutes; ask the organisers which reactor it serves |
| Arm version unknown (M5 USB vs Pi socket) | High | `connect_arm()` tries both, then dry-run |
| USB serial driver missing on the Mac (CP210x/CH34x) | Medium | Install the driver first; or use the Pi version over WiFi |
| Arm moves unsafely (collision with the table or reactor) | Medium | Small joint moves only, low speed (≤ 30), test poses with the arm clear of objects; a human near the power switch |
| OD barely changes in 1 hour (growth is slow) | High | Threshold just above the current value; or demonstrate with the replay log's rise |
| Running out of time before the arm | High | Track A milestones and documentation count on their own |

## 6. Acceptance
- [ ] Assembly and setup photographed (objective 1)
- [ ] Experiment found and OD retrieved from the API (objective 2)
- [ ] Live timestamped OD stream shown in the notebook (objective 3)
- [ ] Arm test movement on video, or dry-run if there's no arm (objective 4)
- [ ] Threshold trigger demonstrated 3× the same way (objective 5 + repeatability)
- [ ] `robotics.ipynb` runs on a judge's machine (dry-run + replay without hardware)
- [ ] `PROGRESS.md` lists each milestone with time and evidence
- [ ] README updated with the robotics row, folder map and run steps

## 7. Open questions
1. Is `api.environnets.com` the organisers' reactor, or the one we assemble?
2. Which arm version (M5 or Pi) is at our station?
3. Do judges want the live demo in person, video evidence, or both?
