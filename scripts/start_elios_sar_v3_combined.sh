#!/bin/bash

set -u

# ============================================================
# ELIOS-SAR
# COMBINED ROVER + V3 DRONE + GCS STARTUP
#
# SAFE VERSION
#
# - One Gazebo mine world
# - Existing rover architecture preserved
# - V3 drone replaces X500
# - No automatic Offboard
# - No fake demo node
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PX4_DIR="${PX4_DIR:-$HOME/PX4-Autopilot}"
MINE_WS="${MINE_WS:-$HOME/Elios_SAR_sim_ws}"
MINE_PKG_DIR="$MINE_WS/src/ellios_sar_mine"

GCS_ROS_WS="$PROJECT_ROOT/ros2_ws"

BACKEND_DIR="$PROJECT_ROOT/gcs/backend"
FRONTEND_DIR="$PROJECT_ROOT/gcs/frontend"

ROS_SETUP="/opt/ros/jazzy/setup.bash"

MINE_WORLD="$MINE_PKG_DIR/worlds/ellios_mine.sdf"
MINE_MODELS="$MINE_PKG_DIR/models"

V3_MODEL_DIR="$PROJECT_ROOT/simulation/drone/models/elios_protected_drone_v3"
V3_INSTALLED_DIR="$PX4_DIR/Tools/simulation/gz/models/elios_protected_drone_v3"

export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

banner()
{
    echo ""
    echo "============================================================"
    echo "$1"
    echo "============================================================"
    echo ""
}

check_path()
{
    if [ ! -e "$1" ]; then
        echo "ERROR: Missing:"
        echo "$1"
        exit 1
    fi
}

# ------------------------------------------------------------
# Filesystem checks
# ------------------------------------------------------------

check_filesystem()
{
    banner "CHECKING ELIOS-SAR FILESYSTEM"

    check_path "$PROJECT_ROOT"
    check_path "$PX4_DIR"
    check_path "$MINE_WS"
    check_path "$MINE_PKG_DIR"
    check_path "$MINE_WORLD"
    check_path "$MINE_MODELS"
    check_path "$GCS_ROS_WS/install/setup.bash"
    check_path "$BACKEND_DIR"
    check_path "$FRONTEND_DIR"
    check_path "$V3_MODEL_DIR/model.sdf"
    check_path "$V3_INSTALLED_DIR/model.sdf"

    echo "Filesystem check PASSED."
}

# ------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------

cleanup()
{
    banner "CLEANING OLD ELIOS-SAR RUNTIME"

    pkill -f "$PX4_DIR/build/px4_sitl_default/bin/px4" 2>/dev/null || true
    pkill -f "MicroXRCEAgent" 2>/dev/null || true
    pkill -f "gz sim" 2>/dev/null || true
    pkill -f "ros_gz_bridge" 2>/dev/null || true
    pkill -f "async_slam_toolbox_node" 2>/dev/null || true
    pkill -f "rosbridge_websocket" 2>/dev/null || true
    pkill -f "ellios_sar_px4_bridge" 2>/dev/null || true
    pkill -f "node src/server.js" 2>/dev/null || true
    pkill -f "node.*vite" 2>/dev/null || true

    sleep 5

    echo "Cleanup complete."
}

# ------------------------------------------------------------
# TERMINAL 1
# Mine Gazebo
# ------------------------------------------------------------

