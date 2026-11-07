# Guide: what we did and how to explain it

**Purpose:** help us explain our work to the judges. It's written in plain language, so either of us can present either challenge.
Sections 1–2 are what we say. The rest is the background that lets us answer follow-up questions.
All numbers below come from the executed notebook `digital-twin/digital_twin.ipynb`.

- [1. Talking to the judges](#1-talking-to-the-judges)
- [2. Challenge 1: Digital Twin](#2-challenge-1-digital-twin)
- [3. Challenge 2: Biofilm dispersion](#3-challenge-2-biofilm-dispersion)
- [4. How we worked (team, agents, board)](#4-how-we-worked-team-agents-board)
- [5. Tools and file formats](#5-tools-and-file-formats)
- [6. Glossary](#6-glossary)

---

## 1. Talking to the judges

### 1.1 Digital Twin: the 30-second version
> "We built a simulation of a real E. coli colony that starts from the first microscope photo and predicts the next 70 minutes. We didn't guess any rules. We measured each one from the tracking data, added them one at a time, and checked how much each one cut the error. Cells grow exponentially, but slowly, doubling about every **144** minutes. They divide by the *adder* rule, adding about **1.7 µm** of length each cycle. Cells near the open side, where food arrives, grow about **13%** faster, though that effect is weak. With all three rules, our twin is within **4.8%** of the real cell count and **1.1%** of the real area."

### 1.2 Digital Twin: the story, one rule at a time
| Step | Question | What we measured | What it did to the twin |
|---|---|---|---|
| Start | Can we reproduce the first photo? | 248 cells loaded from frame 0, in a 34 × 60 µm box open on the right | Cells appear exactly where the real ones are (overlay plot) |
| Rule 1: growth | Same amount per minute, or same percentage? | log(length) vs time is a straight line, so growth is exponential. Rate α = **0.29/h** (doubling ≈ 144 min; cells differ by CV **0.31**); longer cells add more µm/min (r = 0.55) | Area is already close (1.3% error), but the count stays flat because nobody divides (14.3% error) |
| Rule 2: division | At a fixed size, or after adding a fixed amount? | From the family tree, mothers divide at 3.61 µm and daughters are born at 1.93 µm (each about half), so Δ ≈ **1.68** µm. Only 2 full cycles fit in 65 min, so we take the adder from the literature and estimate Δ from division and birth lengths | Count now rises. Count error drops from **14.3%** to **4.8%**; area error improves to **1.1%** |
| Rule 3: position | Do cells near the food grow faster? | Growth rate vs x: +0.6% per µm toward the opening (+13% at the opening), but weak (r = 0.08) | Almost no change: 4.79% → 4.75% count error. Measured, but not what drives this colony |
| (Extra) flow | Is the fluid flow a better food signal than distance? | Not attempted (time) | Next step |

### 1.3 Questions judges might ask, and our answers
- **"Why exponential and not linear growth?"** On a log scale, each cell's length rises in a straight line, which means the same percentage every minute. The linear fit was worse (show the plot).
- **"How do you know it's an adder?"** Honest answer: our 65-minute window is shorter than one cell cycle (~144 min), so we see only 2 cells from birth to division. That isn't enough to prove adder vs sizer from these data alone. We use the adder because it's the established rule for E. coli (Taheri-Araghi et al., 2015) and Viva-munk implements it. We measured Δ from the 92 divisions we did see (division length 3.61 µm, birth length 1.93 µm). Division lengths also vary a lot (CV 0.20), which fits an adder better than a strict sizer.
- **"Why does your twin's count lag (or lead) the real one?"** Cells in the first photo are at random points in their lives. Treated as newborns, they all divide a cycle late. Treated as average age, every long cell divides in the first 5 minutes, a burst the real data doesn't show. We drew each frame-0 cell's division length from the 92 real division lengths longer than it is now. The remaining gap: our count falls about 8% behind by 65 min (308 vs 337) while area stays on target. Real cells get smaller on average (2.30 → 2.08 µm² per cell), i.e. they divide at smaller sizes than a steady adder predicts.
- **"Why several random seeds?"** Each simulated cell draws its own growth rate and added length from the measured spread, so runs differ. We average **3** seeds (the spread is shown as faint lines on each plot) to report a stable number.
- **"Did you tune parameters to fit the curve?"** No. Every number comes from measuring individual cells, not from fitting the count curve. That's why the hidden 70 minutes is a real prediction.
- **"Where is the twin still wrong?"** The count runs about 5% low (cells divide a bit too late), so our hidden-period count is probably an underestimate. Area is the more reliable prediction (1.1% error).
- **"What would you do with more time?"** Use the COMSOL flow field as a food map; add slowdown under crowding (Viva-munk has a pressure option); fit each cell's own growth rate rather than a shared mean.

### 1.4 Biofilm: the 30-second version
> "From 17 microscope frames with labelled colony outlines, we tracked each colony's centre over time, measured how far it moved (net displacement and total path), and compared that with a supplied breakup score. Colony **33** moved farthest (37.2 px from where it started); colony **27** fragmented most (breakup score up 45 points, crossing our threshold of 40 at frame 8). Colony 33 also crossed 40 later (frame 14), colony 41 was already above 40 from the first frame, and the rest never crossed. A caution: a centre can move because the colony changes shape, not just because it travels, and the breakup score is an indicator, not a count of released cells."

---

## 2. Challenge 1: Digital Twin

Full working plan: [digital-twin/PLAN.md](digital-twin/PLAN.md).

### 2.1 The idea
A **digital twin** is a computer simulation of a real thing that behaves like the real thing. The organisers grew **E. coli** bacteria in a tiny chamber on a microscope chip and photographed it every 5 minutes. We get the first photo (248 cells) and the real data for the first 65 minutes. Our simulation starts from that photo and uses rules measured from the data to predict the next 70 minutes, which are hidden from us. The closer our predicted cell count and area are to reality, the better.

### 2.2 The biology
- **E. coli** is a rod-shaped bacterium about 1 µm wide and 2–5 µm long (1 µm = a thousandth of a millimetre). From above it looks like a **capsule**: a rectangle with a half-circle at each end.
- **Growth.** A cell gets longer but not wider. Growth is usually **exponential**: the same *percentage* each minute, not the same amount. Plotting `log(length)` against time turns exponential growth into a straight line. The slope is the **growth rate α**, and the **doubling time** is `ln(2) / α`.
- **Division.** When a cell is long enough, it splits in the middle into two **daughters**. There are two classic models of *when*:
  - **Sizer:** it divides at a fixed length.
  - **Adder:** it divides after adding a fixed length **Δ** since its own birth, whatever its birth size. E. coli is known to be an adder; we show it from the data.
- **Position.** Food arrives through the open side, so cells near it may grow faster than cells deep inside.
- **Pushing.** Growing cells push their neighbours. Cells pushed out of the open side wash away.

### 2.3 The chamber
- It's 34 µm wide (x) by 60 µm tall (y), with the origin at the **top-left**. **y points down**, as in images.
- It's closed on the left (x=0), top and bottom, and **open on the right (x=34)**, where flowing growth medium (food) passes by.
- 1 pixel = 0.0645 µm, and frames are 5 min apart. Frames 0–13 are given (0–65 min) and frames 14–27 are hidden (70–135 min).

### 2.4 The data
| File | One row is… | Key columns |
|---|---|---|
| `frame0_cells.csv` | a cell in the first photo | `x_um, y_um` (centre), `length_um` (total, tip to tip), `width_um`, `angle_rad`, `area_um2` |
| `tracks_0-13.csv` | a cell in one frame | the same, plus `frame, time_min, cell_id, parent_id`. Follow one `cell_id` to watch it grow. |
| `lineage_0-13.csv` | a cell over its life | `first_frame, last_frame, parent_id` (0 = already there at frame 0), `ends_in_window` (it disappeared in frames 0–13, usually by dividing) |
| `real_counts_0-13.csv` | a frame | `cells` and `total_area_um2`: **what we're scored against** (248 → 337 cells over 65 min) |
| `real_masks_0-13.npz` | stack of images | each pixel = which cell is there (0 = background). Used to draw the real cells in the video. |
| `comsol_flow/` | flow grid | liquid speed at each 1 µm point, from a **COMSOL** physics model of this chip. The cells don't drift with it; it's a hint about where fresh food reaches. |

### 2.5 The software
**Vivarium** (Python package `process-bigraph`) builds simulations from small, swappable parts:

| Part | Meaning | In our twin |
|---|---|---|
| **State** | everything that exists now | all cells: position, angle, length, width |
| **Process** | code that does one job each time step: reads the state, returns changes | grow and divide; physics |
| **Step** | runs right after the processes every tick | remove cells that left the chamber |
| **Wires** | which part of the state a process touches | `cells` ↔ physics |
| **Document** | a dict describing the state and all processes | what `build_document()` makes |
| **Composite** | runs the document's clock | `Composite(spec, core=core)` |
| **Emitter** | the recorder | gives us cell counts per frame |

**Viva-munk** (package `multi-cell`) provides ready-made bacteria processes:
- `PymunkProcess`: 2D physics. Cells are rigid capsules that push each other in a box. (**pymunk** is the physics engine underneath.)
- `AdderGrowDivide`: each cell grows exponentially at its own α and divides after adding its own Δ. Each cell's α and Δ are drawn randomly around our measured mean and spread.
- `RemoveCrossing`: deletes cells that cross x = 34.

Two details worth mentioning to judges, because they show care:
- In Viva-munk, a cell's `length` is only the straight middle part. We convert: `length = total_length − width`.
- Cells in the first photo are mid-life, not newborn. We gave each one an estimated birth length so they don't all divide late.

### 2.6 Scoring
- **% error** = for each frame, |twin − real| ÷ real × 100, averaged. It's computed for cell **count** and total **area**, and lower is better.
- Judges also weigh *reasoning*: rules measured, added one at a time, each effect shown.
- The hand-in is one Google Colab notebook that runs top to bottom on its own.

### 2.7 The final figure
**(a)** cell count and **(b)** total area, each divided by its starting value so every line starts at 1. One coloured line per rule set (growth; + division; + position), the real data as dots, and the hidden 70–135 min shaded grey. Underneath is the % error table, plus a video of our twin beside the real cells.

---

## 3. Challenge 2: Biofilm dispersion

- **Biofilm:** bacteria living stuck together in clumps (colonies) on a surface. **Dispersion** is the clumps breaking up and cells leaving.
- **Data:** 17 microscope frames (TIFF images); colony masks, where each pixel holds the ID of the colony there; and a supplied 0–100 **breakup score** per colony per frame. The score is the organisers' fragmentation indicator, not a % of cells released. Source: Chou et al. (2026), Supplementary Video 1.
- **What we measured:**
  - **centroid:** a colony's centre (average x, y of its mask pixels);
  - **displacement:** straight-line distance from its first centre;
  - **step distance:** movement since the previous frame;
  - **cumulative distance:** the total path length;
  - **breakup change:** score now minus first score;
  - **first threshold frame:** the first frame with score ≥ 40.
- **Missing frames:** if a colony isn't visible in a frame, we record NaN (not zero) and don't count a step across the gap.
- **Units:** pixels and frames, because the physical scale isn't verified.
- **Grading:** 70 points come from automatic comparison of our numbers (to 0.05 px). 30 points cover the overlay, animation, figure and a 100–150 word interpretation.
- **Limitations to mention:** a centroid moves when a colony changes shape; a breakup score doesn't prove cells were released; only some colonies were labelled.

---

## 4. How we worked (team, agents, board)

| Thing | What it is |
|---|---|
| **Split** | One challenge each, done in parallel: Alex on the Digital Twin, Brandon on Biofilm. |
| **AI agents** | Each of us directed a coding AI (Claude) that read the data and wrote and ran code. We made the decisions and checked the results. |
| **The board** | A pinned GitHub issue the two agents post to, so each knows what the other is doing (`tools/board`). |
| **This repo** | One folder per challenge (`digital-twin/`, `biofilm/`); `shared/` only for pieces both use. |
| **`art/`** | A small logger that records the size of our work every minute (`art/worklog.jsonl`), for a generative-art piece of the hackathon at the end. |

---

## 5. Tools and file formats

| Name | What it is |
|---|---|
| **Google Colab** | Free Jupyter notebooks in the browser on Google's servers. "Self-contained" means **Runtime → Restart and run all** works in a fresh Colab. |
| **Jupyter notebook (`.ipynb`)** | Code cells plus their saved outputs (plots, tables, videos) and text cells. |
| **pandas / numpy / matplotlib** | Tables / arrays and maths / plots in Python. |
| **`.csv` / `.npz` / `.tif` / GIF** | Text table / bundle of numpy arrays / microscope image / animation (embedded as bytes in the notebook). |
| **pin** | An exact package version, so results are reproducible. |

---

## 6. Glossary

- **α (alpha), growth rate:** how fast a cell grows exponentially. Doubling time = ln 2 ÷ α.
- **Δ (delta), added length:** in the adder model, length added between birth and division.
- **Adder / sizer / timer:** divide after adding a fixed length / at a fixed size / after a fixed time.
- **Capsule area:** (L − w)·w + π·w²/4.
- **CV:** standard deviation ÷ mean, i.e. how much cells differ from each other.
- **Frame:** one photo; 5 min apart here.
- **Lineage:** the family tree of divisions.
- **Mask:** an image whose pixels hold object IDs (0 = background).
- **Monolayer:** cells in a single flat layer, as on this chip.
- **Seed:** the number that fixes a run's random choices.
- **Window:** the 34 × 60 µm area the camera sees. Only cells inside it count.
