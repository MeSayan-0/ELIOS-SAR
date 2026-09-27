import { Ros, Topic } from "roslib";
import mongoose from "mongoose";

import {
  updateCommandStatus,
  getRecentCommands,
} from "./commandService.js";

import {
  getVehicleByType,
  getVehicle,
  updateTelemetry,
  markStaleVehicles,
  getStateSnapshot as getInMemorySnapshot,
} from "./gcsState.js";

import { Vehicle } from "../models/Vehicle.js";
import { broadcast } from "../websocket/manager.js";

const ROSBRIDGE_URL =
  process.env.ROSBRIDGE_URL ||
  "ws://127.0.0.1:9090";

let ros = null;
let broadcastTimer = null;
let stalenessTimer = null;
let reconnectTimer = null;
let lastDbSyncTimes = new Map();

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    startRosStatusGateway();
  }, 2000);
}

function queueStateBroadcast() {
  if (broadcastTimer) return;
  broadcastTimer = setTimeout(() => {
    broadcastTimer = null;
    broadcast({
      type: "state",
      state: getInMemorySnapshot(),
    });
  }, 50); // 20Hz throttled flush
}

function asyncSyncToMongo(vehicleId, telemetry) {
  if (mongoose.connection.readyState !== 1) return;

  const now = Date.now();
  const lastSync = lastDbSyncTimes.get(vehicleId) || 0;
  if (now - lastSync < 3000) return; // Informant write throttled to once per 3s
  lastDbSyncTimes.set(vehicleId, now);

  Vehicle.updateOne(
    { vehicleId },
    {
      $set: {
        connected: true,
        lastSeen: new Date(),
        telemetry,
      },
    },
    { upsert: true }
  ).catch((err) => {
    // Non-blocking informant: do not crash if DB write fails
    console.debug("[DB Informant] Vehicle sync notice:", err.message);
  });
}

