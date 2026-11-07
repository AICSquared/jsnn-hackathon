# %% [markdown]
# ## Part B: the myCobot 320 arm responds to optical density
#
# **Objectives 4 and 5.** Connect to the arm, run a predefined test movement, then make the arm move when the
# live optical density (OD) of the culture crosses a threshold.
#
# **Runs anywhere.** If no arm is connected (in Colab, or on a judge's laptop) the notebook switches to
# **dry-run mode**: it prints every command it would send and draws the arm's pose, so every step can still be
# checked. On the laptop that is plugged into the arm, the same cells drive the real robot.

# %%
import importlib.util, subprocess, sys, os, glob, time, math
from datetime import datetime, timezone
from pathlib import Path

if importlib.util.find_spec("pymycobot") is None:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pymycobot"], check=True)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

ROBOTICS_DIR = Path(".") if Path("PLAN.md").exists() else Path("robotics") if Path("robotics/PLAN.md").exists() else Path(".")
EVIDENCE = ROBOTICS_DIR / "evidence" / "arm"
EVIDENCE.mkdir(parents=True, exist_ok=True)

# Where the arm is. Leave as None to auto-detect; set ARM_PORT (USB, "M5" version) or ARM_IP (WiFi, "Pi" version).
ARM_PORT = os.environ.get("ARM_PORT")          # e.g. "/dev/tty.usbserial-0001" (Mac) or "COM3" (Windows)
ARM_IP = os.environ.get("ARM_IP")              # e.g. "192.168.1.42": on the arm's Pi run Server_320.py first
# Server_320.py (official, Elephant Robotics): https://raw.githubusercontent.com/elephantrobotics/pymycobot/main/demo/Server_320.py
# It listens on the Pi's WiFi address, port 9000. Or run this notebook ON the arm's Pi: it then uses /dev/ttyAMA0.
SPEED = 30                                     # percent of max speed: slow and safe

# %% [markdown]
# ### Connect: real arm if we can find one, otherwise dry-run
# The myCobot 320 comes in two versions. The **M5** version plugs into the laptop by USB (a serial port).
# The **Pi** version has its own small computer and is reached over the network (port 9000).
# We try both, and fall back to a stand-in "dry-run" arm with the same commands.

# %%
class DryRunArm:
    """Same commands as the real arm; records poses instead of moving motors."""
    name = "dry-run (no arm connected)"

    def __init__(self):
        self.angles = [0.0] * 6
        self.history = []

    def power_on(self):
        print("[dry-run] power_on")

    def send_angles(self, angles, speed, _async=False):
        print(f"[dry-run] send_angles({[round(a, 1) for a in angles]}, speed={speed})")
        self.angles = list(map(float, angles))
        self.history.append(list(self.angles))

    def get_angles(self):
        return list(self.angles)

    def is_moving(self):
        return 0

    def release_all_servos(self):
        print("[dry-run] release_all_servos")


def candidate_ports():
    pats = ["/dev/tty.usbserial*", "/dev/tty.SLAB_USBtoUART*", "/dev/tty.wchusbserial*",
            "/dev/cu.usbserial*", "/dev/ttyUSB*", "/dev/ttyACM*"]
    return sorted({p for pat in pats for p in glob.glob(pat)})


def connect_arm():
    from pymycobot import MyCobot320, MyCobot320Socket
    tries = []
    # Running ON the arm's own Raspberry Pi (myCobot 320 Pi): the motors are on /dev/ttyAMA0 at 115200 baud.
    if not ARM_PORT and not ARM_IP and os.path.exists("/dev/ttyAMA0"):
        for baud in (115200, 1000000):
            try:
                arm = MyCobot320("/dev/ttyAMA0", baud)
                arm.power_on()
                time.sleep(0.5)
                if arm.get_angles():
                    arm.name = f"myCobot 320 Pi (on-board, /dev/ttyAMA0 @ {baud})"
                    return arm
                tries.append(f"/dev/ttyAMA0 @ {baud}: no answer")
            except Exception as e:
                tries.append(f"/dev/ttyAMA0 @ {baud}: {e}")
    for port in ([ARM_PORT] if ARM_PORT else candidate_ports()):
        try:
            arm = MyCobot320(port, 115200)
            arm.power_on()
            time.sleep(0.5)
            if arm.get_angles():                       # the arm answered
                arm.name = f"myCobot 320 M5 on {port}"
                return arm
            tries.append(f"{port}: no answer")
        except Exception as e:
            tries.append(f"{port}: {e}")
    if ARM_IP:
        try:
            arm = MyCobot320Socket(ARM_IP, 9000)
            arm.power_on()
            time.sleep(0.5)
            if arm.get_angles():
                arm.name = f"myCobot 320 Pi at {ARM_IP}"
                return arm
            tries.append(f"{ARM_IP}: no answer")
        except Exception as e:
            tries.append(f"{ARM_IP}: {e}")
    for t in tries:
        print("  tried", t)
    return DryRunArm()


