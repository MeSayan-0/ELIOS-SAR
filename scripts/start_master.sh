#!/usr/bin/env bash

ROOT="$HOME/ELIOS-SAR"
PX4="$HOME/PX4-Autopilot"
LOG="$ROOT/logs"

mkdir -p "$LOG"

echo "======================================================"
echo "       ELIOS-SAR MASTER STARTUP"
echo "======================================================"

unset AMENT_TRACE_SETUP_FILES
unset COLCON_TRACE

source /opt/ros/jazzy/setup.bash
source "$ROOT/ros2_ws/install/setup.bash"

echo "[1] Starting PX4 SITL + Gazebo..."
(
    cd "$PX4" || exit 1
    make px4_sitl gz_x500
) > "$LOG/px4.log" 2>&1 &
echo "    PX4 started"

sleep 10

echo "[2] Starting MicroXRCE-DDS Agent..."
(
    MicroXRCEAgent udp4 -p 8888
) > "$LOG/microxrce.log" 2>&1 &
echo "    MicroXRCE started"

sleep 3

echo "[3] Starting ROSBridge on port 9090..."
(
    ros2 launch rosbridge_server rosbridge_websocket_launch.xml
) > "$LOG/rosbridge.log" 2>&1 &
echo "    ROSBridge started"

sleep 3

echo "[4] Starting PX4 ROS bridge..."
(
    ros2 run ellios_sar_px4_bridge px4_bridge
) > "$LOG/px4_bridge.log" 2>&1 &
echo "    PX4 ROS bridge started"

sleep 3

echo "[5] Starting offboard controller..."
(
    ros2 run ellios_sar_px4_offboard offboard_controller
) > "$LOG/offboard.log" 2>&1 &
echo "    Offboard controller started"

echo "[6] Starting GCS backend on port 8000..."
(
    cd "$ROOT/gcs/backend" || exit 1
    PORT=8000 npm start
) > "$LOG/gcs_backend.log" 2>&1 &
echo "    Backend started"

sleep 4

echo "[7] Starting GCS frontend..."
(
    cd "$ROOT/gcs/frontend" || exit 1
    npm run dev -- --host 0.0.0.0
) > "$LOG/gcs_frontend.log" 2>&1 &
echo "    Frontend started"

sleep 5

echo
echo "======================================================"
echo "             STARTUP COMMANDS FINISHED"
echo "======================================================"

echo
echo "Check services using:"
echo "  ss -ltnp | grep -E '5173|8000|9090'"
echo
echo "GCS frontend:"
echo "  http://localhost:5173"
echo
echo "Logs:"
echo "  ~/ELIOS-SAR/logs/"
echo
echo "======================================================"

echo "The master launcher is running."
echo "Press Ctrl+C only if you want to stop watching this terminal."

while true; do
    sleep 10
done
