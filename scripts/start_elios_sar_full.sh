#!/bin/bash

# ============================================================
# ELIOS-SAR
# FULL ROVER + DRONE + GCS SIMULATION STARTUP
# ============================================================
#
# CANONICAL GCS PROJECT:
# /home/sayan/Desktop/ELIOS-SAR-main
#
# ROVER / MINE SIMULATION:
# /home/sayan/Elios_SAR_sim_ws
#
# PX4:
# /home/sayan/PX4-Autopilot
#
# ============================================================
#
# SYSTEM
#
# DRONE
#   PX4 SITL + Gazebo x500
#   MicroXRCE-DDS :8888
#   PX4 ROS2 command bridge
#   Offboard setpoint publisher
#
# ROVER / MINE
#   Mine Gazebo simulator
#   Rover LiDAR
#   Rover odometry
#   Rover cmd_vel
#   Gazebo TF
#   Static LiDAR TF
#   SLAM Toolbox
#
# GCS
#   rosbridge :9090
#   MERN backend :8000
#   React/Vite frontend :5173
#   Demo node LAST
#
# ============================================================
#
# SAFETY
#
# This script ONLY starts software.
#
# NO ARM
# NO TAKEOFF
# NO OFFBOARD COMMAND
# NO LAND
# NO RTL
# NO DOCK
# NO UNDOCK
#
# ============================================================

set -u

eval $(dbus-launch --sh-syntax)


# ============================================================
# PATHS (DYNAMIC & PORTABLE)
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PX4_DIR="${PX4_DIR:-$HOME/PX4-Autopilot}"

if [ -z "${ROS_SETUP:-}" ]; then
    if [ -f "/opt/ros/jazzy/setup.bash" ]; then
        ROS_SETUP="/opt/ros/jazzy/setup.bash"
    elif [ -f "/opt/ros/humble/setup.bash" ]; then
        ROS_SETUP="/opt/ros/humble/setup.bash"
    elif [ -f "/opt/ros/rolling/setup.bash" ]; then
        ROS_SETUP="/opt/ros/rolling/setup.bash"
    else
        ROS_SETUP="/opt/ros/jazzy/setup.bash"
    fi
fi

GCS_ROS_WS="$PROJECT_ROOT/ros2_ws"

MINE_WS="${MINE_WS:-$HOME/Elios_SAR_sim_ws}"

MINE_PKG_DIR="$MINE_WS/src/ellios_sar_mine"

BACKEND_DIR="$PROJECT_ROOT/gcs/backend"

FRONTEND_DIR="$PROJECT_ROOT/gcs/frontend"


# ============================================================
# MINE GAZEBO
# ============================================================

MINE_WORLD="$MINE_PKG_DIR/worlds/ellios_mine.sdf"

MINE_MODELS="$MINE_PKG_DIR/models"

MINE_SIM_RESOURCES="$MINE_MODELS:$MINE_PKG_DIR"


# ============================================================
# ROS ENVIRONMENT
# ============================================================

export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET


# ============================================================
# HELPER
# ============================================================

banner()
{
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
    echo ""
}


# ============================================================
# CHECK FILESYSTEM
# ============================================================

