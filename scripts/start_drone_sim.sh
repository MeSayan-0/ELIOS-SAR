#!/usr/bin/env bash

# ============================================================
# ELIOS-SAR | DRONE SIMULATION + GCS STARTUP (WSL-COMPATIBLE)
# ============================================================
# Starts:
#   1. PX4 SITL + Gazebo x500 (interactive TTY via tmux)
#   2. MicroXRCE-DDS Agent (:8888)
#   3. rosbridge WebSocket (:9090)
#   4. PX4 ROS 2 Command Bridge
#   5. PX4 Offboard Setpoint Controller
#   6. GCS Backend (:8000)
#   7. GCS Frontend (:5173)
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PX4_DIR="${PX4_DIR:-$HOME/PX4-Autopilot}"
ROS_SETUP="/opt/ros/jazzy/setup.bash"
GCS_ROS_WS="$PROJECT_ROOT/ros2_ws"
SESSION="elios_drone"

echo "============================================================"
echo " Starting ELIOS-SAR Drone Simulation & GCS in WSL"
echo "============================================================"

# 1. Clean up any existing instances
tmux kill-session -t "$SESSION" 2>/dev/null || true
pkill -f "MicroXRCEAgent" 2>/dev/null || true
pkill -f "rosbridge_websocket" 2>/dev/null || true
pkill -f "ellios_sar_px4" 2>/dev/null || true
pkill -f "node src/server.js" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true
pkill -f "gz sim" 2>/dev/null || true
pkill -f "px4" 2>/dev/null || true
sleep 2

# 2. Setup PX4 parameters
if [ -f "$PROJECT_ROOT/scripts/setup_px4_params.sh" ]; then
    bash "$PROJECT_ROOT/scripts/setup_px4_params.sh" || true
fi

# 3. Create tmux session with first window: PX4 SITL + Gazebo
tmux new-session -d -s "$SESSION" -n "px4" \
    "source '$ROS_SETUP' && cd '$PX4_DIR' && make px4_sitl gz_x500; exec bash"

# 4. Window 1: MicroXRCE-DDS Agent
tmux new-window -t "$SESSION" -n "microxrce" \
    "source '$ROS_SETUP' && echo 'Starting MicroXRCEAgent...' && sleep 8 && MicroXRCEAgent udp4 -p 8888; exec bash"

# 5. Window 2: rosbridge WebSocket server (:9090)
tmux new-window -t "$SESSION" -n "rosbridge" \
    "source '$ROS_SETUP' && source '$GCS_ROS_WS/install/setup.bash' && echo 'Starting rosbridge...' && sleep 10 && ros2 launch rosbridge_server rosbridge_websocket_launch.xml; exec bash"

# 6. Window 3: PX4 ROS 2 Bridge
tmux new-window -t "$SESSION" -n "px4_bridge" \
    "source '$ROS_SETUP' && source '$GCS_ROS_WS/install/setup.bash' && echo 'Starting PX4 Bridge...' && sleep 14 && ros2 run ellios_sar_px4_bridge px4_bridge; exec bash"

# 7. Window 4: Offboard Controller
tmux new-window -t "$SESSION" -n "offboard" \
    "source '$ROS_SETUP' && source '$GCS_ROS_WS/install/setup.bash' && echo 'Starting Offboard Controller...' && sleep 16 && ros2 run ellios_sar_px4_offboard offboard_controller; exec bash"

# 8. Window 5: GCS Backend (:8000)
tmux new-window -t "$SESSION" -n "backend" \
    "cd '$PROJECT_ROOT/gcs/backend' && echo 'Starting GCS Backend...' && sleep 16 && node src/server.js; exec bash"

# 9. Window 6: GCS Frontend (:5173)
tmux new-window -t "$SESSION" -n "frontend" \
    "cd '$PROJECT_ROOT/gcs/frontend' && echo 'Starting GCS Frontend...' && sleep 5 && npm run dev -- --host 0.0.0.0; exec bash"

# Automatically apply PX4 preflight bypass parameters once PX4 boots
(
    sleep 15
    tmux send-keys -t "$SESSION:0" "param set NAV_DLL_ACT 0" Enter
    tmux send-keys -t "$SESSION:0" "param set NAV_RCL_ACT 0" Enter
    tmux send-keys -t "$SESSION:0" "param set COM_RC_IN_MODE 1" Enter
    tmux send-keys -t "$SESSION:0" "param save" Enter
) >/dev/null 2>&1 &

echo ""
echo "============================================================"
echo " All services launched inside tmux session: $SESSION"
echo "============================================================"
echo " To view any window or debug logs in real time, run:"
echo "   tmux attach -t $SESSION"
echo " (Press Ctrl+B then 0..6 to switch windows, Ctrl+B then D to detach)"
echo ""
echo " Services:"
echo "   • PX4 SITL + Gazebo : Window 0 (px4)"
echo "   • MicroXRCE-DDS     : Window 1 (microxrce) [UDP 8888]"
echo "   • ROSBridge         : Window 2 (rosbridge) [WS 9090]"
echo "   • PX4 Bridge        : Window 3 (px4_bridge)"
echo "   • Offboard Ctrl     : Window 4 (offboard)"
echo "   • GCS Backend       : Window 5 (backend)    [HTTP/WS 8000]"
echo "   • GCS Frontend      : Window 6 (frontend)   [http://localhost:5173]"
echo "============================================================"
