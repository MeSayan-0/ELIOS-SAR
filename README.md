# ELIOS-SAR

<p align="center">
  <img src="docs/media/simulation-preview.png" alt="ELIOS-SAR Simulation" width="900">
</p>

<h1 align="center">ELIOS-SAR</h1>

<p align="center">
  <strong>Emergency Localization & Intelligent Operations System for Search & Rescue</strong>
</p>

<p align="center">
  Simulation-first multi-robot search-and-rescue platform integrating a ground rover,
  Protected Drone V3, LiDAR, SLAM, ROS 2, PX4, Gazebo and a unified Ground Control Station.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ROS%202-Robotics-blue" alt="ROS 2">
  <img src="https://img.shields.io/badge/Gazebo-Simulation-orange" alt="Gazebo">
  <img src="https://img.shields.io/badge/PX4-Autopilot-black" alt="PX4">
  <img src="https://img.shields.io/badge/LiDAR-Mapping-informational" alt="LiDAR">
  <img src="https://img.shields.io/badge/SLAM-Mapping-success" alt="SLAM">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT">
</p>

---

## Contents

- [Overview](#overview)
- [Demo](#demo)
- [Ground Control Station](#ground-control-station)
- [Key Capabilities](#key-capabilities)
- [Architecture](#architecture)
- [Simulation-to-Hardware Strategy](#simulation-to-hardware-strategy)
- [Technology Stack](#technology-stack)
- [System Components](#system-components)
- [ROS 2 Interfaces](#ros-2-interfaces)
- [Getting Started](#getting-started)
- [Running the Integrated Simulation](#running-the-integrated-simulation)
- [Repository Structure](#repository-structure)
- [Verification and Testing](#verification-and-testing)
- [Development Workflow](#development-workflow)
- [Roadmap](#roadmap)
- [Safety and Operational Boundaries](#safety-and-operational-boundaries)
- [Media](#media)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

ELIOS-SAR is an integrated robotics platform for search-and-rescue scenarios where mapping, situational awareness, remote operation and coordinated robotic sensing are required.

The current integrated simulation combines:

- Custom underground mine environment
- Custom ELIOS-SAR rover
- Protected Drone V3
- PX4 flight-control integration
- Rover 2D LiDAR and odometry
- Rover SLAM
- Drone 3D LiDAR
- ROS 2 communication
- Micro XRCE-DDS
- rosbridge / WebSocket connectivity
- Web-based Ground Control Station
- Mission, telemetry, alert and event interfaces

The system follows a simulation-first architecture: simulated sensors and vehicles communicate through ROS 2 interfaces so that physical hardware can progressively replace simulation components without requiring a redesign of the higher-level GCS, mapping and mission layers.

---

## Demo

<p align="center">
  <a href="docs/media/elios-sar-simulation.mp4">
    <img src="docs/media/simulation-preview.png" alt="ELIOS-SAR Simulation Demo" width="900">
  </a>
</p>

<p align="center"><strong>▶ Click the preview to open the simulation video</strong></p>

The demonstration covers the mine environment, rover, protected drone, LiDAR visualization, ROS 2 integration, PX4 integration and the operator-facing system.

> For very large videos, use a hosted video or release asset and keep the repository preview image.

---

## Ground Control Station

<p align="center">
  <img src="docs/media/gcs-overview.png" alt="ELIOS-SAR Ground Control Station" width="1100">
</p>

The Ground Control Station is the operator-facing layer of ELIOS-SAR. It consolidates robot state, mapping, telemetry, alerts, mission information and operational events.

| GCS Area | Purpose |
|---|---|
| Global Mine Map | Environment and robot visualization |
| Vehicle Status | Rover and drone connectivity |
| Telemetry | Vehicle state and available telemetry |
| Priority Alerts | Active system or mission alerts |
| Mission Summary | Mission-level information |
| Event Log | Operational events and commands |
| System Status | ROS 2 / PX4 / vehicle connectivity |

The GCS is deliberately separated from individual sensor implementations so that simulated and physical systems can expose the same higher-level interfaces.

---

# Key Capabilities

### Multi-Robot Operations
Ground and aerial platforms operate within one mission architecture.

### LiDAR Mapping and SLAM
Rover LiDAR feeds the ROS 2 mapping pipeline and supports SLAM-based environment reconstruction.

### Aerial Reconnaissance
The aerial subsystem provides position, telemetry and 3D environmental sensing.

### Unified Operator Interface
The GCS presents robot state, mapping, telemetry, alerts, mission information and events in one workspace.

### Simulation-to-Hardware Path
The architecture is designed so that simulation adapters can progressively be replaced by hardware drivers while preserving higher-level software contracts.

### Modular ROS 2 Architecture
Robotics, mapping, mission, perception, communication and visualization remain separable subsystems.

---

# Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                    GROUND CONTROL STATION                       │
│                                                                  │
│  Global Map │ Telemetry │ Vehicles │ Missions │ Alerts │ Events │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                         WebSocket / rosbridge
                                │
════════════════════════════════╪═══════════════════════════════════
                         ROS 2 INTERFACE
════════════════════════════════╪═══════════════════════════════════
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
          ┌──────────┐    ┌──────────┐    ┌────────────┐
          │  ROVER   │    │  DRONE   │    │  MISSION   │
          │  STACK   │    │  STACK   │    │ / EVENTS   │
          └────┬─────┘    └────┬─────┘    └─────┬──────┘
               │               │                │
        ┌──────┼──────┐   ┌────┼──────┐         │
        │      │      │   │    │      │         │
      LiDAR  Odom    IMU  PX4  3D    State    Mission
        │      │      │       LiDAR           Events
        └──────┼──────┘         │               │
               │                │               │
               ▼                ▼               │
             SLAM          Aerial Data          │
               │                │               │
               └──────────┬─────┴───────────────┘
                          ▼
                    Common ROS 2
                       contracts
                          │
═══════════════════════════╪═══════════════════════════════════════
                  SIMULATION / HARDWARE
═══════════════════════════╪═══════════════════════════════════════
                          │
                ┌─────────┴─────────┐
                │                   │
           SIMULATION             HARDWARE
                │                   │
             Gazebo             Real Sensors
             PX4 SITL           Real Rover
             Sim LiDAR           Real LiDAR
             Sim IMU             Real IMU
             Sim Camera          Real Camera
```

---

# Simulation-to-Hardware Strategy

ELIOS-SAR treats simulation as a validation environment rather than a separate software product.

### Simulation

```text
Gazebo Sensor
     ↓
ROS 2 Adapter
     ↓
Standard ROS 2 Interface
     ↓
SLAM / Mission / GCS
```

### Hardware

```text
Physical Sensor
     ↓
Hardware Driver / ROS 2 Adapter
     ↓
Same ROS 2 Interface
     ↓
Same SLAM / Mission / GCS
```

| Simulation | Hardware Target |
|---|---|
| Gazebo LiDAR | Real LiDAR |
| Simulated IMU | Real IMU |
| Simulated odometry | Encoders / odometry |
| Drone simulator | Flight controller |
| Simulated camera | Physical camera |
| Simulated environmental data | Physical sensors |

The higher layers remain centered on ROS 2, mapping, mission logic, events, visualization and the GCS.

---

# Technology Stack

| Layer | Technology |
|---|---|
| Robotics Middleware | ROS 2 |
| Simulation | Gazebo |
| Flight Control | PX4 Autopilot |
| Drone Transport | Micro XRCE-DDS |
| Web / ROS Bridge | rosbridge / WebSocket |
| Mapping | LiDAR + ROS 2 SLAM pipeline |
| 2D Sensing | LaserScan / 2D LiDAR |
| 3D Sensing | PointCloud2 / 3D LiDAR |
| Ground Platform | Custom ELIOS-SAR Rover |
| Aerial Platform | Protected Drone V3 |
| Ground Control | Web-based GCS |
| Languages | Python, JavaScript, C/C++ components |
| Build | colcon, CMake, npm |
| Testing | pytest / ROS 2 package tests |
| Version Control | Git / GitHub |

> Version numbers are intentionally not hard-coded here unless they are guaranteed by the repository's current manifests and launch environment.

---

# System Components

## Rover

The custom mine/rover package is maintained under:

```text
external/ellios_sar_mine/
```

Key files:

```text
external/ellios_sar_mine/
├── config/
│   └── mapper_params_online_async.yaml
├── models/
│   └── ellios_rover/
│       ├── model.config
│       └── rover.sdf
├── worlds/
│   ├── ellios_mine.sdf
│   ├── ellios_mine.before-px4.sdf
│   └── ellios_mine.before-px4-sensors.sdf
├── CMakeLists.txt
├── package.xml
└── README.md
```

### Rover data path

```text
Mine World
    ↓
ELIOS Rover
    ↓
2D LiDAR / Odom / IMU
    ↓
ROS 2
    ↓
SLAM
    ↓
Map + TF
    ↓
GCS
```

## Protected Drone V3

The current integrated aerial model is:

```text
simulation/drone/models/elios_protected_drone_v3/
```

The runtime path connects:

```text
Gazebo → Protected Drone V3 → PX4 → Micro XRCE-DDS → ROS 2 → GCS
```

The current integrated startup intentionally uses the V3 platform rather than the legacy X500 startup path.

## Ground Control Station

```text
gcs/
├── backend/
└── frontend/
```

The frontend and backend are kept separate from the robotics workspace.

---

# ROS 2 Interfaces

## Rover

```text
/rover/scan
/rover/pointcloud
/rover/odom
/rover/pose
/rover/imu
/rover/telemetry
/rover/environment
```

## Drone

```text
/drone/pose
/drone/pointcloud
/drone/odom
/drone/telemetry
/drone/rgb
/drone/thermal
/drone/environment
/drone/detections
```

## Mapping

```text
/map
/map_metadata
/tf
/tf_static
```

## Missions

```text
/missions/create
/missions/status
/missions/anchors
/missions/events
```

## System

```text
/system/status
/system/alerts
/system/logs
```

> These interfaces describe the project's common architecture. Not every interface is necessarily active in every runtime configuration; use the current launch configuration and ROS 2 graph as the runtime source of truth.

---

# Getting Started

## Prerequisites

Typical development requirements:

- Ubuntu Linux
- ROS 2
- Gazebo
- PX4 Autopilot
- Micro XRCE-DDS Agent
- Python
- Node.js / npm
- Git
- colcon
- rosdep

## Clone

```bash
git clone https://github.com/MeSayan-0/ELIOS-SAR-Main-GAZEBO-SIM-ROS2.git
cd ELIOS-SAR-Main-GAZEBO-SIM-ROS2
```

## Build ROS 2

```bash
cd ros2_ws

colcon build

source install/setup.bash

cd ..
```

Do not proceed to fusion until both checks and image tests succeed.


<marquee behavior="scroll" direction="left" scrollamount="6">
  <b>✨ THANK YOU FOR VISITING! ✨ SHARE YOUR FEEDBACK! ✨ DROP A STAR IF YOU LIKE IT! ✨ HAPPY CODING! ✨</b>
</marquee>