check_filesystem()
{
    banner "CHECKING ELIOS-SAR FILESYSTEM"

    REQUIRED_DIRS=(
        "$PROJECT_ROOT"
        "$PX4_DIR"
        "$GCS_ROS_WS"
        "$MINE_WS"
        "$MINE_PKG_DIR"
        "$BACKEND_DIR"
        "$FRONTEND_DIR"
    )

    for DIR in "${REQUIRED_DIRS[@]}"
    do
        if [ ! -d "$DIR" ]; then
            echo "ERROR: Required directory not found:"
            echo "$DIR"
            exit 1
        fi
    done


    # --------------------------------------------------------
    # GCS ROS workspace
    # --------------------------------------------------------

    if [ ! -f "$GCS_ROS_WS/install/setup.bash" ]; then
        echo "ERROR: GCS ROS workspace is not built:"
        echo "$GCS_ROS_WS/install/setup.bash"
        echo ""
        echo "Build it first:"
        echo ""
        echo "cd $GCS_ROS_WS"
        echo "source $ROS_SETUP"
        echo "colcon build --symlink-install"
        exit 1
    fi


    # --------------------------------------------------------
    # Mine world
    # --------------------------------------------------------

    if [ ! -f "$MINE_WORLD" ]; then
        echo "ERROR: Mine world not found:"
        echo "$MINE_WORLD"
        exit 1
    fi


    # --------------------------------------------------------
    # Mine models
    # --------------------------------------------------------

    if [ ! -d "$MINE_MODELS" ]; then
        echo "ERROR: Mine models directory not found:"
        echo "$MINE_MODELS"
        exit 1
    fi


    echo "Project root : $PROJECT_ROOT"
    echo "PX4          : $PX4_DIR"
    echo "GCS ROS WS   : $GCS_ROS_WS"
    echo "Mine WS      : $MINE_WS"
    echo "Mine package : $MINE_PKG_DIR"
    echo "Mine world   : $MINE_WORLD"
    echo "Backend      : $BACKEND_DIR"
    echo "Frontend     : $FRONTEND_DIR"
    echo ""

    echo "Filesystem check PASSED."
}


# ============================================================
# CLEAN OLD PROCESSES
# ============================================================

cleanup()
{
    banner "CLEANING OLD ELIOS-SAR RUNTIME"

    echo "[1/13] Stopping old PX4..."

    pkill -f "$PX4_DIR/build/px4_sitl_default/bin/px4" 2>/dev/null || true
    pkill -f "make px4_sitl gz_x500" 2>/dev/null || true


    echo "[2/13] Stopping old Gazebo..."

    pkill -f "gz sim" 2>/dev/null || true


    echo "[3/13] Stopping MicroXRCE-DDS..."

    pkill -f "MicroXRCEAgent" 2>/dev/null || true


    echo "[4/13] Stopping rosbridge..."

    pkill -f "rosbridge_websocket" 2>/dev/null || true


    echo "[5/13] Stopping PX4 bridge..."

    pkill -f "ellios_sar_px4_bridge" 2>/dev/null || true


    echo "[6/13] Stopping Offboard controller..."

    pkill -f "ellios_sar_px4_offboard" 2>/dev/null || true


    echo "[7/13] Stopping mine ros_gz bridges..."

    pkill -f "ros_gz_bridge" 2>/dev/null || true


    echo "[8/13] Stopping SLAM Toolbox..."

    pkill -f "async_slam_toolbox_node" 2>/dev/null || true


    echo "[9/13] Stopping static TF publisher..."

    pkill -f "static_transform_publisher" 2>/dev/null || true


    echo "[10/13] Stopping demo node..."

    pkill -f "ellios_sar_demo" 2>/dev/null || true


    echo "[11/13] Stopping backend..."

    pkill -f "node src/server.js" 2>/dev/null || true


    echo "[12/13] Stopping Vite..."

    pkill -f "node.*vite" 2>/dev/null || true


    echo "[13/13] Waiting for shutdown..."

    sleep 5

    echo ""
    echo "Cleanup complete."
}


# ============================================================
# TERMINAL 1
# PX4 SITL + GAZEBO x500
# ============================================================

start_px4()
{
    banner "STARTING PX4 SITL + GAZEBO"

    gnome-terminal \
        --title="ELIOS-SAR | 1 PX4 + Gazebo" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — PX4 + GAZEBO'
            echo '============================================================'

            source '$ROS_SETUP'

            cd '$PX4_DIR'

            echo ''
            echo 'Starting PX4 SITL + Gazebo x500...'
            echo ''

            make px4_sitl gz_x500

            exec bash
        "
}


# ============================================================
# TERMINAL 2
# MICRO XRCE-DDS AGENT
# ============================================================