arm = connect_arm()
print("Arm:", arm.name)

# %% [markdown]
# ### Objective 4: a predefined test movement
# Small joint moves at low speed, waiting for each move to finish before the next. **Every move is relative to
# the pose the arm is already in** (no big swing to an absolute "zero" pose): turn the base left → right,
# lift and lower the wrist, then return to the starting pose. Every pose is checked by reading the angles back.

# %%
def read_angles(arm, fallback=None, tries=5):
    """The arm's 6 joint angles. Over the network it sometimes answers -1 instead of a list, so retry."""
    for _ in range(tries):
        try:
            a = arm.get_angles()
            if isinstance(a, (list, tuple)) and len(a) == 6:
                return list(a)
        except Exception:
            pass
        time.sleep(0.2)
    return list(fallback) if fallback is not None else [float("nan")] * 6


STEP = 20                                              # degrees per nudge: small and safe
HOME = [round(a, 1) for a in read_angles(arm, fallback=[0.0] * 6)]   # where the arm is right now
print("starting pose:", HOME)


def nudge(joint, delta):
    pose = list(HOME)
    pose[joint] += delta
    return pose


TEST_MOVES = [
    ("start", HOME),
    ("base left", nudge(0, +STEP)),
    ("base right", nudge(0, -STEP)),
    ("wrist up", nudge(3, +STEP)),
    ("wrist down", nudge(3, -STEP)),
    ("start", HOME),
]


def move(arm, angles, speed=SPEED, timeout=15.0):
    """Send a pose and wait until the arm stops (or the timeout passes). Returns the angles read back."""
    arm.send_angles(angles, speed)
    t0 = time.time()
    time.sleep(0.3)
    while time.time() - t0 < timeout:
        try:
            if arm.is_moving() == 0:          # 1 = moving, 0 = stopped, -1 = no answer (keep waiting)
                break
        except Exception:
            pass
        time.sleep(0.2)
    return read_angles(arm, fallback=angles)



def draw_pose(ax, angles, title=""):
    """Side view of a simplified arm (joints 2, 3, 4 bend in the vertical plane) plus base rotation as text."""
    links = [0.135, 0.12, 0.10, 0.06]                     # approximate link lengths (m)
    x, y, a = [0.0], [0.0], math.pi / 2
    for L, j in zip(links, [0, angles[1], angles[2], angles[3]]):
        a += math.radians(j)
        x.append(x[-1] + L * math.cos(a)); y.append(y[-1] + L * math.sin(a))
    ax.plot(x, y, "-o", lw=4, color="#4a6fa5", mfc="white")
    ax.set(xlim=(-0.4, 0.4), ylim=(-0.05, 0.45), aspect="equal", title=title)
    ax.text(-0.38, 0.41, f"base {angles[0]:+.0f}°", fontsize=8)
    ax.set_xticks([]); ax.set_yticks([])


test_log = []
for label, pose in TEST_MOVES:
    reached = move(arm, pose)
    test_log.append(dict(step=label, target=pose, reached=[round(a, 1) for a in reached]))
display(pd.DataFrame(test_log))

fig, axes = plt.subplots(1, len(TEST_MOVES), figsize=(2.2 * len(TEST_MOVES), 2.4))
for ax, (label, pose) in zip(axes, TEST_MOVES):
    draw_pose(ax, pose, label)
