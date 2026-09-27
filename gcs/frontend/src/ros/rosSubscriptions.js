import { rosbridgeClient } from "./rosbridgeClient";
import {
  normalizeBatteryStatus,
  normalizeVehicleStatus,
  normalizeGlobalPosition,
  normalizeLocalPosition,
  normalizeAttitude,
} from "./px4Normalizer";

export const PX4_SUBSCRIPTIONS = [
  {
    topic: "/fmu/out/battery_status_v1",
    type: "px4_msgs/msg/BatteryStatus",
    normalizer: normalizeBatteryStatus,
    handler: "battery",
  },
  {
    topic: "/fmu/out/vehicle_status_v4",
    type: "px4_msgs/msg/VehicleStatus",
    normalizer: normalizeVehicleStatus,
    handler: "status",
  },
  {
    topic: "/fmu/out/vehicle_global_position",
    type: "px4_msgs/msg/VehicleGlobalPosition",
    normalizer: normalizeGlobalPosition,
    handler: "globalPosition",
  },
  {
    topic: "/fmu/out/vehicle_local_position_v1",
    type: "px4_msgs/msg/VehicleLocalPosition",
    normalizer: normalizeLocalPosition,
    handler: "localPosition",
  },
  {
    topic: "/fmu/out/vehicle_attitude",
    type: "px4_msgs/msg/VehicleAttitude",
    normalizer: normalizeAttitude,
    handler: "attitude",
  },
];

export function normalizeOccupancyGrid(msg) {
  if (!msg || !msg.info) return null;
  return {
    width: msg.info.width,
    height: msg.info.height,
    resolution: msg.info.resolution,
    origin: {
      x: msg.info.origin?.position?.x ?? 0,
      y: msg.info.origin?.position?.y ?? 0,
    },
    cells: msg.data ?? [],
    grid: msg.data ?? [],
  };
}

export function startRosSubscriptions(onRosData) {
  rosbridgeClient.connect();

  const waitForConnection = () => {
    if (!rosbridgeClient.connected) {
      setTimeout(waitForConnection, 250);
      return;
    }

    // Standard vehicle & telemetry topics
    rosbridgeClient.subscribe("/drone/pose", "geometry_msgs/PoseStamped");
    rosbridgeClient.on("/drone/pose", (msg) => {
      if (typeof onRosData === "function") {
        onRosData("drone_pose", msg);
      }
    });

    rosbridgeClient.subscribe("/rover/odom", "nav_msgs/Odometry");
    rosbridgeClient.on("/rover/odom", (msg) => {
      if (typeof onRosData === "function") {
        onRosData("rover_pose", msg);
      }
    });

    rosbridgeClient.subscribe("/drone/telemetry", "std_msgs/String");
    rosbridgeClient.on("/drone/telemetry", (msg) => {
      if (typeof onRosData === "function") {
        onRosData("drone_telemetry", msg);
      }
    });

    rosbridgeClient.subscribe("/rover/telemetry", "std_msgs/String");
    rosbridgeClient.on("/rover/telemetry", (msg) => {
      if (typeof onRosData === "function") {
        onRosData("rover_telemetry", msg);
      }
    });

    rosbridgeClient.subscribe("/rover/environment", "std_msgs/String");
    rosbridgeClient.on("/rover/environment", (msg) => {
      if (typeof onRosData === "function") {
        onRosData("rover_environment", msg);
      }
    });

    rosbridgeClient.subscribe("/system/events", "std_msgs/String");
    rosbridgeClient.on("/system/events", (msg) => {
      if (typeof onRosData === "function") {
        onRosData("system_events", msg);
      }
    });

    // Map subscription
    rosbridgeClient.subscribe("/map", "nav_msgs/OccupancyGrid");
    rosbridgeClient.on("/map", (msg) => {
      const normalizedMap = normalizeOccupancyGrid(msg);
      if (typeof onRosData === "function" && normalizedMap) {
        onRosData("map", normalizedMap, msg);
      }
    });

    // PX4 telemetry topics
    PX4_SUBSCRIPTIONS.forEach(({ topic, type, normalizer, handler }) => {
      rosbridgeClient.subscribe(topic, type);

      rosbridgeClient.on(topic, (msg) => {
        const normalized = normalizer(msg);
        if (typeof onRosData === "function") {
          onRosData(handler, normalized, msg);
        }
      });
    });
  };

  waitForConnection();
}