export function startRosStatusGateway() {
  if (ros && ros.isConnected) {
    return;
  }

  try {
    ros = new Ros({
      url: ROSBRIDGE_URL,
    });

    ros.on("connection", () => {
      console.log("[ROS] Status gateway connected to", ROSBRIDGE_URL);
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }

      // 1. Drone Command Status & ACKs
      const statusTopic = new Topic({
        ros,
        name: "/gcs/drone/command_status",
        messageType: "std_msgs/String",
      });

      statusTopic.subscribe(async (message) => {
        try {
          const rawData = String(message?.data || "").trim();
          if (!rawData) return;

          let jsonPayload = null;
          try {
            if (rawData.startsWith("{") && rawData.endsWith("}")) {
              jsonPayload = JSON.parse(rawData);
            }
          } catch (_) {}

          if (jsonPayload && jsonPayload.commandId && jsonPayload.status) {
            const command = await updateCommandStatus(
              jsonPayload.commandId,
              jsonPayload.status,
              jsonPayload.reason ?? null
            );
            broadcast({ type: "command_status", command });
            return;
          }

          let parsedAck = null;
          const ackMatch = rawData.match(
            /^ACK\s+command=(\d+)\s+result=(\d+)(?:\s+param1=([^\s]+))?(?:\s+param2=([^\s]+))?/i
          );

          if (ackMatch) {
            parsedAck = {
              commandCode: Number(ackMatch[1]),
              resultCode: Number(ackMatch[2]),
              success: Number(ackMatch[2]) === 0,
              param1: ackMatch[3] ?? null,
              param2: ackMatch[4] ?? null,
            };
          }

          try {
            const recent = await getRecentCommands(5);
            const pending = recent.find((c) => c.status === "SENT" || c.status === "CREATED");

            if (pending) {
              let nextStatus = "EXECUTING";
              let reason = rawData;

              if (parsedAck) {
                nextStatus = parsedAck.success ? "COMPLETED" : "FAILED";
                reason = `PX4 result=${parsedAck.resultCode}`;
              } else if (rawData.startsWith("ERROR") || rawData.startsWith("UNKNOWN")) {
                nextStatus = "FAILED";
              } else if (rawData.startsWith("SENT")) {
                nextStatus = "SENT";
              }

              const updated = await updateCommandStatus(
                pending.commandId,
                nextStatus,
                reason
              );
              broadcast({ type: "command_status", command: updated });
            }
          } catch (_) {}

          broadcast({
            type: "ros_status",
            data: {
              raw: rawData,
              parsedAck,
              timestamp: new Date().toISOString(),
            },
          });
        } catch (error) {
          console.error("[ROS] Error processing command status:", error?.message || error);
        }
      });

      // 2. Drone Telemetry (String from demo_node or bridge)
      const droneTelTopic = new Topic({
        ros,
        name: "/drone/telemetry",
        messageType: "std_msgs/String",
      });
      droneTelTopic.subscribe((message) => {
        const drone = getVehicleByType("drone");
        if (!drone) return;
        let parsed = {};
        try {
          parsed = typeof message.data === "string" ? JSON.parse(message.data) : message.data;
        } catch (_) {}
        updateTelemetry(drone.vehicleId, parsed);
        asyncSyncToMongo(drone.vehicleId, parsed);
        queueStateBroadcast();
      });

      // 3. Drone Pose
      const dronePoseTopic = new Topic({
        ros,
        name: "/drone/pose",
        messageType: "geometry_msgs/PoseStamped",
      });
      dronePoseTopic.subscribe((message) => {
        const drone = getVehicleByType("drone");
        if (!drone) return;
        const pos = message.pose?.position || { x: 0, y: 0, z: 0 };
        updateTelemetry(drone.vehicleId, { position: { x: pos.x, y: pos.y, z: pos.z } });
        queueStateBroadcast();
      });

      // 4. Rover Telemetry
      const roverTelTopic = new Topic({
        ros,
        name: "/rover/telemetry",
        messageType: "std_msgs/String",
      });
      roverTelTopic.subscribe((message) => {
        const rover = getVehicleByType("rover");
        if (!rover) return;
        let parsed = {};
        try {
          parsed = typeof message.data === "string" ? JSON.parse(message.data) : message.data;
        } catch (_) {}
        updateTelemetry(rover.vehicleId, parsed);
        asyncSyncToMongo(rover.vehicleId, parsed);
        queueStateBroadcast();
      });

      // 5. Rover Pose / Odom
      const roverPoseTopic = new Topic({
        ros,
        name: "/rover/pose",
        messageType: "geometry_msgs/PoseStamped",
      });
      roverPoseTopic.subscribe((message) => {
        const rover = getVehicleByType("rover");
        if (!rover) return;
        const pos = message.pose?.position || { x: 0, y: 0, z: 0 };
        updateTelemetry(rover.vehicleId, { position: { x: pos.x, y: pos.y, z: pos.z } });
        queueStateBroadcast();
      });

      // 6. Rover Environment
      const roverEnvTopic = new Topic({
        ros,
        name: "/rover/environment",
        messageType: "std_msgs/String",
      });
      roverEnvTopic.subscribe((message) => {
        const rover = getVehicleByType("rover");
        if (!rover) return;
        let parsed = {};
        try {
          parsed = typeof message.data === "string" ? JSON.parse(message.data) : message.data;
        } catch (_) {}
        const current = getVehicle(rover.vehicleId);
        updateTelemetry(rover.vehicleId, {
          environment: { ...(current?.telemetry?.environment || {}), ...parsed },
        });
        queueStateBroadcast();
      });

      // 7. PX4 Vehicle Status (Arming, Nav State, Failsafe)
      const px4StatusTopic = new Topic({
        ros,
        name: "/fmu/out/vehicle_status_v4",
        messageType: "px4_msgs/msg/VehicleStatus",
      });
      px4StatusTopic.subscribe((msg) => {
        const drone = getVehicleByType("drone");
        if (!drone) return;
        const isArmed = msg.arming_state === 2; // ARMING_STATE_ARMED
        updateTelemetry(drone.vehicleId, {
          armed: isArmed,
          navState: msg.nav_state,
          failsafe: Boolean(msg.failsafe),
        });
        queueStateBroadcast();
      });

      // 8. PX4 Battery Status
      const px4BatteryTopic = new Topic({
        ros,
        name: "/fmu/out/battery_status_v1",
        messageType: "px4_msgs/msg/BatteryStatus",
      });
      px4BatteryTopic.subscribe((msg) => {
        const drone = getVehicleByType("drone");
        if (!drone) return;
        const remaining =
          msg.remaining !== undefined && msg.remaining >= 0
            ? Math.round(msg.remaining * 100)
            : undefined;
        updateTelemetry(drone.vehicleId, {
          battery: remaining,
          voltage: msg.voltage_v,
        });
        queueStateBroadcast();
      });

      // 9. PX4 Local Position
      const px4PosTopic = new Topic({
        ros,
        name: "/fmu/out/vehicle_local_position_v1",
        messageType: "px4_msgs/msg/VehicleLocalPosition",
      });
      px4PosTopic.subscribe((msg) => {
        const drone = getVehicleByType("drone");
        if (!drone) return;
        updateTelemetry(drone.vehicleId, {
          position: { x: msg.x ?? 0, y: msg.y ?? 0, z: -(msg.z ?? 0) },
        });
        queueStateBroadcast();
      });

      // Periodic staleness check: mark disconnected if no message in 15 seconds
      if (!stalenessTimer) {
        stalenessTimer = setInterval(() => {
          const changed = markStaleVehicles(15000);
          if (changed) {
            queueStateBroadcast();
          }
        }, 2000);
      }
    });

    ros.on("error", (error) => {
      console.warn("[ROS] Status gateway connection warning:", error?.message || error);
      if (ros) {
        try {
          ros.close();
        } catch (_) {}
        ros = null;
      }
      scheduleReconnect();
    });

    ros.on("close", () => {
      console.log("[ROS] Status gateway disconnected; scheduling reconnect...");
      ros = null;
      if (stalenessTimer) {
        clearInterval(stalenessTimer);
        stalenessTimer = null;
      }
      scheduleReconnect();
    });
  } catch (err) {
    console.warn("[ROS] Could not initialize status gateway Ros:", err?.message || err);
    scheduleReconnect();
  }
}