plt.suptitle(f"Test movement ({arm.name})", fontsize=10); plt.tight_layout(); plt.show()

# %% [markdown]
# ### Objective 5: respond to an OD reading
#
# **The rule.** When the OD rises **above the threshold**, the arm performs one response movement (a "nod").
# It then **re-arms only after OD falls back below `threshold − margin`**. This *hysteresis* means noise around
# the threshold can't make the arm fire over and over: **one crossing gives exactly one movement**, every time.
# That makes the response repeatable, which is the tie-breaker in scoring.
#
# **OD source.** The live reading comes from `latest_od()` in Part A (Pioreactor API). If Part A isn't loaded
# or the API is down, a recorded or simulated OD series is used instead, and the notebook says which.

# %%
class ThresholdTrigger:
    def __init__(self, threshold, margin):
        self.threshold, self.margin, self.armed = threshold, margin, True

    def update(self, od):
        """Return True exactly once per upward crossing of the threshold."""
        if self.armed and od > self.threshold:
            self.armed = False
            return True
        if not self.armed and od < self.threshold - self.margin:
            self.armed = True
        return False


# Self-check: noisy OD that crosses the threshold twice must fire exactly twice.
rng = np.random.default_rng(0)
test_series = np.concatenate([np.linspace(0.10, 0.30, 40), np.linspace(0.30, 0.10, 40)] * 2) + rng.normal(0, 0.01, 160)
trig = ThresholdTrigger(0.20, 0.03)
fires = [i for i, v in enumerate(test_series) if trig.update(v)]
assert len(fires) == 2, fires
print(f"self-check passed: 2 crossings in noisy data → {len(fires)} triggers (at samples {fires})")

RESPONSE = [("nod down", nudge(3, -STEP)), ("nod up", nudge(3, +STEP)), ("back to start", HOME)]


def respond(arm):
    for _, pose in RESPONSE:
        move(arm, pose)
    return arm.get_angles()


# %% [markdown]
# ### Optional: higher OD → a joint further down the arm (opt-in with `OD_LEVELS`)
#
# By default the arm makes one "nod" at a single threshold (above). Setting `OD_LEVELS=preset` instead gives
# five OD levels, each moving **one joint by 15°** and back. The lowest level moves the wrist, and each higher
# level moves a joint closer to the base, so a denser culture moves more of the arm:
#
# | Level | OD above | Joint |
# |---|---|---|
# | 1 | 0.006 | J5 wrist turn |
# | 2 | 0.015 | J4 wrist bend |
# | 3 | 0.04 | J3 elbow |
# | 4 | 0.10 | J2 shoulder |
# | 5 | 0.25 | J1 base |
#
# (J6, the end flange, only spins in place, so it is not used.) Custom levels use the same format,
# e.g. `OD_LEVELS="0.01:J4:15,0.05:J1:15"`.
#
# - Levels are **absolute OD values** (not relative to the baseline), so the same vial gives the same move every run.
# - Each level fires **once per upward crossing**, with its own hysteresis: it re-arms only after OD falls below
#   `level − margin`, where margin is 10% of the level (at least 0.0002 OD).
# - The first reading only sets the starting state: a level the OD is already above does not fire at start-up.
# - If OD jumps past several levels in one reading, only the **highest** level's move runs, and the lower levels
#   are marked as fired, so they don't fire later while OD is still above them.
# - Safety: joints J1–J6 only, at most 30° per move, relative to the start pose, at `SPEED`, and every move must
#   pass the **table limiter** below before it is sent.

# %%
MAX_LEVEL_DEG = 30
PRESET_LEVELS = "0.006:J5:15,0.015:J4:15,0.04:J3:15,0.1:J2:15,0.25:J1:15"