start_mine()
{
    banner "STARTING MINE GAZEBO"

    gnome-terminal \
        --title="ELIOS-SAR | 1 Mine Gazebo" \
        -- bash -lc "
            source '$ROS_SETUP'

            export GZ_SIM_RESOURCE_PATH='$PX4_DIR/Tools/simulation/gz/models:$MINE_MODELS:$MINE_PKG_DIR:$V3_MODEL_DIR'

            cd '$MINE_PKG_DIR'

            echo 'Starting ELIOS-SAR mine...'
            gz sim -r -v 3 '$MINE_WORLD'

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 2
# V3 SPAWN
# ------------------------------------------------------------

spawn_v3()
{
    banner "SPAWNING V3 DRONE"

    gnome-terminal \
        --title="ELIOS-SAR | 2 Spawn V3" \
        -- bash -lc "
            source '$ROS_SETUP'

            export GZ_SIM_RESOURCE_PATH='$PX4_DIR/Tools/simulation/gz/models:$MINE_MODELS:$MINE_PKG_DIR:$V3_MODEL_DIR'

            sleep 8

            echo 'Spawning protected V3 drone...'

            gz service -s /world/default/create \
                --reqtype gz.msgs.EntityFactory \
                --reptype gz.msgs.Boolean \
                --timeout 5000 \
                --req 'sdf_filename: \"${V3_INSTALLED_DIR}/model.sdf\", name: \"elios_protected_drone_v3\", pose: {position: {x: 0, y: 0, z: 1.5}}'

            echo ''
            echo 'V3 spawn command completed.'
            echo ''

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 3
# PX4 ATTACH TO V3
# ------------------------------------------------------------

start_px4()
{
    banner "STARTING PX4 FOR V3"

    gnome-terminal \
        --title="ELIOS-SAR | 3 PX4 V3" \
        -- bash -lc "
            source '$ROS_SETUP'

            export PX4_GZ_STANDALONE=1
            export PX4_GZ_WORLD=default
            export PX4_SIM_MODEL=gz_elios_v3
            export PX4_GZ_MODEL_NAME=elios_protected_drone_v3

            export GZ_SIM_RESOURCE_PATH='$PX4_DIR/Tools/simulation/gz/models:$MINE_MODELS:$MINE_PKG_DIR:$V3_MODEL_DIR'

            sleep 12

            cd '$PX4_DIR'

            echo 'Attaching PX4 to V3...'

            ./build/px4_sitl_default/bin/px4

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 4
# MicroXRCE
# ------------------------------------------------------------

start_microxrce()
{
    banner "STARTING MICRO XRCE-DDS"

    gnome-terminal \
        --title="ELIOS-SAR | 4 MicroXRCE :8888" \
        -- bash -lc "
            source '$ROS_SETUP'

            sleep 15

            MicroXRCEAgent udp4 -p 8888

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 5
# Rover LiDAR
# ------------------------------------------------------------

start_rover_scan()
{
    banner "STARTING ROVER LiDAR BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 5 Rover LiDAR" \
        -- bash -lc "
            source '$ROS_SETUP'

            sleep 12

            ros2 run ros_gz_bridge parameter_bridge \
            '/rover/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 6
# Rover Odom
# ------------------------------------------------------------

start_rover_odom()
{
    banner "STARTING ROVER ODOM BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 6 Rover Odom" \
        -- bash -lc "
            source '$ROS_SETUP'

            sleep 12

            ros2 run ros_gz_bridge parameter_bridge \
            '/rover/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry'

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 7
# Rover CMD
# ------------------------------------------------------------

start_rover_cmd()
{
    banner "STARTING ROVER CONTROL BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 7 Rover CMD" \
        -- bash -lc "
            source '$ROS_SETUP'

            sleep 12

            ros2 run ros_gz_bridge parameter_bridge \
            '/rover/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist'

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 8
# TF
# ------------------------------------------------------------

start_tf()
{
    banner "STARTING ROVER TF BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 8 TF" \
        -- bash -lc "
            source '$ROS_SETUP'

            sleep 12

            ros2 run ros_gz_bridge parameter_bridge \
            '/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V'

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 9
# Rover static LiDAR TF
# ------------------------------------------------------------

start_rover_lidar_tf()
{
    banner "STARTING ROVER STATIC LiDAR TF"

    gnome-terminal \
        --title="ELIOS-SAR | 9 Rover LiDAR TF" \
        -- bash -lc "
            source '$ROS_SETUP'

            sleep 15

            ros2 run tf2_ros static_transform_publisher \
            0 0 0.30 0 0 0 \
            base_link ellios_rover/base_link/lidar_2d

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 10
# SLAM
# ------------------------------------------------------------

start_slam()
{
    banner "STARTING SLAM TOOLBOX"

    gnome-terminal \
        --title="ELIOS-SAR | 10 SLAM" \
        -- bash -lc "
            source '$ROS_SETUP'

            sleep 18

            cd '$MINE_WS'

            ros2 launch slam_toolbox online_async_launch.py \
            slam_params_file:='$MINE_PKG_DIR/config/mapper_params_online_async.yaml'

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 11
# V3 LiDAR
# ------------------------------------------------------------

start_v3_lidar()
{
    banner "STARTING V3 3D LiDAR BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 11 V3 LiDAR" \
        -- bash -lc "
            source '$ROS_SETUP'

            sleep 18

            ros2 run ros_gz_bridge parameter_bridge \
            '/drone/lidar/points/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked'

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 12
# rosbridge
# ------------------------------------------------------------

start_rosbridge()
{
    banner "STARTING ROSBRIDGE :9090"

    gnome-terminal \
        --title="ELIOS-SAR | 12 rosbridge" \
        -- bash -lc "
            source '$ROS_SETUP'
            source '$GCS_ROS_WS/install/setup.bash'

            sleep 20

            ros2 launch rosbridge_server rosbridge_websocket_launch.xml

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 13
# PX4 command bridge
# ------------------------------------------------------------

start_px4_bridge()
{
    banner "STARTING PX4 COMMAND BRIDGE"

    gnome-terminal \
        --title="ELIOS-SAR | 13 PX4 Bridge" \
        -- bash -lc "
            source '$ROS_SETUP'
            source '$GCS_ROS_WS/install/setup.bash'

            sleep 22

            ros2 run ellios_sar_px4_bridge px4_bridge

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 14
# Backend
# ------------------------------------------------------------

start_backend()
{
    banner "STARTING GCS BACKEND"

    gnome-terminal \
        --title="ELIOS-SAR | 14 Backend :8000" \
        -- bash -lc "
            cd '$BACKEND_DIR'

            sleep 8

            node src/server.js

            exec bash
        "
}

# ------------------------------------------------------------
# TERMINAL 15
# Frontend
# ------------------------------------------------------------

start_frontend()
{
    banner "STARTING GCS FRONTEND"

    gnome-terminal \
        --title="ELIOS-SAR | 15 Frontend :5173" \
        -- bash -lc "
            cd '$FRONTEND_DIR'

            sleep 10

            npm run dev

            exec bash
        "
}

# ============================================================
# MAIN
# ============================================================

clear

banner "ELIOS-SAR V3 COMBINED SYSTEM"

echo "This launcher uses:"
echo ""
echo "  ONE mine Gazebo"
echo "  Rover"
echo "  Protected Drone V3"
echo "  PX4"
echo "  MicroXRCE-DDS"
echo "  Rover LiDAR / Odom / CMD"
echo "  Rover SLAM"
echo "  V3 3D LiDAR"
echo "  rosbridge"
echo "  PX4 command bridge"
echo "  GCS backend"
echo "  GCS frontend"
echo ""
echo "NOT STARTED:"
echo "  X500"
echo "  automatic Offboard"
echo "  fake demo node"
echo ""

check_filesystem
cleanup

start_mine
sleep 5

spawn_v3
sleep 3

start_px4
sleep 3

start_microxrce
sleep 3

start_rover_scan
sleep 2

start_rover_odom
sleep 2

start_rover_cmd
sleep 2

start_tf
sleep 2

start_rover_lidar_tf
sleep 2

start_slam
sleep 2

start_v3_lidar
sleep 2

start_rosbridge
sleep 2

start_px4_bridge
sleep 2

start_backend
sleep 3

start_frontend

sleep 5

banner "ELIOS-SAR V3 COMBINED STARTUP LAUNCHED"

echo "GCS: http://localhost:5173"
echo ""
echo "IMPORTANT:"
echo "The drone static TF is intentionally NOT started yet."
echo "We will solve rover/drone TF separation after the basic"
echo "combined system is verified."
echo ""
echo "No ARM / TAKEOFF / LAND / RTL / automatic Offboard command"
echo "is issued by this launcher."

exec bash
