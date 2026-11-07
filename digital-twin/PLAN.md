# Plan: Digital Twin Challenge (challenge 1)

**Owner:** Alex (`@alexwilldev`). Brandon owns the Biofilm challenge in `biofilm/`; see the board.
**Time budget:** 2 hours.
**Deliverable:** one self-contained Google Colab notebook, `digital-twin/digital_twin.ipynb`.
**Source:** https://github.com/SamOliveiraLab/Digital-Twin-Challenge, cloned to `~/Developer/challenge-ref`.
**Complexity:** Medium. The modelling is simple. The risk is learning the Viva-munk API and the simulation run time.

For what every term means, see [../GUIDE.md](../GUIDE.md).

---

## 1. The challenge in brief

### Task
- Start from the first microscope picture (frame 0): 248 real E. coli cells in a 34 × 60 µm chamber, open on the right side (x = 34).
- Build a simulation with **Vivarium + Viva-munk** and predict the colony from 0 to 135 min (frames 0–27, 5 min apart).
- We get the real data for frames 0–13 (0–65 min). Frames 14–27 are hidden, and that is what gets scored (`chamber.json: frames_scored = 14-27`).
- Add the rules one at a time. Measure each from the data rather than guessing it, and show what each rule changes:
  1. **Growth:** linear or exponential? Does every cell grow at the same rate?
  2. **Division:** a fixed size, or a fixed added length (the "adder")?
  3. **Position:** do cells near the opening (x = 34) grow faster?
  4. *Optional extra:* use the COMSOL flow field instead of plain distance-to-opening as the "fresh food" signal.

### Deliverables (from the README and `starter_notebook.ipynb`)
1. For **each rule**: the measurement, a plot of twin vs real cell count over frames 0–13, and the **% error** of cell count and total cell area.
2. **Final result**, like `images/digital_twin_result.png`:
   - figure (a) cell count and (b) total area over 0–135 min, each divided by its value at t = 0, with one line per rule set, the real data as dots, and the hidden 70–135 min shaded grey;
   - a table of % error (count, area) with one row per rule set;
   - a **video** of the twin next to the real cells, 0–135 min.
3. A few sentences discussing the results: what each rule changed, which mattered most, and where the twin is still off.

### Judging (what we know)
- No points rubric is published. Stated criteria: "how you think, how you approach the problem, and how close you get."
- "Close" means a low % error. The hidden frames 14–27 are graded, presumably by organisers who compare our curves (or a prediction file) against the hidden data.
- Rules must be **measured, not guessed**, and each one must be shown separately.
- % error = mean over frames of |twin − real| / real × 100, for both count and area.

### Data
| file | contents | used for |
|---|---|---|
| `data/frame0_cells.csv` | 248 cells: `cell_id, x_um, y_um, length_um` (total, tip to tip), `width_um, angle_rad, area_um2` | initial state |
| `data/chamber.json` | 34 × 60 µm; y points down; open side x = 34; 0.0645 µm/px; 300 s/frame | geometry, units |
| `data/real_counts_0-13.csv` | `frame, time_min, cells, total_area_um2` (248 → 337 cells, 570 → 700 µm²) | the target for % error |
| `data/tracks_0-13.csv` | every cell in every frame, plus `parent_id` (4084 rows) | rule 1 (growth), rule 3 (x vs growth) |
| `data/lineage_0-13.csv` | `cell_id, first_frame, last_frame, parent_id, ends_in_window` (447 cells) | rule 2 (division) |
| `data/real_masks_0-13.npz`, `real_movie_0-13.gif`, PNGs | real outlines and pictures | the side-by-side video |
| `comsol_flow/*.npz/csv` | fluid velocity on a 1 µm grid, frames 0–13 | optional rule 3b |

### Constraints
- Python ≥ 3.11. The exact pins are Viva-munk `3fc4188…`, `process-bigraph==1.1.4`, `bigraph-schema==1.1.3`, `pymunk==7.2.0`.
- The notebook must run top to bottom in a fresh Colab. The first cell pip-installs the pins and `git clone`s the challenge repo for the data. No local paths.
- Count only cells inside the 34 × 60 window. Cells that leave through x = 34 are removed.
- Runs are random, so average a few seeds (3) before trusting a change.
- Viva-munk `length` is the **straight middle part only**: `length = length_um − width_um`, `radius = width_um / 2`.