def parse_levels(spec):
    """'0.01:J4:20,0.05:J1:25' -> [(0.01, 3, 20.0), (0.05, 0, 25.0)], sorted by OD. 'preset' -> PRESET_LEVELS."""
    if (spec or "").strip().lower() == "preset":
        spec = PRESET_LEVELS
    levels = []
    for part in (spec or "").replace(" ", "").split(","):
        if not part:
            continue
        try:
            od_s, joint_s, deg_s = part.split(":")
            od, deg = float(od_s), float(deg_s)
            joint = int(joint_s.upper().lstrip("J")) - 1
        except ValueError as err:
            raise ValueError(f"OD_LEVELS entry {part!r} must look like 0.05:J1:25") from err
        if not 0 <= joint <= 5:
            raise ValueError(f"OD_LEVELS entry {part!r}: joint must be J1..J6")
        if not 0 < abs(deg) <= MAX_LEVEL_DEG:
            raise ValueError(f"OD_LEVELS entry {part!r}: degrees must be between 0 and {MAX_LEVEL_DEG}")
        levels.append((od, joint, deg))
    levels.sort()
    if len({od for od, _, _ in levels}) != len(levels):
        raise ValueError("OD_LEVELS has two entries with the same OD")
    return levels


class LevelTrigger:
    """One hysteresis switch per level. update(od) returns the index of the level to act on, or None."""

    def __init__(self, levels, min_margin=0.0002):
        self.levels = levels
        self.margins = [max(0.1 * od, min_margin) for od, _, _ in levels]
        self.armed = [True] * len(levels)
        self.primed = False

    def update(self, od):
        if not self.primed:
            # First reading: levels the OD is already above count as fired, so starting the run with a vial
            # already in does not move the arm. They re-arm once OD falls below them.
            self.primed = True
            self.armed = [od <= lvl for lvl, _, _ in self.levels]
            return None
        fired = []
        for i, (lvl, _, _) in enumerate(self.levels):
            if self.armed[i] and od > lvl:
                self.armed[i] = False
                fired.append(i)
            elif not self.armed[i] and od < lvl - self.margins[i]:
                self.armed[i] = True
        return max(fired) if fired else None


# %% [markdown]
# ### Table limiter
#
# Before any level move is sent, we **calculate where every part of the arm will be** from the joint angles,
# using the myCobot 320's link geometry (DH parameters, manual p. 138). Height 0 is the surface the arm stands on.
# A move is sent only if all of these hold, otherwise it is skipped and logged as `BLOCKED`:
#
# 1. Every joint, the flange and the tool tip (`TOOL_MM` beyond the flange, default 100 mm for the gripper) stay at
#    least `TABLE_CLEARANCE_MM` (default 50 mm) above the table, at the target **and** at 10 points along the way.
# 2. For the bending joints (J2 shoulder, J3 elbow, J4 wrist) the 15° goes whichever way keeps the arm **higher**.
# 3. Every joint stays 10° inside its limit (±165°, J6 ±175°).
# 4. On the real arm, the calculated flange position must match the position the arm reports (`get_coords`) within
#    20 mm at start-up. If it doesn't, or the arm can't report it, level mode refuses to move the real arm.
#
# It only knows about the table. Keep other objects (the reactor, cables) out of the arm's reach.

# %%
DH = [  # (alpha_{i-1}, a_{i-1} mm, d_i mm, theta offset) for J1..J6, modified DH, myCobot 320 manual p. 138
    (0.0, 0.0, 173.9, 0.0), (math.pi / 2, 0.0, 0.0, -math.pi / 2), (0.0, -135.0, 0.0, 0.0),
    (0.0, -120.0, 95.0, -math.pi / 2), (math.pi / 2, 0.0, 87.78, 0.0), (-math.pi / 2, 0.0, 65.5, 0.0)]
TOOL_MM = float(os.environ.get("TOOL_MM", 100))
TABLE_CLEARANCE_MM = float(os.environ.get("TABLE_CLEARANCE_MM", 50))
JOINT_LIMITS = [165, 165, 165, 165, 165, 175]
LIMIT_MARGIN = 10


def arm_points(angles):
    """3D points (mm) of each joint, the flange and the tool tip for the given joint angles (degrees)."""
    T, pts = np.eye(4), []
    for (alpha, a, d, off), q in zip(DH, angles):
        th = math.radians(q) + off
        ca, sa, ct, st = math.cos(alpha), math.sin(alpha), math.cos(th), math.sin(th)
        T = T @ np.array([[ct, -st, 0, a], [st * ca, ct * ca, -sa, -sa * d], [st * sa, ct * sa, ca, ca * d], [0, 0, 0, 1]])
        pts.append(T[:3, 3].copy())
    pts.append((T @ np.array([0, 0, TOOL_MM, 1]))[:3])
    return pts


