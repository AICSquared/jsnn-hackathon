#!/usr/bin/env bash
# Low-priority art logger: appends one JSON line per minute to art/worklog.jsonl
# describing the shape of the team's work (no file contents, just sizes/counts).
# Every 5th tick it also fetches origin (Brandon's pushes) and counts board posts.
# Stop: pkill -f art/snapshot.sh
cd "$(dirname "$0")/.." || exit 1
OUT=art/worklog.jsonl
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
tick=0
while true; do
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  dirs=""
  for d in digital-twin biofilm shared tools; do
    if [ -d "$d" ]; then
      files=$(find "$d" -type f | wc -l | tr -d ' ')
      bytes=$(find "$d" -type f -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')
    else files=0; bytes=0; fi
    dirs="$dirs\"$d\":{\"files\":$files,\"bytes\":$bytes},"
  done
  dirty=$(git diff --numstat 2>/dev/null | awk '{a+=$1;d+=$2} END{printf "{\"add\":%d,\"del\":%d}", a, d}')
  local_commits=$(git rev-list --count HEAD 2>/dev/null || echo 0)
  remote=""
  if [ $((tick % 5)) -eq 0 ]; then
    git fetch -q origin 2>/dev/null
    alex=$(git log --all --author=alex -i --oneline 2>/dev/null | wc -l | tr -d ' ')
    brandon=$(git log --all --author=brandon -i --oneline 2>/dev/null | wc -l | tr -d ' ')
    posts=$(gh api "repos/$REPO/issues/${BOARD_ISSUE:-1}" -q .comments 2>/dev/null || echo null)
    remote=",\"commits_alex\":$alex,\"commits_brandon\":$brandon,\"board_posts\":$posts"
  fi
  echo "{\"ts\":\"$ts\",\"dirs\":{${dirs%,}},\"dirty\":$dirty,\"commits\":$local_commits$remote}" >> "$OUT"
  tick=$((tick + 1))
  sleep 60
done
