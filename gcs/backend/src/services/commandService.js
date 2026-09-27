import { randomUUID } from "node:crypto";
import mongoose from "mongoose";

import { Command } from "../models/Command.js";
import { Vehicle } from "../models/Vehicle.js";
import { createSystemEvent } from "./systemEventService.js";
import { getVehicle, isVehicleOnline } from "./gcsState.js";
import { isRosCommandConnected } from "./rosCommandGateway.js";

const DRONE_COMMANDS = new Set([
  "ARM",
  "DISARM",
  "TAKEOFF",
  "LAND",
  "OFFBOARD",
  "HOLD",
  "RTL",
  "RETURN_TO_DOCK",
  "DOCK",
  "ABORT",
]);

const ROVER_COMMANDS = new Set([
  "FORWARD",
  "BACK",
  "LEFT",
  "RIGHT",
  "STOP",
  "RETURN_TO_DOCK",
  "DOCK",
  "ABORT",
]);

function normalizeCommand(command) {
  if (typeof command !== "string") {
    throw new Error("command must be a string");
  }
  const cmd = command.trim().toUpperCase();
  if (cmd === "DOCK") return "RETURN_TO_DOCK";
  return cmd;
}

function validateVehicleCommand(vehicle, command) {
  const allowed =
    vehicle.vehicleType === "drone"
      ? DRONE_COMMANDS
      : ROVER_COMMANDS;

  if (!allowed.has(command)) {
    throw new Error(
      `${command} is not valid for ${vehicle.vehicleType}`
    );
  }
}

function validateVehicleSafety(vehicle, command) {
  const online = isVehicleOnline(vehicle.vehicleId);
  const rosConnected = isRosCommandConnected();

  // Allow command if vehicle is actively reporting telemetry in-memory OR ROS command gateway is connected
  if (!online && !rosConnected && !vehicle.connected) {
    throw new Error("vehicle is offline");
  }

  const telemetry = vehicle.telemetry ?? {};

  if (
    telemetry.failsafe === true &&
    ![
      "LAND",
      "RTL",
      "RETURN_TO_DOCK",
      "ABORT",
      "STOP",
    ].includes(command)
  ) {
    throw new Error("vehicle is in failsafe state");
  }
}

export async function createCommand({
  vehicleId,
  command,
  metadata = {},
}) {
  if (!vehicleId) {
    throw new Error("vehicleId is required");
  }

  const normalizedCommand = normalizeCommand(command);

  // 1. Resolve vehicle from in-memory state first (single source of truth)
  let vehicle = getVehicle(vehicleId);

  // 2. Fallback to MongoDB if not in memory
  if (!vehicle && mongoose.connection.readyState === 1) {
    vehicle = await Vehicle.findOne({ vehicleId }).lean();
  }

  if (!vehicle) {
    throw new Error("vehicle not found");
  }

  validateVehicleCommand(vehicle, normalizedCommand);
  validateVehicleSafety(vehicle, normalizedCommand);

  const now = new Date();
  const commandRecord = {
    commandId: randomUUID(),
    vehicleId: vehicle.vehicleId,
    vehicleType: vehicle.vehicleType,
    command: normalizedCommand,
    status: "CREATED",
    source: "GCS",
    metadata,
    createdAt: now,
    updatedAt: now,
  };

  // 3. Asynchronously record to MongoDB (informant - non-blocking)
  if (mongoose.connection.readyState === 1) {
    Command.create(commandRecord).catch((err) => {
      console.debug("[DB Informant] Command record notice:", err.message);
    });
  }

  // 4. Record system event asynchronously
  createSystemEvent({
    level: "INFO",
    source: "GCS",
    eventType: "COMMAND",
    vehicleId: vehicle.vehicleId,
    message: `${normalizedCommand} command sent`,
    metadata: {
      commandId: commandRecord.commandId,
      command: normalizedCommand,
    },
  }).catch(() => {});

  return {
    command: commandRecord,
    vehicle,
  };
}

export async function updateCommandStatus(
  commandId,
  status,
  reason = null
) {
  const updatedRecord = {
    commandId,
    status,
    reason,
    updatedAt: new Date(),
  };

  // Asynchronously update MongoDB informant
  if (mongoose.connection.readyState === 1) {
    Command.findOneAndUpdate(
      { commandId },
      { $set: { status, reason, updatedAt: new Date() } },
      { new: true }
    )
      .lean()
      .catch(() => {});
  }

  return updatedRecord;
}

export async function rejectCommand(commandId, reason) {
  return updateCommandStatus(commandId, "REJECTED", reason);
}

export async function getRecentCommands(limit = 100) {
  if (mongoose.connection.readyState !== 1) {
    return [];
  }

  try {
    return await Command.find({})
      .sort({ createdAt: -1 })
      .limit(limit)
      .lean();
  } catch (_) {
    return [];
  }
}

export async function getVehicleCommands(vehicleId, limit = 100) {
  if (mongoose.connection.readyState !== 1) {
    return [];
  }

  try {
    return await Command.find({ vehicleId })
      .sort({ createdAt: -1 })
      .limit(limit)
      .lean();
  } catch (_) {
    return [];
  }
}
