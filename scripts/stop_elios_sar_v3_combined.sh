#!/usr/bin/env bash

echo "============================================================"
echo "ELIOS-SAR V3 COMBINED SYSTEM - STOP"
echo "============================================================"

echo
echo "Stopping ELIOS-SAR runtime..."

# ------------------------------------------------------------
# PX4
# ------------------------------------------------------------
pkill -TERM -f "px4_sitl_default/bin/px4" 2>/dev/null || true
pkill -TERM -f "Attaching PX4 to V3" 2>/dev/null || true

# ------------------------------------------------------------
# MicroXRCE-DDS
# ------------------------------------------------------------
pkill -TERM -f "MicroXRCEAgent" 2>/dev/null || true

# ------------------------------------------------------------
# ROS-Gazebo bridges
# ------------------------------------------------------------
pkill -TERM -f "ros_gz_bridge" 2>/dev/null || true
pkill -TERM -f "parameter_bridge" 2>/dev/null || true

# ------------------------------------------------------------
# SLAM
# ------------------------------------------------------------
pkill -TERM -f "slam_toolbox" 2>/dev/null || true

# ------------------------------------------------------------
# ROS bridge
# ------------------------------------------------------------
pkill -TERM -f "rosbridge_websocket" 2>/dev/null || true

# ------------------------------------------------------------
# ELIOS PX4 command bridge
# ------------------------------------------------------------
pkill -TERM -f "ellios_sar_px4_bridge" 2>/dev/null || true
pkill -TERM -f "px4_bridge" 2>/dev/null || true

# ------------------------------------------------------------
# GCS backend
# ------------------------------------------------------------
pkill -TERM -f "gcs/backend/src/server.js" 2>/dev/null || true
pkill -TERM -f "node.*server.js" 2>/dev/null || true

# ------------------------------------------------------------
# GCS frontend
# ------------------------------------------------------------
pkill -TERM -f "vite" 2>/dev/null || true
pkill -TERM -f "npm.*run dev" 2>/dev/null || true

# ------------------------------------------------------------
# GAZEBO
# IMPORTANT:
# Kill the GUI and server explicitly.
# ------------------------------------------------------------

# First try normal termination
pkill -TERM -f "gz sim gui" 2>/dev/null || true
pkill -TERM -f "gz sim -r" 2>/dev/null || true
pkill -TERM -f "gz sim" 2>/dev/null || true

sleep 2

# If Gazebo survives, force kill it
pkill -KILL -f "gz sim gui" 2>/dev/null || true
pkill -KILL -f "gz sim -r" 2>/dev/null || true
pkill -KILL -f "gz sim" 2>/dev/null || true

# Also catch Gazebo executable processes
pkill -KILL -f "/gz sim" 2>/dev/null || true

sleep 2

echo
echo "============================================================"
echo "VERIFYING RUNTIME"
echo "============================================================"

REMAINING=$(pgrep -af \
"px4_sitl_default/bin/px4|Attaching PX4 to V3|MicroXRCEAgent|gz sim|ros_gz_bridge|parameter_bridge|slam_toolbox|rosbridge_websocket|ellios_sar_px4_bridge|px4_bridge|vite|gcs/backend/src/server.js" \
|| true)

if [ -z "$REMAINING" ]; then
    echo
    echo "ALL ELIOS-SAR V3 PROCESSES STOPPED."
else
    echo
    echo "WARNING: Some processes are still running:"
    echo "$REMAINING"
fi

echo
echo "============================================================"
echo "ELIOS-SAR V3 STOP COMPLETE"
echo "============================================================"