def lowest_point(angles):
    return min(p[2] for p in arm_points(angles))


def pose_problem(start, target):
    """None if moving from start to target is safe, else the reason it is not."""
    for j, (q, lim) in enumerate(zip(target, JOINT_LIMITS)):
        if abs(q) > lim - LIMIT_MARGIN:
            return f"J{j + 1} at {q:.0f}° is within {LIMIT_MARGIN}° of its ±{lim}° limit"
    for t in np.linspace(0, 1, 11):            # target and 10 points along the joint-space path
        pose = [s + t * (g - s) for s, g in zip(start, target)]
        z = lowest_point(pose)
        if z < TABLE_CLEARANCE_MM:
            return f"part of the arm would come within {z:.0f} mm of the table (minimum {TABLE_CLEARANCE_MM:.0f} mm)"
    return None


def level_target(level):
    """(target pose, signed degrees used, problem or None). Bending joints go whichever way keeps the arm higher."""
    _, joint, deg = level
    options = [deg, -deg] if joint in (1, 2, 3) else [deg]
    # Rank by the lowest point, then by tool-tip height: the shoulder joint never moves, so the lowest point is
    # often a tie, and the tip height is what tells "lifts the arm" from "lowers it toward the table".
    options.sort(key=lambda d: (round(lowest_point(nudge(joint, d)), 1), arm_points(nudge(joint, d))[-1][2]), reverse=True)
    for d in options:
        target = nudge(joint, d)
        problem = pose_problem(HOME, target)
        if problem is None:
            return target, d, None
    return nudge(joint, options[0]), options[0], problem


def limiter_trusted(arm):
    """On the real arm, the calculated flange position must match the arm's own reading within 20 mm."""
    if isinstance(arm, DryRunArm):
        return True, "dry-run arm: limiter checked by calculation only"
    for _ in range(5):
        try:
            c = arm.get_coords()
            if isinstance(c, (list, tuple)) and len(c) == 6:
                calc = arm_points(HOME)[5]
                err = float(np.linalg.norm(np.array(c[:3]) - calc))
                ok = err <= 20
                return ok, f"calculated flange {np.round(calc, 1).tolist()} vs arm {list(c[:3])}: {err:.1f} mm apart"
        except Exception:
            pass
        time.sleep(0.2)
    return False, "the arm did not report its position (get_coords)"


def respond_level(arm, level):
    """Run one level's move if the limiter allows it. Returns (pose read back or None, signed degrees, problem)."""
    target, d, problem = level_target(level)
    if problem or not LIMITER_OK:
        return None, d, problem or f"limiter not trusted on this arm ({LIMITER_NOTE})"
    move(arm, target)
    move(arm, HOME)
    return read_angles(arm, fallback=HOME), d, None


LIMITER_OK, LIMITER_NOTE = limiter_trusted(arm)
print(f"table limiter: {'active' if LIMITER_OK else 'NOT TRUSTED, level moves disabled'} ({LIMITER_NOTE}); "
      f"start pose lowest point {lowest_point(HOME):.0f} mm above the table")

# Limiter self-checks: the geometry matches the manual (all joints at 0 → arm straight up, flange 516.7 mm high;
# shoulder at 90° → arm horizontal at shoulder height 173.9 mm), a pose that dips into the table is blocked,
# and a small move from an upright pose is allowed.
assert abs(arm_points([0] * 6)[5][2] - 516.68) < 0.1
assert abs(arm_points([0, 90, 0, 0, 0, 0])[5][2] - 173.9) < 0.1
assert pose_problem([0] * 6, [0, 100, 60, 0, 0, 0]) is not None
assert pose_problem([0] * 6, [0, 15, 0, 0, 0, 0]) is None
assert pose_problem([0] * 6, [0, 0, 0, 0, 160, 0]) is not None          # joint-limit margin
_tip = lambda pose: arm_points(pose)[-1][2]
_lean = [0, 30, 0, 0, 0, 0]                                               # arm leaning forward
assert _tip([0, 45, 0, 0, 0, 0]) < _tip(_lean) < _tip([0, 15, 0, 0, 0, 0])   # bending back toward upright lifts the tip


