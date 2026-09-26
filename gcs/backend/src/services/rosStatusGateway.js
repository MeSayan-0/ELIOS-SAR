import { Ros, Topic } from "roslib";

import {
  updateCommandStatus,
  getRecentCommands,
} from "./commandService.js";

import {
  broadcast,
} from "../websocket/manager.js";

const ROSBRIDGE_URL =
  process.env.ROSBRIDGE_URL ||
  "ws://127.0.0.1:9090";

let ros = null;
let statusTopic = null;

export function startRosStatusGateway() {
  if (ros) {
    return;
  }

  try {
    ros = new Ros({
      url: ROSBRIDGE_URL,
    });

    ros.on(
      "connection",
      () => {
        console.log(
          "[ROS] Status gateway connected"
        );

        statusTopic =
          new Topic({
            ros,
            name:
              "/gcs/drone/command_status",
            messageType:
              "std_msgs/String",
          });

        statusTopic.subscribe(
          async (message) => {
            try {
              const rawData = String(message?.data || "").trim();
              if (!rawData) return;

              // 1. Try parsing JSON format
              let jsonPayload = null;
              try {
                if (rawData.startsWith("{") && rawData.endsWith("}")) {
                  jsonPayload = JSON.parse(rawData);
                }
              } catch (_) {
                jsonPayload = null;
              }

              if (jsonPayload && jsonPayload.commandId && jsonPayload.status) {
                const command =
                  await updateCommandStatus(
                    jsonPayload.commandId,
                    jsonPayload.status,
                    jsonPayload.reason ?? null
                  );

                broadcast({
                  type: "command_status",
                  command,
                });
                return;
              }

              // 2. Parse raw string from px4_bridge (e.g., "SENT ARM", "ACK command=...", "ERROR ...")
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

              // Try correlating with the most recent SENT command if available
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

                  broadcast({
                    type: "command_status",
                    command: updated,
                  });
                }
              } catch (dbErr) {
                // Non-blocking if database is unavailable
              }

              // Broadcast raw ROS bridge status to frontend clients
              broadcast({
                type: "ros_status",
                data: {
                  raw: rawData,
                  parsedAck,
                  timestamp: new Date().toISOString(),
                },
              });

            } catch (error) {
              console.error(
                "[ROS] Error processing command status:",
                error?.message || error
              );
            }
          }
        );
      }
    );

    ros.on(
      "error",
      (error) => {
        console.warn(
          "[ROS] Status gateway connection error:",
          error?.message || error
        );
      }
    );

    ros.on(
      "close",
      () => {
        console.log(
          "[ROS] Status gateway disconnected"
        );

        statusTopic = null;
        ros = null;
      }
    );
  } catch (err) {
    console.warn("[ROS] Could not initialize status gateway Ros:", err?.message || err);
  }
}