start_microxrce()
{
    banner "STARTING MICRO XRCE-DDS AGENT"

    gnome-terminal \
        --title="ELIOS-SAR | 2 MicroXRCE :8888" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — MICRO XRCE-DDS'
            echo ' UDP 8888'
            echo '============================================================'

            source '$ROS_SETUP'

            sleep 10

            MicroXRCEAgent udp4 -p 8888

            exec bash
        "
}


# ============================================================
# TERMINAL 3
# MINE SIMULATOR + GAZEBO
# ============================================================

start_mine()
{
    banner "STARTING MINE SIMULATOR + GAZEBO"

    gnome-terminal \
        --title="ELIOS-SAR | 3 Mine Simulator" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — MINE SIMULATOR'
            echo '============================================================'

            source '$ROS_SETUP'

            cd '$MINE_PKG_DIR'

            export GZ_SIM_RESOURCE_PATH='$MINE_SIM_RESOURCES'

            echo ''
            echo 'Gazebo resource path:'
            echo \"\$GZ_SIM_RESOURCE_PATH\"
            echo ''

            echo 'Starting Mine Gazebo world...'
            echo ''

            gz sim -r -v 3 '$MINE_WORLD'

            exec bash
        "
}


# ============================================================
# TERMINAL 4
# ROVER LiDAR BRIDGE
# ============================================================

start_rover_scan_bridge()
{
    banner "STARTING ROVER LiDAR BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 4 Rover LiDAR Bridge" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — ROVER LiDAR'
            echo ' /rover/scan'
            echo '============================================================'

            source '$ROS_SETUP'

            cd '$MINE_PKG_DIR'

            sleep 12

            ros2 run ros_gz_bridge parameter_bridge \
            /rover/scan@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan

            exec bash
        "
}


# ============================================================
# TERMINAL 5
# ROVER ODOMETRY BRIDGE
# ============================================================

start_rover_odom_bridge()
{
    banner "STARTING ROVER ODOMETRY BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 5 Rover Odom" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — ROVER ODOMETRY'
            echo ' /rover/odom'
            echo '============================================================'

            source '$ROS_SETUP'

            cd '$MINE_PKG_DIR'

            sleep 12

            ros2 run ros_gz_bridge parameter_bridge \
            /rover/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry

            exec bash
        "
}


# ============================================================
# TERMINAL 6
# ROVER CMD_VEL BRIDGE
# ============================================================

start_rover_cmd_bridge()
{
    banner "STARTING ROVER CMD_VEL BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 6 Rover CMD" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — ROVER CONTROL'
            echo ' /rover/cmd_vel'
            echo '============================================================'

            source '$ROS_SETUP'

            cd '$MINE_WS'

            sleep 12

            ros2 run ros_gz_bridge parameter_bridge \
            /rover/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist

            exec bash
        "
}


# ============================================================
# TERMINAL 7
# TF BRIDGE
# ============================================================

start_tf_bridge()
{
    banner "STARTING TF BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 7 TF Bridge" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — TF BRIDGE'
            echo '============================================================'

            source '$ROS_SETUP'

            cd '$MINE_PKG_DIR'

            sleep 12

            ros2 run ros_gz_bridge parameter_bridge \
            /tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V

            exec bash
        "
}


# ============================================================
# TERMINAL 8
# STATIC LiDAR TF
# ============================================================

start_lidar_tf()
{
    banner "STARTING STATIC LiDAR TF"

    gnome-terminal \
        --title="ELIOS-SAR | 8 LiDAR TF" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — STATIC LiDAR TF'
            echo '============================================================'

            source '$ROS_SETUP'

            sleep 15

            ros2 run tf2_ros static_transform_publisher \
            0 0 0.30 0 0 0 \
            base_link ellios_rover/base_link/lidar_2d

            exec bash
        "
}


# ============================================================
# TERMINAL 9
# SLAM TOOLBOX
# ============================================================

