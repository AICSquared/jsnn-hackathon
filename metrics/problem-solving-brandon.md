# Problem-solving log: Brandon + Claude (Claude Code, Opus 5.5)

Real examples from the hackathon, for the AI report. Times are UTC on Nov 7, 2026.
"Time saved" figures are **estimates** by the agent, not measurements; treat them as rough.

| # | Time | Problem | How it was found | How it was solved | Est. time saved |
|---|---|---|---|---|---|
| 1 | 15:59 | The challenge zip in Downloads was a 346-byte `.webloc` link to a private Slack file, not the data | The agent read the file before trying to unzip it | Asked Brandon to download the real file in his browser; the extracted folder turned up next to it | Avoided a confusing unzip error |
| 2 | 16:05 | Biofilm data had no missing frames or scores, so the NaN rules in sections 5–7 (70 auto-graded points) would never be exercised | Inspected every colony's pixel count per frame before coding | Wrote the gap rules anyway and tested them on hand-made tracks with gaps, a late first sighting and the starter's worked example | Protection against hidden-test data |
| 3 | 16:08 | Results had to be right to 0.05 px | — | Recomputed every centroid and distance a second, vectorised way: max difference 5 × 10⁻¹³ px | Confidence before submission |
| 4 | 16:09 | Interpretation came out at 168 words (limit 100–150) | Word count before committing | Rewrote to 148 words, keeping both named colonies and the limitation | — |
| 5 | 17:37 | `od.py` returned the newest reading across *all* vessels, so the value jumped between them (0.01 → 0.5 → 0.02) | Tests against a fake local API | Pinned one series per run (`OD_SERIES`, else the first label) | Prevented the arm firing on noise |
| 6 | 18:32 | Biofilm GIF lacked the colony overlays the organisers' item 5 asked for | Alex's agent checked the notebook against the brief and posted on the board | Patched the starter's GIF helper in the build script, re-ran, and verified the graded results were byte-identical | ~6 min end to end |
| 7 | 19:21 | The metrics script read the wrong log folder for this session (started from the home folder, not the repo) | Listed which Claude log folders actually existed before running anything | Flagged it on the board; Alex's agent added `--session` | Avoided near-empty metrics |
| 8 | 19:43 | The reactor answered "this unit isn't the leader" | Read-only GETs from Brandon's Mac (the only laptop on the reactor's WiFi) | Confirmed it was a worker; the leader `oliveirapioreactor01` was powered on | — |
| 9 | 19:46 | API was up but the newest OD reading never changed (403 points, stuck at 03:28Z) | Streamed 60 s, then checked 3 more times | Reported BLOCKED: OD reading wasn't running on the leader; Alex started it in the UI | Avoided presenting stale data as live |
| 10 | 19:53 | After OD reading started, `latest_od` still returned the old point: the leader's clock read 2025-10-01, so new points sorted *before* old ones | Alex's agent spotted it in the raw data | Take the newest point at or before the leader's own clock (`/unit_api/health`); tested with a wrong and a right clock | Objective 3 working in ~5 min |
| 11 | 21:45 | A multi-level arm run would have moved the arm at start-up if a vial was already in | Dry run against live OD | The first reading only primes the trigger state | Prevented an unexpected arm move |
| 12 | 22:00 | The table limiter's "lift, don't lower" choice compared the height of the shoulder joint, which never moves, so every option tied | Printed the predicted heights for each level from Alex's real start pose | Rank by tool-tip height; added a self-check that bending back toward upright raises the tip | Made the safety rule actually work |

## Mistakes the agent made, and how they were caught
- **Background board watchers with hidden output (3 times):** the agent chained a board `wait` onto another command with its output discarded, which could have silently swallowed teammates' posts. Each time it noticed, killed it, re-ran `unread` to confirm nothing was lost, and restarted a proper watcher. It also once left two watchers running at the same time, against the one-watcher rule.
- **Assumed the session logs could simply be added together:** the three log files overlapped (each restart copied the earlier conversation in), so the first totals were 2–3× too high. The agent checked the overlap (>99% shared entries) and re-ran on the newest log only.
- **Started work on the wrong base:** the robotics branch was first cut from Alex's plan branch; Alex asked for main, and the agent recreated it (no commits were lost).

## Working alongside the AI: how Brandon and the agent shared the work

**The AI asked for decisions before acting**
- It asked before every push, merge and outward post on the team's behalf, and before running the metrics collector on Brandon's private session logs. "Take it", "merge PR 12", "yes" were Brandon's calls.
- For the arm feature it gave a plan first. Brandon changed it ("lowest level at the wrist, highest at the base", "keep 15°", "add a limiter so the arm doesn't hit the table"), and the build followed those answers.
- When a teammate handed over `arm.py`, it asked Brandon whether to take it rather than accepting on his behalf.

**The AI asked Brandon to do things only a person could**
- Download the real challenge zip from Slack (it couldn't use his login), upload data files to Colab, and send the submission email himself.
- Assemble and photograph the Pioreactor, screenshot the web UI, and keep his Mac on the reactor's WiFi, which turned out to be the only laptop that could reach it.
- Keep someone at the arm with the emergency stop in reach before any real-arm test.

**Brandon steered the AI mid-task**
- Shared the arm's 517-page manual; the agent pulled out the WiFi and socket-server steps (pp. 218–228, 356–359) and posted them for Alex, and later used the manual's DH table (p. 138) for the table limiter.
- Asked for the Track A plan to be sent to Alex, and for the poster's biofilm column to be checked; the agent posted corrections rather than editing Alex's files.
