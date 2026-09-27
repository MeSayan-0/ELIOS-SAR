#!/bin/bash

# ============================================================
# ELIOS-SAR
# FULL SYSTEM STOP SCRIPT
# ============================================================
#
# Stops the complete ELIOS-SAR simulation ecosystem.
#
# DOES NOT:
#   - delete files
#   - delete ROS workspace
#   - delete Gazebo models
#   - delete PX4
#   - modify GCS source
#   - modify configuration
#
# ============================================================

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PX4_DIR="${PX4_DIR:-$HOME/PX4-Autopilot}"


banner()
{
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
    echo ""
}


clear

banner "ELIOS-SAR FULL SYSTEM STOP"

echo "Stopping all ELIOS-SAR simulation processes..."
echo ""


# ============================================================
# 1. DEMO NODE
# ============================================================

echo "[1/12] Stopping Demo Node..."

pkill -f "ellios_sar_demo" 2>/dev/null || true


# ============================================================
# 2. FRONTEND / VITE
# ============================================================

echo "[2/12] Stopping GCS Frontend..."

pkill -f "node.*vite" 2>/dev/null || true


# ============================================================
# 3. BACKEND
# ============================================================

echo "[3/12] Stopping GCS Backend..."

pkill -f "node src/server.js" 2>/dev/null || true


# ============================================================
# 4. PX4 COMMAND BRIDGE
# ============================================================

echo "[4/12] Stopping PX4 ROS2 Bridge..."

pkill -f "ellios_sar_px4_bridge" 2>/dev/null || true


# ============================================================
# 5. OFFBOARD CONTROLLER
# ============================================================

echo "[5/12] Stopping Offboard Controller..."

pkill -f "ellios_sar_px4_offboard" 2>/dev/null || true


# ============================================================
# 6. ROSBRIDGE
# ============================================================

echo "[6/12] Stopping rosbridge..."

pkill -f "rosbridge_websocket" 2>/dev/null || true


# ============================================================
# 7. SLAM TOOLBOX
# ============================================================

echo "[7/12] Stopping SLAM Toolbox..."

pkill -f "async_slam_toolbox_node" 2>/dev/null || true


# ============================================================
# 8. STATIC TF
# ============================================================

echo "[8/12] Stopping Static TF..."

pkill -f "static_transform_publisher" 2>/dev/null || true


# ============================================================
# 9. ROVER GAZEBO BRIDGES
# ============================================================

echo "[9/12] Stopping ROS-Gazebo Bridges..."

pkill -f "ros_gz_bridge" 2>/dev/null || true


# ============================================================
# 10. MICRO XRCE-DDS
# ============================================================

echo "[10/12] Stopping MicroXRCE-DDS Agent..."

pkill -f "MicroXRCEAgent" 2>/dev/null || true


# ============================================================
# 11. PX4 SITL
# ============================================================

echo "[11/12] Stopping PX4 SITL..."

pkill -f "$PX4_DIR/build/px4_sitl_default/bin/px4" 2>/dev/null || true
pkill -f "make px4_sitl gz_x500" 2>/dev/null || true


# ============================================================
# 12. ALL GAZEBO
# ============================================================

echo "[12/12] Stopping Gazebo..."

pkill -f "gz sim" 2>/dev/null || true


# ============================================================
# WAIT
# ============================================================

echo ""
echo "Waiting for processes to terminate..."
sleep 5


# ============================================================
# VERIFY
# ============================================================

banner "VERIFYING ELIOS-SAR SHUTDOWN"


FOUND=0


check_process()
{
    local NAME="$1"
    local PATTERN="$2"

    if pgrep -f "$PATTERN" >/dev/null 2>&1
    then
        echo "WARNING: Still running -> $NAME"
        FOUND=1
    else
        echo "STOPPED : $NAME"
    fi
}


check_process "Demo Node" "ellios_sar_demo"
check_process "Vite" "node.*vite"
check_process "Backend" "node src/server.js"
check_process "PX4 Bridge" "ellios_sar_px4_bridge"
check_process "Offboard" "ellios_sar_px4_offboard"
check_process "rosbridge" "rosbridge_websocket"
check_process "SLAM" "async_slam_toolbox_node"
check_process "Static TF" "static_transform_publisher"
check_process "ROS-Gazebo Bridge" "ros_gz_bridge"
check_process "MicroXRCE-DDS" "MicroXRCEAgent"
check_process "PX4 SITL" "$PX4_DIR/build/px4_sitl_default/bin/px4"
check_process "Gazebo" "gz sim"


echo ""

if [ "$FOUND" -eq 0 ]
then

    banner "ELIOS-SAR SYSTEM STOPPED"

    echo "All ELIOS-SAR simulation processes are stopped."
    echo ""
    echo "No project files were deleted."
    echo "No configuration was modified."
    echo ""
    echo "You can start the complete system again with:"
    echo ""
    echo "$PROJECT_ROOT/scripts/start_elios_sar_full.sh"
    echo ""

else

    banner "ELIOS-SAR STOP COMPLETED WITH WARNINGS"

    echo "Some processes may still be running."
    echo ""
    echo "Check manually with:"
    echo ""
    echo "ps aux | grep -E 'px4|gz sim|rosbridge|ros_gz_bridge|slam|ellios_sar|vite|server.js|MicroXRCEAgent'"
    echo ""
fi
