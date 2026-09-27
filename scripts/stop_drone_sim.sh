#!/usr/bin/env bash

# ============================================================
# ELIOS-SAR | STOP DRONE SIMULATION & GCS
# ============================================================

SESSION="elios_drone"

echo "Stopping ELIOS-SAR Drone Simulation & GCS..."

tmux kill-session -t "$SESSION" 2>/dev/null || true
pkill -f "MicroXRCEAgent" 2>/dev/null || true
pkill -f "rosbridge_websocket" 2>/dev/null || true
pkill -f "ellios_sar_px4" 2>/dev/null || true
pkill -f "node src/server.js" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true
pkill -f "gz sim" 2>/dev/null || true
pkill -f "px4" 2>/dev/null || true

echo "All services stopped."