start_slam()
{
    banner "STARTING SLAM TOOLBOX"

    gnome-terminal \
        --title="ELIOS-SAR | 9 SLAM Toolbox" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — SLAM TOOLBOX'
            echo '============================================================'

            source '$ROS_SETUP'

            cd '$MINE_WS'

            sleep 18

            ros2 launch slam_toolbox online_async_launch.py \
            slam_params_file:='$MINE_PKG_DIR/config/mapper_params_online_async.yaml'

            exec bash
        "
}


# ============================================================
# TERMINAL 10
# ROSBRIDGE :9090
# ============================================================

start_rosbridge()
{
    banner "STARTING ROSBRIDGE :9090"

    gnome-terminal \
        --title="ELIOS-SAR | 10 rosbridge :9090" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — ROSBRIDGE'
            echo ' WebSocket :9090'
            echo '============================================================'

            source '$ROS_SETUP'
            source '$GCS_ROS_WS/install/setup.bash'

            export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET

            sleep 15

            ros2 launch rosbridge_server rosbridge_websocket_launch.xml

            exec bash
        "
}


# ============================================================
# TERMINAL 11
# PX4 ROS2 COMMAND BRIDGE
# ============================================================

start_px4_bridge()
{
    banner "STARTING ELIOS PX4 COMMAND BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 11 PX4 Bridge" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — PX4 COMMAND BRIDGE'
            echo '============================================================'

            source '$ROS_SETUP'
            source '$GCS_ROS_WS/install/setup.bash'

            export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET

            sleep 20

            ros2 run ellios_sar_px4_bridge px4_bridge

            exec bash
        "
}


# ============================================================
# TERMINAL 12
# OFFBOARD SETPOINT CONTROLLER
# ============================================================

start_offboard()
{
    banner "STARTING OFFBOARD CONTROLLER"

    gnome-terminal \
        --title="ELIOS-SAR | 12 Offboard" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — OFFBOARD CONTROLLER'
            echo '============================================================'

            source '$ROS_SETUP'
            source '$GCS_ROS_WS/install/setup.bash'

            export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET

            sleep 25

            ros2 run ellios_sar_px4_offboard offboard_controller

            exec bash
        "
}


# ============================================================
# TERMINAL 13
# GCS BACKEND :8000
# ============================================================

start_backend()
{
    banner "STARTING GCS BACKEND :8000"

    gnome-terminal \
        --title="ELIOS-SAR | 13 Backend :8000" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — MERN BACKEND'
            echo ' PORT 8000'
            echo '============================================================'

            cd '$BACKEND_DIR'

            sleep 8

            node src/server.js

            exec bash
        "
}


# ============================================================
# TERMINAL 14
# GCS FRONTEND :5173
# ============================================================

start_frontend()
{
    banner "STARTING GCS FRONTEND :5173"

    gnome-terminal \
        --title="ELIOS-SAR | 14 Frontend :5173" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — REACT/VITE GCS'
            echo ' PORT 5173'
            echo '============================================================'

            cd '$FRONTEND_DIR'

            sleep 5

            npm run dev

            exec bash
        "
}


# ============================================================
# TERMINAL 15
# DEMO NODE — LAST
# ============================================================

start_demo()
{
    banner "STARTING ELIOS-SAR DEMO NODE — LAST"

    gnome-terminal \
        --title="ELIOS-SAR | 15 Demo Node" \
        -- bash -lc "

            echo '============================================================'
            echo ' ELIOS-SAR — DEMO NODE'
            echo ' STARTED LAST'
            echo '============================================================'

            source '$ROS_SETUP'
            source '$GCS_ROS_WS/install/setup.bash'

            export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET

            sleep 30

            ros2 run ellios_sar_demo demo_node

            exec bash
        "
}


# ============================================================
# MAIN
# ============================================================

clear

banner "ELIOS-SAR FULL SYSTEM STARTUP"

echo "============================================================"
echo " CANONICAL PROJECT"
echo "============================================================"
echo ""
echo "$PROJECT_ROOT"
echo ""

