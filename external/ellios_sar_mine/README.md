# ELLIOS Search & Rescue: Underground Mine Simulation 🧗‍♂️🚧

A complete ROS 2 simulation package for autonomous underground coal mine exploration using Gazebo Harmonic and SLAM Toolbox.

## 📋 Overview
This project simulates the **ELLIOS Mine-SAR Unmanned Ground Vehicle (UGV)** operating within a custom subterranean environment. It is designed to test search and rescue algorithms, differential drive kinematics, and real-time mapping in GPS-denied locations.

## ✨ Key Features
* **Underground Coal Mine World:** A custom 3D tunnel environment (`ellios_mine.sdf`) complete with rock obstacles, wooden support beams, and dim subterranean lighting.
* **ELLIOS Rover Model:** A custom 4-wheel skid-steer UGV equipped with high-friction tires.
* **Sensors & Kinematics:** Integrated 360-degree GPU LiDAR (10 Hz) and a Gazebo `DiffDrive` plugin for `/cmd_vel` control and `/odom` telemetry.
* **Real-Time SLAM:** Asynchronous 2D occupancy grid mapping utilizing the ROS 2 `slam_toolbox`.

## ⚙️ System Requirements
* **OS:** Ubuntu 24.04 LTS
* **ROS 2:** Jazzy Jalisco
* **Simulator:** Gazebo Harmonic

## 🚀 Build Instructions
Navigate to your ROS 2 workspace and build the package:
```bash
cd ~/Elios_SAR_sim_ws
colcon build --packages-select ellios_sar_mine
source install/setup.bash
# Export the model path and run the simulation
GZ_SIM_RESOURCE_PATH=$(pwd)/src/ellios_sar_mine/models gz sim -r src/ellios_sar_mine/worlds/ellios_mine.sdf
