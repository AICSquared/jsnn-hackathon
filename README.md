# JSNN Hackathon
## Alex Williams and Brandon Townsend

Our team repo for the JSNN hackathon (Nov 7, 2026). **We placed 2nd in stage 1 and advanced to the final round.** The bonus robotics challenge uses a myCobot 320 arm and a Pioreactor provided by the organisers. Each challenge is a self-contained **Google Colab notebook** in its own folder. We built them with AI coding agents (Claude) that coordinated through a GitHub-issue message board.

| Challenge | Folder | Owner | Notebook | Result |
|---|---|---|---|---|
| 1. Digital Twin: simulate an E. coli colony | [`digital-twin/`](digital-twin/) | Alex | [`digital_twin.ipynb`](digital-twin/digital_twin.ipynb) | Predicts cell count within **4.8%** and area within **1.1%** of the real cells · **2nd place, stage 1** |
| 2. Biofilm dispersion: track colonies breaking up | [`biofilm/`](biofilm/) | Brandon | [`biofilm_dispersion.ipynb`](biofilm/biofilm_dispersion.ipynb) | Colony 33 moved farthest (37.2 px); colony 27 had the largest breakup-score increase (+45) |
| Bonus: Robotics that Responds: live OD → robot arm | [`robotics/`](robotics/) | Brandon (reactor + OD), Alex (arm) | `robotics.ipynb` (in progress) | Planned: see [`robotics/PLAN.md`](robotics/PLAN.md) |

**Open in Colab:** Digital Twin [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/alexwilldev/jsnn-hackathon/blob/main/digital-twin/digital_twin.ipynb) · Biofilm [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/alexwilldev/jsnn-hackathon/blob/main/biofilm/biofilm_dispersion.ipynb)

**New here? Read in this order:** this README → [GUIDE.md](GUIDE.md) (what everything means, and how to explain it to judges) → the notebooks.

---

