/**
 * Single source of truth for ELIOS-SAR vehicle fleet (drones and rovers).
 * Any default, dummy, or operational vehicle configuration originates here.
 */
export const DEFAULT_FLEET = [
  {
    vehicleId: "DRONE-01",
    vehicleType: "drone",
    name: "Elios Aerial Scout",
    capabilities: [
      "rgb_camera",
      "thermal_camera",
      "px4_offboard",
      "optical_flow",
    ],
    metadata: {
      model: "x500_quadcopter",
      sensors: ["rgb", "thermal", "lidar_1d", "imu", "barometer"],
      flightLimits: {
        maxAltitude: 15.0,
        maxSpeed: 5.0,
      },
    },
  },
  {
    vehicleId: "ROVER-01",
    vehicleType: "rover",
    name: "Elios Ground Explorer",
    capabilities: [
      "2d_lidar",
      "gas_detection",
      "environment_sensing",
      "crawler",
    ],
    metadata: {
      model: "differential_crawler",
      sensors: ["lidar_2d", "gas_mq4", "gas_co", "temperature", "humidity"],
      driveLimits: {
        maxSpeed: 1.5,
      },
    },
  },
];

export function getVehicleConfig(vehicleId) {
  return DEFAULT_FLEET.find((v) => v.vehicleId === vehicleId) || null;
}

export function getVehiclesByType(vehicleType) {
  return DEFAULT_FLEET.filter((v) => v.vehicleType === vehicleType);
}
