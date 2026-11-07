#!/usr/bin/env bash
# Run the live OD -> arm test from a terminal and watch every reading as it arrives.
# Usage (from the repo root):  robotics/run_live.sh [minutes]      (default 10)
# Needs: Server_320.py running on the arm's Pi, this laptop on the same WiFi, no other Python session connected.
set -e
cd "$(dirname "$0")"
OUT="evidence/arm/live_run_$(date +%Y%m%d_%H%M%S).txt"
RUN=".live_run.py"                       # inside robotics/ so od.py saves its log to robotics/evidence/
cat od.py arm.py > "$RUN"
trap 'rm -f "$RUN"' EXIT
echo "Running live test for ${1:-10} min; output also saved to robotics/$OUT"
MPLBACKEND=Agg OD_WATCH_MINUTES="${1:-10}" ARM_IP="${ARM_IP:-192.168.8.149}" \
  ../digital-twin/.venv/bin/python -u "$RUN" 2>&1 | tee "$OUT"