### Open questions (not blocking; we assume the bracketed answer)
1. **How do we submit?** A link to the Colab notebook, or an uploaded .ipynb? *(Assume we upload the .ipynb with all outputs kept, and keep a Colab link ready too.)*
2. **Does a prediction file get graded?** `.gitignore` lists `my_prediction.csv`, which suggests one might be collected. *(Assume no. If it's cheap, we also write `my_prediction.csv` with frame, count and area for frames 0–27.)*
3. **Is the COMSOL flow extra worth points?** *(Assume it's a bonus. Only attempt it if we are ahead at the 85 min mark.)*

---

## 2. Patterns to mirror (grounding)

This repo (`jsnn-hackathon`) has no code to mirror yet. The useful patterns are in Viva-munk at the pinned commit (`~/Developer/vivamunk-ref`):

| What | Source | Pattern |
|---|---|---|
| Loading real cells into a chamber | `partaker_to_vivamunk.py:68` `load_partaker_cells`, `:120` `build_agents` | agent dict: `id, type='segment', mass, length, radius, angle, location, velocity, elasticity`; mass = 0.02 × capsule area. **Its `length` is the total length; ours must subtract the width.** |
| Document (composite spec) | `partaker_to_vivamunk.py:222` `document_fn` | `cells` + `multibody` (`local:PymunkProcess`, `env_size`=x extent, `env_height`=y extent) + `remove_crossing` + `emitter` |
| Adder growth and division | `multi_cell/processes/grow_divide.py:374` `AdderGrowDivide` | per-cell α (1/h, lognormal), Δ (µm), divide when `L ≥ L_birth + Δ`. Attach it with `add_adder_grow_divide_to_agents(state, 'cells', config)` (`:167`) |
| Removing cells at the opening | `multi_cell/processes/remove_crossing.py` | `make_remove_crossing_process(x_max=34, agents_key='cells')` |
| Running | `multi_cell/experiments/runner.py` `run_experiment` | to read before Step 3 |
| Side-by-side video | `side_by_side_combiner.py`, `real_movie_renderer.py`, `sim_mask_renderer.py` | the organisers' own video tooling, reused or adapted |

**Known gotcha:** `AdderGrowDivide._ensure_initialized` sets `L_birth` to the cell's **current** length. Cells in frame 0 are partway through their cycle, so every frame-0 cell would wait a whole extra Δ before dividing, and the count would lag. Fix this with a small subclass (or a pre-set field) that gives frame-0 cells a measured birth length, `L_birth ≈ L_now − (fraction of Δ already added)`, estimated from the data.

---

## 3. Notebook structure

The notebook follows the starter's sections, so the judges can find everything. Each section is one or a few cells.

| # | Section | What it holds |
|---|---|---|
| 0 | Title + summary | a 3-line summary of the result and the final error table (filled in at the end) |
| 1 | Setup | `pip install` the pins; `git clone` the challenge repo (skipped if already there); imports; `SEED`s; constants (34 × 60, 300 s/frame) |
| 2 | Look at the data | load the CSVs; show frame 0 and the real movie; real count and area curves |
| 3 | Helpers (one cell) | `frame0_to_agents()`, `build_document(rules)`, `run_twin(rules, seed)` → per-frame table of count and area inside the window, `pct_error(sim, real)`, `plot_vs_real()` |
| 4 | Baseline (rule 0) | physics only, no growth: cells sit still. A sanity check that they appear where the real cells are (overlay on frame 0) |
| 5 | Rule 1: growth | **Measure:** fit log(length) vs time per cell → α distribution (mean, CV); show that it's exponential (log-length is straight). **Twin:** growth with no division. Plot and % error |
| 6 | Rule 2: division | **Measure:** from the lineage, Δ = L_div − L_birth (adder) vs L_div (sizer); daughter / mother length ratio. **Twin:** `AdderGrowDivide` with the measured α and Δ, plus the frame-0 birth-length fix. Plot and % error |
| 7 | Rule 3: position | **Measure:** α vs `x_um` (binned plus a linear fit). **Twin:** α scaled by distance to the opening (subclass). Plot and % error. *Optional 3b:* α from the COMSOL flow speed, compared |
| 8 | Final result | 3 seeds × each rule set → figure (a) count and (b) area, normalised, 0–135 min, hidden part grey; % error table; side-by-side video (real 0–65 min, then twin only) embedded as GIF bytes |
| 9 | Discussion | 5–8 sentences |

Simulation settings: process interval 30 s, run 8100 s (135 min), record every 300 s.

---

## 4. Time budget (120 min)

| Time | Block | Done when |
|---|---|---|
| 0:00–0:10 | **Setup + smoke test.** Local venv on Python 3.11+ with the pins (started in the background immediately). Run 20 cells for 10 sim-min and time it. | We know the sim speed (s per sim-minute at 250 → 600 cells) |
| 0:10–0:25 | **Measurements (sections 2, 5, 6, 7).** These are pandas only and need no simulation. | α mean/CV, Δ mean/CV, α-vs-x fit are all known |
| 0:25–0:50 | **Twin core (sections 3–4).** Loader, document, run, count/area in window, % error. | Baseline run overlays frame 0 correctly |
| 0:50–1:10 | **Rules 1 and 2** with the birth-length fix. | Count curve tracks 248 → 337 by 65 min |
| 1:10–1:25 | **Rule 3** (position). Use 3 seeds per rule set from here on. | Rule-3 % error is compared with rule 2 |
| 1:25–1:45 | **Final result.** Figure, table, video, discussion. | Every deliverable is visible in the notebook |
| 1:45–1:55 | **Colab check.** Restart and run all in a fresh Colab, fix path or install issues, save with outputs. | Clean run with all outputs present |
| 1:55–2:00 | Submit; post on the board. | Submitted |

**Cut lines if we're behind:** at 1:10 with rule 2 not yet working, drop rule 3 to measurement-only (show the plot and say it wasn't added). At 1:25, skip the COMSOL extra entirely. At 1:40, use a simple matplotlib twin animation for the video, without real-mask rendering.

**If the sim is slow** (more than ~2 min per 135-min run): use 2 seeds, and record only every 300 s.

---

## 5. Work split and parallelism

- **Alex's agent:** everything in this plan.
- **Brandon's agent:** Biofilm challenge (`biofilm/`), assigned on the board.
- Inside this challenge, the measurement work (block 0:10–0:25) can run in parallel with the twin core (0:25–0:50), using a subagent for the pandas measurements while the main agent builds the loader.

## 6. shared/

Keep it minimal. Nothing goes into `shared/` until a second notebook actually needs it. Both notebooks must be self-contained, so shared pieces are **snippets copied into cells**, not imported modules. Likely candidates once biofilm confirms the need:
- `shared/colab_setup.md`: the first-cell pattern (pip install pins, fetch data, detect Colab vs local).
- `shared/embed_gif.md`: embedding GIF bytes so the animation survives submission (biofilm's starter already has `display_trajectory_gif`).

No other shared code. Don't build for challenges we haven't seen.

## 7. Files

| File | Action |
|---|---|
| `digital-twin/PLAN.md` | this plan |
| `GUIDE.md` | explainer for every concept, file and tool |
| `digital-twin/digital_twin.ipynb` | CREATE: the deliverable |
| `digital-twin/requirements.txt` | CREATE: pins for the local venv (copy of the challenge's) |
| `art/snapshot.sh`, `art/worklog.jsonl` | low-priority art logger (already running) |

## 8. Validation

```bash
# local run-all (the same thing Colab will do)
jupyter nbconvert --to notebook --execute digital-twin/digital_twin.ipynb --output digital_twin.ipynb
```
Then upload to Colab, choose Runtime → Restart and run all, and check every output is present.

## 9. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Viva-munk API learning curve (document wiring, emitter output format) | High | Copy `partaker_to_vivamunk.py`'s document. Smoke-test in the first 10 min |
| Slow simulation at ~600 cells over 135 min | Medium | Time it early; fewer seeds; 30 s interval |
| Count lags because frame-0 cells reset `L_birth` | High (known) | Birth-length fix, section 2 |
| `length` total vs middle-part mix-up | Medium | Subtract the width in the loader; assert that total area at t=0 ≈ 570 µm² |
| Colab Python or pin install fails | Low–Med | Test in Colab by 1:45; pins need git, which Colab has |
| Overfitting to frames 0–13 | Medium | Keep parameters measured, not tuned to the count curve |

## 10. Acceptance
- [ ] Every starter-notebook step is filled in, with plots and % errors per rule
- [ ] The final figure, table and video match the format of `images/`
- [ ] The discussion is written
- [ ] Runs top to bottom in fresh Colab, with outputs saved