# Self-check with the preset: a gradual rise moves wrist → base, then a single jump moves only the base.
_lv = parse_levels("preset")
assert [(od, j + 1, d) for od, j, d in _lv] == [(0.006, 5, 15), (0.015, 4, 15), (0.04, 3, 15), (0.1, 2, 15), (0.25, 1, 15)], _lv
_series = ([0.004] * 3 + [0.007, 0.0065, 0.0068]    # crosses 0.006 once, despite noise around it
           + [0.02, 0.05, 0.045, 0.12, 0.3, 0.35]    # crosses 0.015, 0.04, 0.1, then 0.25
           + [0.1, 0.02, 0.003]                      # falls below every level: all re-arm
           + [0.38, 0.39])                           # one jump past all five: only the base moves
_lt = LevelTrigger(_lv)
_hits = [(i, _lv[k][1] + 1) for i, v in enumerate(_series) if (k := _lt.update(v)) is not None]
assert _hits == [(3, 5), (6, 4), (7, 3), (9, 2), (10, 1), (15, 1)], _hits
assert _lt.update(0.39) is None and _lt.update(0.3) is None     # stays high: no re-fire
_start_high = LevelTrigger(_lv)                                  # run starts with a vial already in (OD 0.03)
assert [_start_high.update(v) for v in (0.03, 0.03, 0.05)] == [None, None, 2]   # no move at start; 0.04 still fires
print(f"level self-check passed: rising OD → joints {[j for _, j in _hits]} (J5 wrist … J1 base, then base only for the jump)")

# %%
def simulated_od():
    """Fallback OD: rises past the threshold, falls back, and rises again (two crossings)."""
    for v in np.concatenate([np.linspace(0.10, 0.30, 15), np.linspace(0.30, 0.10, 15), np.linspace(0.10, 0.30, 15)]):
        yield datetime.now(timezone.utc).isoformat(timespec="seconds"), float(v)


live = "latest_od" in globals() and globals().get("EXPERIMENT")
if live:
    first = latest_od(EXPERIMENT)
    live = first is not None
if live:
    SOURCE = f"live Pioreactor OD (experiment {EXPERIMENT})"
    # Threshold from the live signal itself: the last ~12 readings give the current level and its noise.
    # Trigger a little above normal noise (4 standard deviations, at least 0.0002 OD), so noise alone never
    # fires the arm but a real rise in OD does. Re-arm only after OD falls back 2 noise-widths below it.
    # Override for a demo with OD_THRESHOLD / OD_MARGIN environment variables.
    try:
        now_iso = leader_now()
        pts = sorted(get_od_series(EXPERIMENT).get(SERIES_USED, []), key=lambda p: _when(p[0]))
        pts = [p for p in pts if not now_iso or _when(p[0]) <= _when(now_iso)][-12:]
        vals = np.array([p[1] for p in pts]) if len(pts) >= 3 else np.array([first[1]])
    except Exception:
        vals = np.array([first[1]])
    # Robust baseline: the median and MAD ignore a few leftover high readings (e.g. the previous vial still settling),
    # which otherwise inflate the noise estimate and push the threshold above what a real vial reaches.
    level = float(np.median(vals))
    noise = float(1.4826 * np.median(np.abs(vals - level)))
    margin_above = min(max(4 * noise, 0.0002), 0.005)       # 4 robust sd, but never less than 0.0002 or more than 0.005
    THRESHOLD = float(os.environ.get("OD_THRESHOLD", round(level + margin_above, 5)))
    MARGIN = float(os.environ.get("OD_MARGIN", round(min(max(2 * noise, 0.0001), 0.0025), 5)))
    print(f"live baseline: OD {level:.5f} ± {noise:.5f} over {len(vals)} readings")
    EVERY = float(os.environ.get("OD_POLL_SECONDS", 5.0))   # match the reactor sampling (default: 1 reading every 5 s)
    POLLS = int(float(os.environ.get("OD_WATCH_MINUTES", 5)) * 60 / EVERY)   # how long to watch (default 5 min)
    def readings():
        for _ in range(POLLS):
            r = latest_od(EXPERIMENT)
            if r:
                yield r
            time.sleep(EVERY)
