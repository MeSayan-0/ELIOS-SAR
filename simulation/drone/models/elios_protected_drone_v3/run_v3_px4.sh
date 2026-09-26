#!/usr/bin/env bash
set -eo pipefail

MODEL_NAME="elios_protected_drone_v3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PX4_DIR="${PX4_DIR:-$HOME/PX4-Autopilot}"
WORLD="${PX4_GZ_WORLD:-$PX4_DIR/Tools/simulation/gz/worlds/default.sdf}"
SERVER_CONFIG="$PX4_DIR/Tools/simulation/gz/server.config"
PX4_BIN="$PX4_DIR/build/px4_sitl_default/bin/px4"

[[ -f "$WORLD" ]] || { echo "ERROR: PX4 Gazebo world not found: $WORLD"; exit 1; }
[[ -f "$SERVER_CONFIG" ]] || { echo "ERROR: PX4 Gazebo server config not found: $SERVER_CONFIG"; exit 1; }
[[ -x "$PX4_BIN" ]] || { echo "ERROR: PX4 SITL binary not found/executable: $PX4_BIN"; exit 1; }
[[ -f "$MODEL_ROOT/$MODEL_NAME/model.sdf" ]] || { echo "ERROR: model not installed. Run install_elios_v3.sh first."; exit 1; }

source /opt/ros/jazzy/setup.bash
set -u
export PX4_GZ_STANDALONE=1
export PX4_SYS_AUTOSTART=4001
export PX4_SIM_MODEL="$MODEL_NAME"
export GZ_SIM_RESOURCE_PATH="$MODEL_ROOT:$PX4_DIR/Tools/simulation/gz/models:${GZ_SIM_RESOURCE_PATH:-}"
export GZ_SIM_SERVER_CONFIG_PATH="$SERVER_CONFIG"

if pgrep -x px4 >/dev/null 2>&1; then
  echo "ERROR: PX4 is already running. Stop it first if you want a clean launch."
  exit 1
fi

if gz topic -l >/dev/null 2>&1; then
  echo "Gazebo appears to be running already; reusing it."
else
  echo "Starting PX4 default Gazebo world..."
  gz sim -r -v 3 "$WORLD" &
  GZ_PID=$!
  trap 'kill "$GZ_PID" 2>/dev/null || true' EXIT INT TERM
  sleep 3
fi

echo "Starting PX4 SITL with $MODEL_NAME..."
cd "$PX4_DIR"
exec "$PX4_BIN"
