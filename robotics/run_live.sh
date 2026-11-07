#!/usr/bin/env bash
# Run the live OD -> arm test from a terminal and watch every reading as it arrives.
# Usage (from the repo root):  robotics/run_live.sh [minutes]      (default 10)
# Needs: Server_320.py running on the arm's Pi, this laptop on the same WiFi, no other Python session connected.
set -e
cd "$(dirname "$0")"
OUT="evidence/arm/live_run_$(date +%Y%m%d_%H%M%S).txt"
cat od.py arm.py > /tmp/robotics_live.py
echo "Running live test for ${1:-10} min; output also saved to robotics/$OUT"
MPLBACKEND=Agg OD_WATCH_MINUTES="${1:-10}" ARM_IP="${ARM_IP:-192.168.8.149}" \
  ../digital-twin/.venv/bin/python -u /tmp/robotics_live.py 2>&1 | tee "$OUT"