else:
    SOURCE = "simulated OD (Part A not connected: live API unavailable)"
    THRESHOLD, MARGIN = 0.20, 0.03
    readings = simulated_od
print(f"OD source: {SOURCE}\nthreshold {THRESHOLD}, re-arm below {THRESHOLD - MARGIN:.4f}")

LEVELS = parse_levels(os.environ.get("OD_LEVELS"))
level_trigger = LevelTrigger(LEVELS) if LEVELS else None
if LEVELS:
    print("level mode (OD_LEVELS): " + ", ".join(f"OD > {od} → J{j + 1} {d:+g}°" for od, j, d in LEVELS)
          + "  (the single threshold above is not used)")

trigger = ThresholdTrigger(THRESHOLD, MARGIN)
log = []
RUN_STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = EVIDENCE / f"trigger_log_{RUN_STAMP}.csv"     # one file per run, written after EVERY reading
try:
    for ts, od in readings():
        if level_trigger:
            k = level_trigger.update(od)
            fired = k is not None
            pose, d, problem = respond_level(arm, LEVELS[k]) if fired else (None, None, None)
            lvl, j = (LEVELS[k][0], LEVELS[k][1]) if fired else (None, None)
            if fired and problem:
                event = f"BLOCKED J{j + 1} {d:+g}° (level {lvl}): {problem}"
            else:
                event = f"ARM MOVED J{j + 1} {d:+g}° (level {lvl})" if fired else ""
            state = " ".join(f"{od_l}:{'armed' if a else 'fired'}" for (od_l, _, _), a in zip(LEVELS, level_trigger.armed))
            log.append(dict(time=ts, od=od, threshold=lvl if fired else "", event=event,
                            pose=[round(a, 1) for a in pose] if pose else ""))
        else:
            fired = trigger.update(od)
            pose = respond(arm) if fired else None
            event = "ARM MOVED" if fired else ""
            state = "armed" if trigger.armed else "waiting to re-arm"
            log.append(dict(time=ts, od=od, threshold=THRESHOLD, event=event,
                            pose=[round(a, 1) for a in pose] if pose else ""))
        pd.DataFrame(log).to_csv(LOG_FILE, index=False)     # saved continuously, so Ctrl+C keeps everything
        if live or fired:   # live runs print every reading so you can watch; simulated runs print only triggers
            shown = "levels" if level_trigger else f"threshold {THRESHOLD}"
            print(f"{ts}  OD {od:.5f}  {shown}  {('→ ' + event) if fired else state}", flush=True)
except KeyboardInterrupt:
    print("stopped early (Ctrl+C); everything so far is saved", flush=True)
log = pd.DataFrame(log)
print(f"trigger log: {LOG_FILE}", flush=True)

fig, ax = plt.subplots(figsize=(9, 3.2))
ax.plot(range(len(log)), log.od, "-o", ms=3, label="OD")
if LEVELS:
    for od_l, j, d in LEVELS:
        ax.axhline(od_l, color="r", ls="--", lw=1)
        ax.text(0, od_l, f" J{j + 1} {d:+g}°", color="r", fontsize=8, va="bottom")
else:
    ax.axhline(THRESHOLD, color="r", ls="--", label="threshold")
    ax.axhline(THRESHOLD - MARGIN, color="r", ls=":", lw=1, label="re-arm level")
for i in log.index[log.event != ""]:
    ax.axvline(i, color="green", alpha=0.4); ax.text(i, ax.get_ylim()[1], " arm", color="green", fontsize=8, va="top")
ax.set(xlabel="reading #", ylabel="OD", title=f"Arm response to OD ({SOURCE})"); ax.legend(frameon=False, fontsize=8)
plt.tight_layout(); plt.show()
print(f"{(log.event != '').sum()} responses from {len(log)} readings; log saved to {EVIDENCE / 'trigger_log.csv'}")
