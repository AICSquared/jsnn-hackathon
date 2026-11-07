# %% [markdown]
# ## Track A: live optical density (OD) from the Pioreactor
#
# Objectives 2 and 3: find the running experiment, read its OD, and show a live timestamped stream.
#
# The API sits behind a Cloudflare tunnel that can go down. So every reading we fetch is **recorded** to
# `robotics/evidence/reactor/od_log.csv`, and when the API is unreachable the same functions **replay** that log.
# The notebook therefore runs anywhere, with or without the reactor.
#
# Contract with the arm track (`arm.py`): `latest_od(EXPERIMENT) -> (iso_timestamp, od) | None`.

# %%
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Organisers' tunnel by default. For our own reactor on the same network, set PIOREACTOR_API before running,
# e.g. PIOREACTOR_API=http://<hostname>.local/api, or assign od.API in the notebook.
API = os.environ.get("PIOREACTOR_API", "https://api.environnets.com/api").rstrip("/")
TIMEOUT_S = 8
MODE = "auto"        # "auto": live, falling back to replay on failure | "live": never replay | "replay": never call the API

try:
    HERE = Path(__file__).resolve().parent
except NameError:    # running as a notebook cell
    HERE = Path.cwd() / "robotics" if (Path.cwd() / "robotics").is_dir() else Path.cwd()
LOG = HERE / "evidence" / "reactor" / "od_log.csv"
LOG_FIELDS = ["fetched_at", "experiment", "series", "timestamp", "od"]


class ApiDown(Exception):
    """The Pioreactor API could not be reached or returned something unusable."""


