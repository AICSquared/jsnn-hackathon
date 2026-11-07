"""Render art/worklog.jsonl as a generative piece: art/hackathon_art.png.

Time spirals outward from the centre (one turn per 30 minutes). Each folder is a coloured strand whose
thickness and glow follow how much work it holds; commits flare as stars; board posts are rings.
Run any time:  digital-twin/.venv/bin/python art/render.py && open art/hackathon_art.png
"""
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
rows = [json.loads(l) for l in (HERE / "worklog.jsonl").read_text().splitlines() if l.strip()]
t = np.array([datetime.fromisoformat(r["ts"].replace("Z", "+00:00")).timestamp() for r in rows])
mins = (t - t[0]) / 60
theta = mins / 30 * 2 * np.pi
radius = 1 + mins / 6

STRANDS = {"digital-twin": ("#f2b134", 0.0), "biofilm": ("#4cc9f0", 2.1), "shared": ("#b5179e", 4.2),
           "tools": ("#80ed99", 1.05)}

fig = plt.figure(figsize=(9, 9), facecolor="#07070f")
ax = fig.add_axes([0, 0, 1, 1], polar=True, facecolor="#07070f")
ax.set_axis_off()

fine = np.linspace(0, mins[-1], max(len(mins) * 20, 2))
th_f, r_f = fine / 30 * 2 * np.pi, 1 + fine / 6
for k, (name, (color, phase)) in enumerate(STRANDS.items()):
    size = np.array([r["dirs"].get(name, {}).get("bytes", 0) for r in rows], float)
    if size.max() == 0:
        continue
    w = 0.3 + 6 * np.sqrt(np.interp(fine, mins, size) / size.max())
    wobble = 0.35 * np.sin(th_f * 3 + phase)
    for glow, alpha in [(9, 0.03), (4, 0.07), (1, 0.9)]:
        ax.scatter(th_f + phase, r_f + wobble, s=w * glow * 3, color=color, alpha=alpha, lw=0)
    fig.text(0.05, 0.95 - k * 0.03, f"● {name}", color=color, fontsize=10, family="monospace")

edits = np.array([r["dirty"]["add"] + r["dirty"]["del"] for r in rows], float)
ax.scatter(theta, radius * 0.6, s=2 + 60 * np.sqrt(edits / max(edits.max(), 1)), color="white", alpha=0.25, lw=0)


def events(key):
    out, prev = [], None
    for i, r in enumerate(rows):
        if key in r and r[key] is not None:
            if prev is not None and r[key] > prev:
                out.append(i)
            prev = r[key]
    return out


for key, color in [("commits_alex", "#f2b134"), ("commits_brandon", "#4cc9f0")]:
    for i in events(key):
        ax.scatter(theta[i], radius[i] + 1.2, s=380, marker="*", color=color, edgecolor="white", lw=0.6, zorder=5)
for i in events("board_posts"):
    ax.scatter(theta[i], radius[i], s=900, facecolor="none", edgecolor="white", alpha=0.35, lw=0.8)

span = f"{datetime.fromtimestamp(t[0]):%H:%M} → {datetime.fromtimestamp(t[-1]):%H:%M}"
fig.text(0.5, 0.03, f"jsnn hackathon · {span} · {len(rows)} minutes", color="0.6", ha="center", family="monospace")
out = HERE / "hackathon_art.png"
fig.savefig(out, dpi=130, facecolor=fig.get_facecolor())
print(out)