## Contents
1. [What's in the repo](#1-whats-in-the-repo)
2. [Run the notebooks](#2-run-the-notebooks)
3. [How the Digital Twin works](#3-how-the-digital-twin-works)
4. [How the Biofilm notebook works](#4-how-the-biofilm-notebook-works)
5. [How we worked: agents, board, git](#5-how-we-worked-agents-board-git)
6. [Learn it: a path for both of us](#6-learn-it-a-path-for-both-of-us)
7. [Known issues](#7-known-issues)

---

## 1. What's in the repo

```
jsnn-hackathon/
├── README.md                 ← you are here: overview, how to run, how to learn it
├── GUIDE.md                  ← plain-language explainer + judge talking points (both challenges)
├── AGENTS.md / CLAUDE.md     ← rules every AI agent follows (board etiquette, branches, ownership)
├── agentwalkthrough.md       ← how the agent message-board framework works (from the template)
│
├── digital-twin/             ← Challenge 1 (Alex)
│   ├── digital_twin.ipynb      THE DELIVERABLE: open this in Colab
│   ├── digital_twin.py         the notebook's source: edit this, not the .ipynb
│   ├── build_notebook.py       turns digital_twin.py into digital_twin.ipynb
│   └── PLAN.md                 the plan we made before writing code (task, data, time budget, risks)
│
├── biofilm/                  ← Challenge 2 (Brandon)
│   ├── biofilm_dispersion.ipynb          THE DELIVERABLE (needs 3 data files uploaded, see §2)
│   ├── biofilm_dispersion_starter.ipynb  the organisers' blank template, for reference
│   ├── build_notebook.py                 fills the starter's TODO cells → the deliverable
│   └── interpretation.md                 the 148-word interpretation (also inside the notebook)
│
├── robotics/                 ← Bonus challenge (Brandon: reactor + live OD; Alex: arm)
│   ├── PLAN.md                 1-hour plan: objectives, API, the two-track split, risks
│   ├── od.py                   (Track A) find the experiment, stream live OD, record/replay
│   ├── arm.py                  (Track B) myCobot 320 control, dry-run fallback, OD threshold trigger
│   ├── build_notebook.py       joins od.py + arm.py → robotics.ipynb
│   └── evidence/               photos, videos, OD log: proof of each milestone
│
├── tools/board               ← command-line tool for the agent message board (GitHub issue #1)
├── .claude/                  ← hooks that show new board posts to Claude Code agents
├── .github/ISSUE_TEMPLATE/   ← template for the board issue
│
├── art/                      ← just for fun: a generative-art record of our work
│   ├── snapshot.sh             logs the size of our work once a minute → worklog.jsonl
│   └── render.py               draws worklog.jsonl as hackathon_art.png
│
├── refs/                     ← NOT in git: local copies of the challenge repo, Viva-munk source, biofilm data
└── docs/                     ← images for the docs
```

The `refs/` folder and the Python environment (`digital-twin/.venv`) only exist on the machine that made them. Git ignores them, and the notebooks don't need them because they download what they need themselves.

---

## 2. Run the notebooks

### In Google Colab (how judges will see it)
Both notebooks already contain their saved outputs (plots, tables, video), so you can **read them without running anything**. To run one yourself:

**Digital Twin** (downloads its own data):
1. Click the Digital Twin **Open in Colab** badge at the top of this README (or in Colab: **File → Open notebook → GitHub**, paste `alexwilldev/jsnn-hackathon`, pick `digital-twin/digital_twin.ipynb`).
2. Choose **Runtime → Run all**. The first cell installs the exact package versions and downloads the challenge data. If it says the runtime restarts, wait a moment and choose **Run all** again (it only does this once).
3. It takes about 6–10 minutes: the simulation runs 3 random seeds for each set of rules.

**Biofilm** (you supply the data):
1. Click the Biofilm **Open in Colab** badge (or open `biofilm/biofilm_dispersion.ipynb` the same way).
2. Click the **folder icon** on the left and upload `biofilm.zip`, `colony_masks.npz` and `breakup_scores.csv` from the organisers' zip.
3. Choose **Runtime → Run all**.

**Robotics (bonus):** the notebook runs anywhere in *dry-run* mode (no arm needed) and replays recorded OD if the live API is down. To drive the real arm, run it on the laptop connected to the myCobot. See [`robotics/PLAN.md`](robotics/PLAN.md).

**To share a notebook:** choose **File → Save a copy in Drive**, then **Share → Anyone with the link → Viewer**.

### On your own computer
```bash
python3.13 -m venv digital-twin/.venv
digital-twin/.venv/bin/pip install -r refs/digital-twin-challenge/requirements.txt plum-dispatch==2.10.1 nbconvert ipykernel
digital-twin/.venv/bin/python digital-twin/build_notebook.py
digital-twin/.venv/bin/jupyter nbconvert --to notebook --execute --inplace digital-twin/digital_twin.ipynb
```
(The data clone happens automatically on first run if `refs/digital-twin-challenge` isn't there.)

**Editing workflow:** change `digital-twin/digital_twin.py`, rebuild with `build_notebook.py`, re-execute, and commit both files. The `.py` is plain text, so changes are easy to read in git. The `.ipynb` holds the outputs.

---

## 3. How the Digital Twin works

**The challenge:** the organisers grew 248 *E. coli* bacteria in a 34 × 60 µm chamber on a microscope chip (open on the right, where food flows past) and photographed it every 5 minutes. We get the first photo and 65 minutes of real data. We must simulate the colony and **predict the cell count and area for the next 70 hidden minutes**. Every rule has to be *measured* from the data and added one at a time.

```mermaid
flowchart LR
    A[Frame 0: 248 real cells] --> B[Convert to simulator cells<br/>check area = 570 µm²]
    D[Tracking data<br/>frames 0–13] --> M[Measure rules]
    M --> R1[Rule 1: growth<br/>exponential, doubling ≈ 144 min]
    M --> R2[Rule 2: division<br/>adder, Δ ≈ 1.7 µm]
    M --> R3[Rule 3: position<br/>+13% growth at the opening]
    B --> S[Simulate 135 min<br/>Vivarium + Viva-munk physics]
    R1 --> S
    R2 --> S
    R3 --> S
    S --> C[Count cells & area<br/>inside the camera window]
    C --> E[% error vs real<br/>3 seeds averaged]
```

| Step | What we did | Why |
|---|---|---|
| Load cells | middle length = tip-to-tip − width; radius = width / 2 | The simulator measures only the straight middle of a rod. Check: 569.0 vs 570.2 µm² real area at t = 0 |
| Open side | physics box 10 µm wider; delete cells whose centre passes x = 34 | The simulator only has closed boxes |
| Rule 1: grow | fit log(length) vs time for 369 cells | A straight line on a log scale means the same % growth per minute (exponential) |
| Rule 2: divide | adder rule: divide after adding Δ = 1.68 µm | Only 2 full cell cycles fit in 65 min, so Δ = mean length at division − mean length at birth |
| Mid-life cells | each frame-0 cell draws a division length from the 92 real ones longer than it | Otherwise all cells divide a cycle late, or all at once |
| Rule 3: position | growth rate scaled by distance from the opening | Measured but weak (r = 0.08) |
| Score | % error = mean of \|twin − real\| ÷ real over frames 0–13, average of 3 seeds | Runs are random |

**Result (% error, lower is better):**

| Rules | Cell count | Cell area |
|---|---|---|
| 1: grow | 14.25 | 1.28 |
| 1+2: + divide | 4.79 | 1.13 |
| 1+2+3: + position | **4.75** | **1.12** |

Division matters most. Position barely matters in this window. The twin's count falls behind the real count after about 20 min (308 vs 337 cells at 65 min) while its area stays on target: real cells are dividing at smaller sizes than our measured Δ predicts. More in the notebook's discussion and in [GUIDE.md §1–2](GUIDE.md).

---

## 4. How the Biofilm notebook works

17 microscope frames of bacterial colonies, plus masks saying which pixel belongs to which colony, plus a supplied 0–100 "breakup score" per colony per frame. For every colony and frame the notebook computes:
- **centroid**: the mean x, y of the colony's pixels;
- **displacement**: the distance from its first centroid;
- **step and cumulative distance**: how far it moved each frame, and in total;
- **breakup change**: the score minus its first *finite* score;
- **first threshold frame**: the first frame where the score is ≥ 40.

Missing frames are NaN and never zero, and a step is never counted across a gap. 70 of the 100 points are auto-graded within tight tolerances (centroids 0.05 px, distances 0.10 px, score changes 0.01, exact frame numbers for crossings), so the code checks itself against the starter's worked example and a missing-frame case. Details: [GUIDE.md §3](GUIDE.md) and [`biofilm/interpretation.md`](biofilm/interpretation.md).

---

## 5. How we worked: agents, board, git

- **One challenge each, in parallel.** Each person directs their own AI agent (Claude Code), which writes and runs the code. We make the decisions and check the results.
- **The board** is pinned [issue #1](https://github.com/alexwilldev/jsnn-hackathon/issues/1). Agents post every commit, push and handoff there, and tag each other with `@login`. Commands: `tools/board read -n 20`, `tools/board post "[Name's Claude] …"`, `tools/board wait`. How it works: [agentwalkthrough.md](agentwalkthrough.md).
- **Git flow:** for each task, file an issue, then work on branch `<issue#>-<slug>`, commit and push often, open a PR with `Closes #N`, and the author merges once it works. Post on the board before touching shared files (README, GUIDE, AGENTS, `shared/`).
- **Ownership:** Alex owns `digital-twin/`, `GUIDE.md`, `art/` and `robotics/arm.py`; Brandon owns `biofilm/` and `robotics/od.py`.

---

## 6. Learn it: a path for both of us

The goal is that either of us can explain *either* notebook to a judge without the agent.

**Level 1: the story (15 min).** Read [GUIDE.md §1](GUIDE.md): the 30-second pitch, the rule-by-rule table, and likely judge questions. Say the pitch out loud to each other.

**Level 2: read the notebook like a lab report (30 min).** Open the notebook in Colab and, section by section, answer:
1. *Step 2:* what do the real count and area curves look like, and which grows faster?
2. *Step 3:* why does the area check (569 vs 570 µm²) matter before anything else?
3. *Step 4:* in the log-length plot, why does a straight line mean exponential growth?
4. *Step 5:* why can't we measure Δ directly, and what did we do instead?
5. *Step 6:* the position effect is measured but weak. Should we still keep the rule?
6. *Step 7:* which rule dropped the error the most, and why is the area error low even with growth alone?

**Level 3: change one thing and predict first (30 min).** In Colab, edit one value, **write your prediction down**, then rerun from that step:

| Change (in the notebook) | Your prediction | What to expect (check it!) |
|---|---|---|
| In `RULE3`, set `x_slope=0` | ? | Almost no change: position is a weak effect |
| In `RULE2`, set `delta_mean=1.31` (the 2 complete cycles) | ? | Count error hardly moves in 0–65 min; more cells in the hidden period |
| In `RULE2`, set `use_birth_estimate=False` | ? | Count lags badly: every frame-0 cell is treated as newborn |
| In `RULE1`, double `alpha_mean_per_h` | ? | Area overshoots fast |
| Biofilm: change `THRESHOLD` to 30 | ? | 4 colonies cross instead of 3, and earlier |

**Level 4: rederive the design.** In Claude Code, run `/rederive` (on some setups it's `/rederive:rederive`). It asks you to re-invent each design decision from the problem (for example "how do you make a closed box behave like a chamber with one open side?") instead of explaining the code. Progress is saved in `.rederive/log.md` (local only).

**Words to know:** digital twin, exponential growth, doubling time, adder rule, Δ, capsule, seed, % error, centroid, displacement, NaN. All are defined in [GUIDE.md §6](GUIDE.md).

---

## 7. Known issues

- **Colab crash `cannot reify schema Array …`:** Colab ships `plum-dispatch` 2.9.0, which breaks the simulation library. The notebook now pins 2.10.1 and restarts the runtime once if needed. If you opened an older copy, reopen it from GitHub.
- **Count lag:** the twin predicts about 8% fewer cells than real at 65 min (explained in §3). Its hidden-period count is probably an underestimate, so trust the area prediction more.
- **Biofilm data isn't in git:** upload the 3 files in Colab (§2).

---

*Art:* `digital-twin/.venv/bin/python art/render.py && open art/hackathon_art.png` draws our work so far as a spiral: one strand per folder, stars for commits, rings for board posts.
