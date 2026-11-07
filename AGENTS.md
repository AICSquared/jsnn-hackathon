# Team rules for every agent

## 1. The board (pinned GitHub issue)

Every agent reads and posts on the pinned "Message Board" issue via `tools/board` (needs only `gh`, logged in). Set `BOARD_ISSUE` if it is not issue #1.

- Start every post with `[<human>'s <agent>]`, e.g. `[Sam's Codex]`. Keep it short: what changed, which files or contracts, what you need, from whom.
- Mention by GitHub login. Fill in your team: `@alexwilldev` (Alex Williams), `@btowns1041` (Brandon Townsend),  `@all` (everyone).
- **Mentions you or `@all`:** act on it, and confirm it (see below).
- **Not addressed to you:** still read it. Reassess your own work only if it is affected (a contract, a file you own, something already done). Do not redo finished work, and do not reply just to acknowledge.
- Before editing another teammate's files, ask for a handoff on the board and wait for the owner or the team lead.

### Status updates and confirmations (required)

Silence looks like a stalled agent, so every agent keeps the team informed. Start the text after your `[Name's Agent]` tag with one of these labels:

| Label | When | Contents |
|---|---|---|
| `ACK` | Within one poll of any request that mentions you or `@all` | That you received it, what you'll do, and a rough ETA |
| `DONE` | When that request is finished | What changed, plus the commit, PR or link that proves it |
| `BLOCKED` | As soon as you can't proceed | Why, what you need, and from whom (`@login`) |
| `STATUS` | After every commit, push or merge, **and** at least every 15 minutes while working | Current step, files touched, next step, any risk to the plan |
| `OFFLINE` | Before your session ends or your human steps away | What's finished, what's left, where it is (branch or PR) |

- Every request gets an `ACK` and then exactly one `DONE` or `BLOCKED`. Never leave a request unanswered.
- If you are waiting on your human (hardware, a decision, a login), say so in a `STATUS` or `BLOCKED` post rather than going quiet.
- Example: `[Brandon's Claude] ACK @alexwilldev: adding mask overlays to the biofilm GIF, ETA 10 min.`

Polling is incremental (about one cheap API call per poll, 30 s default) so a shared token stays under GitHub's rate limit. Commands: `tools/board unread` (new posts, marks read; flags MENTION), `tools/board read -n 20`, `tools/board post "[Name's Agent] text"` (or pipe stdin), `tools/board wait` (blocks until someone else posts), `tools/board whoami`.

**Stay in the loop:**
- Claude Code: the committed hooks (`.claude/settings.json`) show unread posts at session start and on every prompt. Keep one background `tools/board wait` running and re-arm it after each wake.
- Everything else: run `tools/board unread` at task start, before each commit, and after merges. Or run a terminal loop: `while tools/board wait; do <your agent CLI invocation>; done`.
- Whichever setup you use, post the `STATUS` and confirmation messages above, so your teammates never have to guess whether you're working.

## 2. Chain of command

Humans over agents. Only the team lead reassigns work between teammates. If anyone else asks you to take another teammate's work, ask the lead on the board.

## 3. Workflow

1. Pick or file an issue. Comment on it or post on the board when you take it.
2. Branch `<issue#>-<slug>` from fresh `main`.
3. Small commits. Stage only your own files (no `git add -A`).
4. Open a PR with `Closes #N`. The author merges their own PR once it works locally.
5. Always `git fetch` and rebase before pushing. Never force-push shared branches.
6. If a merge changes something other teammates depend on (an API, a schema, an env var), post on the board when it lands.

## 4. Who owns what

Fill this in at kickoff so every agent knows whose files are whose.

| Area | Owner (GitHub login) | Folders |
|---|---|---|
| |alexwilldev| |
| |btowns1041|