echo "============================================================"
echo " STARTUP ORDER"
echo "============================================================"
echo ""
echo " 1. PX4 SITL + Gazebo x500"
echo " 2. MicroXRCE-DDS :8888"
echo " 3. Mine Simulator + Gazebo"
echo " 4. Rover LiDAR bridge"
echo " 5. Rover odometry bridge"
echo " 6. Rover cmd_vel bridge"
echo " 7. TF bridge"
echo " 8. Static LiDAR TF"
echo " 9. SLAM Toolbox"
echo "10. rosbridge :9090"
echo "11. PX4 ROS2 bridge"
echo "12. Offboard controller"
echo "13. GCS backend :8000"
echo "14. GCS frontend :5173"
echo "15. Demo node LAST"
echo ""

echo "============================================================"
echo " SAFETY"
echo "============================================================"
echo ""
echo " NO ARM"
echo " NO TAKEOFF"
echo " NO OFFBOARD COMMAND"
echo " NO LAND"
echo " NO RTL"
echo " NO DOCK"
echo " NO UNDOCK"
echo ""


# ============================================================
# CHECKS
# ============================================================

check_filesystem

cleanup

# Automatically configure PX4 SITL parameters for ROS 2 DDS offboard flight
if [ -f "$PROJECT_ROOT/scripts/setup_px4_params.sh" ]; then
    bash "$PROJECT_ROOT/scripts/setup_px4_params.sh" || true
fi


# ============================================================
# START SYSTEM
# ============================================================

start_px4
sleep 8

start_microxrce
sleep 3

start_mine
sleep 8

start_rover_scan_bridge
sleep 2

start_rover_odom_bridge
sleep 2

start_rover_cmd_bridge
sleep 2

start_tf_bridge
sleep 2

start_lidar_tf
sleep 2

start_slam
sleep 3

start_rosbridge
sleep 3

start_px4_bridge
sleep 3

start_offboard
sleep 3

start_backend
sleep 5

start_frontend
sleep 5

start_demo


# ============================================================
# FINAL MESSAGE
# ============================================================

sleep 5

clear

banner "ELIOS-SAR FULL SYSTEM STARTUP COMPLETE"

echo "============================================================"
echo " DRONE"
echo "============================================================"
echo ""
echo " PX4 SITL + Gazebo       : STARTED"
echo " MicroXRCE-DDS           : UDP 8888"
echo " PX4 ROS2 Bridge         : STARTED"
echo " Offboard Controller     : STARTED"
echo ""

echo "============================================================"
echo " ROVER / MINE"
echo "============================================================"
echo ""
echo " Mine Simulator          : STARTED"
echo " /rover/scan             : BRIDGED"
echo " /rover/odom             : BRIDGED"
echo " /rover/cmd_vel          : BRIDGED"
echo " /tf                     : BRIDGED"
echo " Static LiDAR TF         : STARTED"
echo " SLAM Toolbox            : STARTED"
echo " /map                    : GENERATED"
echo ""

echo "============================================================"
echo " GCS"
echo "============================================================"
echo ""
echo " rosbridge               : :9090"
echo " Backend                 : :8000"
echo " Frontend                : :5173"
echo " Demo Node               : LAST"
echo ""

echo "============================================================"
echo " MINE GAZEBO"
echo "============================================================"
echo ""
echo " World                   : ellios_mine.sdf"
echo " Resource path           : models + mine package"
echo " Gazebo                  : running"
echo ""

echo "============================================================"
echo " GCS URL"
echo "============================================================"
echo ""
echo " http://localhost:5173"
echo ""

echo "============================================================"
echo " SAFETY"
echo "============================================================"
echo ""
echo " NO ARM"
echo " NO TAKEOFF"
echo " NO OFFBOARD COMMAND"
echo " NO LAND"
echo " NO RTL"
echo " NO DOCK"
echo " NO UNDOCK"
echo ""

echo "The system only starts the simulation ecosystem."
echo ""

echo "============================================================"
echo " ELIOS-SAR READY"
echo "============================================================"
echo ""

if [ -t 0 ]; then
    exec bash
fi
