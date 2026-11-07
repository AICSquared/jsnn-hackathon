# Problem-solving log: Alex + Claude (Claude Code, Opus 5.5)

Real examples from the hackathon, for the AI report. Times are UTC on Nov 7, 2026.
"Time saved" figures are **estimates** by the agent, not measurements; treat them as rough.

| # | Time | Problem | How it was found | How it was solved | Est. time saved |
|---|---|---|---|---|---|
| 1 | 15:58 | The organisers' library treats `length` as the rod's middle part only, not tip to tip | Read the Viva-munk source before writing code | Convert with length − width; check that total area at t=0 matches the real 570 µm² (got 569.0) | 30–60 min of chasing a wrong colony size |
| 2 | 16:05 | The simulator only has closed boxes, but the chamber is open on one side | Read the physics process source (walls on all 4 sides) | Physics box 10 µm wider, plus a step that deletes cells past x = 34 (the organisers' own trick in a script we found) | ~30 min |
| 3 | 16:08 | Only 2 complete cell cycles in the 65-minute window, so the division rule can't be measured directly | Measurement showed doubling ≈ 144 min > window | Estimate Δ from mean division length − mean birth length; say so honestly in the notebook | Avoided a silently wrong rule |
| 4 | 16:24 | The twin's cell count jumped 10% in the first 5 minutes | Agent inspected its own output figure | Frame-0 cells drew division lengths from the 92 real divisions instead of all being "average age" | ~20 min |
| 5 | 16:40 | Notebook crashed in Colab (`cannot reify schema Array`) but worked locally | User pasted the Colab error and package versions | Recreated Colab's versions locally, isolated **plum-dispatch 2.9.0** as the cause, pinned 2.10.1, and auto-restart once | 1–2 h of guessing |
| 6 | 17:30 | Live OD API returned Cloudflare error 1033 and the docs site was unreachable | `curl` and fetch attempts | Read the API routes straight from the Pioreactor open-source code; designed record/replay so work could continue offline | Unblocked the robotics plan |
| 7 | 18:32 | Biofilm GIF lacked the colony overlays the organisers asked for | Checked the notebook against the organisers' 6-item list | Asked Brandon's agent on the board; it fixed and merged it in ~6 min | Prevented a lost requirement |
| 8 | 18:45 | Biofilm numbers needed to be right to 0.05 px (auto-graded) | — | Independent re-implementation matched every value to ~10⁻¹² px | Confidence before submission |
| 9 | 19:15 | Arm is the Pi version; the manual's remote-control chapter was missing from the PDF text | Searched the 517-page manual | Read the official `Server_320.py` from the manufacturer's GitHub (port 9000, `/dev/ttyAMA0`); added an on-board fallback in case venue WiFi blocks devices | ~30 min |

## Mistakes the agent made, and how they were caught
- **Posted on the board before a file was saved** (robotics plan, 17:31): a hook blocked the write. The agent noticed, saved the file, and posted a correction.
- **Edited files on the wrong branch** (arm.py, 19:16): the edit failed, but a notebook-only commit went out with a post claiming the change. The agent checked the commit's file list, re-applied the change, and posted a correction.
- **Count error got slightly worse (3.95% → 4.79%) after a fix**: the agent kept the more honest model (no artificial burst) and explained the trade-off rather than chasing the lower number.

## How work was divided
- One challenge per person in parallel (Digital Twin: Alex; Biofilm: Brandon). Robotics: Brandon on the reactor and OD data, Alex on the arm, meeting at one function (`latest_od`).
- Agents coordinated through a GitHub-issue board with ACK / DONE / BLOCKED / STATUS labels (added to AGENTS.md mid-event after an agent went quiet for ~1 h).
- Humans decided: work split, merges, submissions, hardware. Agents: reading docs and source, writing and running code, verifying, drafting docs and emails.

## Working alongside the AI: how humans and agents shared the work

The agent didn't work alone. It regularly stopped to ask for decisions, sent us to do things only a person could, and took corrections mid-task.

**The AI asked for clarification before committing to a direction**
- At planning time it asked which challenge the plan should cover (a second challenge's zip had arrived unexpectedly), how much time we had, and how to split the work. We answered "Digital Twin for Alex, assign the other to Brandon, 2 hours".
- For the robotics bonus it asked which hardware we had, who should own it, what the deliverable should be (a Colab notebook can't drive a USB arm), and the time budget. We answered "plan for both, split it, script + Colab doc, 1 hour", and the plan was built around those answers.
- It asked before every merge into `main` and before every outward action (posting on others' behalf, drafting email). Merges happened only after "Yes, merge it".

**The AI asked us to run things on our side, or go somewhere**
- **Colab debugging:** the agent couldn't see Colab, so it asked Alex to run the notebook there, paste the red error block, download the run, then run two `pip list` / `pip freeze` commands. Those two pastes let it isolate the faulty package (plum-dispatch 2.9.0) in minutes.
- **Hardware:** it asked us to check the arm's model (M5 vs Pi), plug in the emergency stop, power the arm, and find its IP address. It also asked us to check whether the Pioreactor kit came with a Raspberry Pi before fetching Alex's Pi 5 from the dorm.
- **Submissions:** it prepared the files and the email drafts, but sending stayed with Alex. Attaching the 7.9 MB notebook and pressing Send were human steps by design.
- **Teammates:** when Brandon's agent went quiet, it suggested messaging Brandon directly (Discord or in person) rather than taking over his files.

**We corrected and steered the AI mid-task**
- "The deliverable will be a Colab doc", "put everything in a single repo", "commit frequently", "post on the board every time": each became a standing rule, and the agent moved its reference folders into the repo, set up per-commit board posts, and saved them to memory.
- "The guide will be used to explain our work to judges": the agent restructured GUIDE.md around a 30-second pitch and likely judge questions.
- "The wording makes the arm sound like a prize": fixed in the README.
- When Brandon's agent went silent for about an hour, Alex had the agent add ACK / DONE / BLOCKED / STATUS rules to AGENTS.md. Brandon's agent adopted them within minutes.

**Agents coordinated with each other, with humans in charge**
- The two agents talked only through the board. Alex's agent asked for a handoff before touching Brandon's files rather than editing them, and Brandon's agent asked Brandon before running the metrics script on his logs.
- Brandon's agent caught 4 wording errors in Alex's README; Alex's agent caught a missing requirement (GIF overlays) in Brandon's notebook.

**The AI also taught**
- Alex used `/rederive`: the agent posed the design problems (how to load real cells into a simulator; how to check the conversion) and Alex re-derived the solutions himself, with progress logged locally.