def _get(path):
    """GET API + path and parse JSON. Raises ApiDown on any network, HTTP or JSON failure."""
    req = urllib.request.Request(API + path, headers={"Accept": "application/json",
                                                      "User-Agent": "jsnn-hackathon-robotics"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as err:
        raise ApiDown(f"{path}: {err}") from err


# %% [markdown]
# ### Objective 2: find the experiment and retrieve its OD
#
# `/experiments/latest` gives the running experiment. `/experiments/{exp}/time_series/od_readings?lookback=2`
# gives the last 2 hours of raw OD for every unit and channel, as series labels plus lists of points.
# The exact keys are unverified until the API is up, so the parser accepts the common spellings
# (`series`/`data`, `x`/`timestamp`, `y`/`value`) and raises a clear error otherwise.

# %%
def _read_log():
    if not LOG.exists():
        return []
    with LOG.open(newline="") as f:
        return list(csv.DictReader(f))


def get_latest_experiment():
    """Name of the running experiment; if the API is down, the experiment in the log; else None."""
    if MODE != "replay":
        try:
            body = _get("/experiments/latest")
            name = body.get("experiment") if isinstance(body, dict) else None
            if name:
                return name
            raise ApiDown(f"/experiments/latest: no 'experiment' key in {str(body)[:200]}")
        except ApiDown:
            if MODE == "live":
                raise
    rows = _read_log()
    return rows[-1]["experiment"] if rows else None


def _parse_series(body):
    """Turn the time_series response into {series_label: [(iso_timestamp, od), ...]} sorted by time."""
    if not isinstance(body, dict):
        raise ApiDown(f"od_readings: expected an object, got {type(body).__name__}")
    labels = body.get("series") or body.get("labels") or []
    data = body.get("data") or []
    if len(labels) != len(data):
        raise ApiDown(f"od_readings: {len(labels)} series labels but {len(data)} data lists; keys={list(body)}")
    out = {}
    for label, points in zip(labels, data):
        pts = []
        for p in points:
            ts = p.get("x", p.get("timestamp")) if isinstance(p, dict) else p[0]
            val = p.get("y", p.get("value")) if isinstance(p, dict) else p[1]
            if ts is None or val is None:
                continue
            pts.append((str(ts), float(val)))
        out[str(label)] = sorted(pts)
    return out


def get_od_series(experiment, lookback_hours=2):
    """All OD series for an experiment from the live API, recorded to the log. Raises ApiDown."""
    path = f"/experiments/{urllib.parse.quote(experiment, safe='')}/time_series/od_readings?lookback={lookback_hours}"
    series = _parse_series(_get(path))
    _record(experiment, series)
    return series


# %% [markdown]
# ### Record and replay
#
# Each new point is appended once to `od_log.csv` (deduplicated on series + timestamp). In replay mode,
# successive calls to `latest_od` step through the logged points in time order, as if they were arriving live,
# and wrap around at the end so a replayed demo can be repeated exactly.

# %%
def _record(experiment, series):
    seen = {(r["series"], r["timestamp"]) for r in _read_log()}
    new = [(label, ts, od) for label, pts in series.items() for ts, od in pts if (label, ts) not in seen]
    if not new:
        return 0
    LOG.parent.mkdir(parents=True, exist_ok=True)
    write_header = not LOG.exists()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LOG.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(LOG_FIELDS)
        for label, ts, od in sorted(new, key=lambda r: r[1]):
            w.writerow([now, experiment, label, ts, od])
    return len(new)


_replay_pos = 0


def reset_replay():
    """Start replay from the first logged reading again."""
    global _replay_pos
    _replay_pos = 0


def _replay_next(experiment, series_label=None):
    """Next logged point for this experiment (and series), cycling through the log. None if the log is empty."""
    global _replay_pos
    rows = [r for r in _read_log()
            if (experiment is None or r["experiment"] == experiment)
            and (series_label is None or r["series"] == series_label)]
    if not rows:
        return None
    rows.sort(key=lambda r: (r["timestamp"], r["series"]))
    row = rows[_replay_pos % len(rows)]
    _replay_pos += 1
    return row["timestamp"], float(row["od"])


# %% [markdown]
# ### The contract: `EXPERIMENT` and `latest_od`
#
# One reading: the newest point of **one** series. Mixing units or channels would make the value jump between
# vessels and trigger the arm on noise, so a single series is used: `series_label` if given, else `OD_SERIES`,
# else the first series alphabetically (e.g. `unit1-2`). The chosen label is kept in `SERIES_USED`.

# %%
OD_SERIES = None     # set to a label such as "unit1-2" to pin the vessel/channel
SOURCE = None        # "live" or "replay": where the last latest_od() reading came from
SERIES_USED = None


def latest_od(experiment, series_label=None):
    """(ISO timestamp, OD) of the newest reading, or None if there is no live data and nothing to replay."""
    global SOURCE, SERIES_USED
    wanted = series_label or OD_SERIES
    if MODE != "replay" and experiment:
        try:
            series = get_od_series(experiment)
            label = wanted or (min(series) if series else None)
            points = series.get(label, []) if label else []
            if points:
                SOURCE, SERIES_USED = "live", label
                return points[-1]
        except ApiDown:
            if MODE == "live":
                raise
    if MODE == "live":
        return None
    if wanted is None:
        labels = sorted({r["series"] for r in _read_log() if experiment is None or r["experiment"] == experiment})
        wanted = labels[0] if labels else None
    SOURCE, SERIES_USED = "replay", wanted
    return _replay_next(experiment, wanted)


EXPERIMENT = get_latest_experiment()   # None when the API is down and nothing has been logged yet
print(f"EXPERIMENT = {EXPERIMENT!r}  (mode {MODE}, log {'has data' if LOG.exists() else 'empty'})")


# %% [markdown]
# ### Objective 3: a live, timestamped OD stream
#
# Polls `latest_od` every `every` seconds for `seconds` seconds, prints a table row per new reading and redraws
# a plot. Repeated readings (the reactor samples less often than we poll) are printed once.

# %%
def stream_od(seconds=60, every=5, experiment=None, series_label=None, plot=True):
    """Stream OD readings and return them as a list of (timestamp, od, source)."""
    experiment = experiment or EXPERIMENT or get_latest_experiment()
    header = (f"experiment: {experiment!r}   mode: {MODE}   log: {LOG}\n"
              f"{'polled at (UTC)':<27}{'reading timestamp':<34}{'OD':>10}  source")
    print(header)
    rows, readings, last_ts, end = [], [], None, time.time() + seconds
    while True:
        reading = latest_od(experiment, series_label)
        polled = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if reading is None:
            print(f"{polled:<27}no data (API down and nothing logged)")
        elif reading[0] != last_ts:
            last_ts = reading[0]
            readings.append((*reading, SOURCE))
            rows.append(f"{polled:<27}{reading[0]:<34}{reading[1]:>10.4f}  {SOURCE}")
            if not (plot and _draw(header, rows, readings, experiment)):
                print(rows[-1])
        if time.time() + every > end:
            break
        time.sleep(every)
    return readings


def _draw(header, rows, readings, experiment):
    """In a notebook, redraw the whole table plus a plot in place. Returns False outside a notebook."""
    try:
        get_ipython  # noqa: F821
        import matplotlib.pyplot as plt
        from IPython.display import clear_output, display
    except (NameError, ImportError):
        return False
    clear_output(wait=True)
    print(header)
    print("\n".join(rows))
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(range(len(readings)), [r[1] for r in readings], "o-")
    ax.set(xlabel="reading #", ylabel="OD", title=f"Live OD: {experiment} ({readings[-1][2]})")
    ax.grid(alpha=0.3)
    display(fig)
    plt.close(fig)
    return True


# %% [markdown]
# **Live stream (objective 3).** 30 seconds of readings, polled every 5 s. Live when the reactor is up,
# otherwise a replay of the recorded log. Runs in the notebook and as a script, not when imported.

# %%
if __name__ == "__main__":
    od_stream = stream_od(seconds=30, every=5)
    print(f"{len(od_stream)} readings, series {SERIES_USED!r}, source {SOURCE!r}")
