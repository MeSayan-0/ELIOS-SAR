import { randomUUID } from "crypto";

import { Command } from "../models/Command.js";
import { Vehicle } from "../models/Vehicle.js";
import { createSystemEvent } from "./systemEventService.js";

const DRONE_COMMANDS = new Set([
  "ARM",
  "DISARM",
  "OFFBOARD",
  "TAKEOFF",
  "HOVER",
  "LAND",
  "RETURN_TO_DOCK",
  "RTL",
  "ABORT",
]);

const ROVER_COMMANDS = new Set([
  "FORWARD",
  "BACK",
  "LEFT",
  "RIGHT",
  "STOP",
  "DOCK",
  "UNDOCK",
]);

const CONFIRM_COMMANDS = new Set([
  "TAKEOFF",
  "LAND",
  "RETURN_TO_DOCK",
  "RTL",
  "ABORT",
  "DOCK",
  "UNDOCK",
]);

export function getAllowedCommands(vehicleType) {
  if (vehicleType === "drone") {
    return [...DRONE_COMMANDS];
  }

  if (vehicleType === "rover") {
    return [...ROVER_COMMANDS];
  }

  return [];
}

export function commandRequiresConfirmation(command) {
  return CONFIRM_COMMANDS.has(command);
}

function normalizeCommand(command) {
  if (typeof command !== "string") {
    throw new Error("command is required");
  }

  return command
    .trim()
    .toUpperCase();
}

function validateVehicleCommand(
  vehicle,
  command
) {
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

function validateVehicleSafety(
  vehicle,
  command
) {
  if (!vehicle.connected) {
    throw new Error(
      "vehicle is offline"
    );
  }

  const telemetry =
    vehicle.telemetry ?? {};

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
    throw new Error(
      "vehicle is in failsafe state"
    );
  }
}

export async function createCommand({
  vehicleId,
  command,
  metadata = {},
}) {
  if (!vehicleId) {
    throw new Error(
      "vehicleId is required"
    );
  }

  const normalizedCommand =
    normalizeCommand(command);

  const vehicle =
    await Vehicle.findOne({
      vehicleId,
    });

  if (!vehicle) {
    throw new Error(
      "vehicle not found"
    );
  }

  validateVehicleCommand(
    vehicle,
    normalizedCommand
  );

  validateVehicleSafety(
    vehicle,
    normalizedCommand
  );

  const now = new Date();

  const commandRecord =
    await Command.create({
      commandId: randomUUID(),
      vehicleId: vehicle.vehicleId,
      vehicleType: vehicle.vehicleType,
      command: normalizedCommand,
      status: "CREATED",
      source: "GCS",
      metadata,
      createdAt: now,
      updatedAt: now,
    });

  try {
    await createSystemEvent({
      level: "INFO",
      source: "GCS",
      eventType: "COMMAND",
      vehicleId: vehicle.vehicleId,
      message: `${normalizedCommand} command sent`,
      metadata: {
        commandId: commandRecord.commandId,
        command: normalizedCommand,
      },
    });
  } catch (err) {
    // non-blocking
  }

  return {
    command: commandRecord.toObject(),
    vehicle: vehicle.toObject(),
  };
}

export async function updateCommandStatus(
  commandId,
  status,
  reason = null
) {
  const command =
    await Command.findOne({
      commandId,
    });

  if (!command) {
    throw new Error(
      "command not found"
    );
  }

  command.status = status;
  command.reason = reason;
  command.updatedAt = new Date();

  await command.save();

  return command.toObject();
}

export async function rejectCommand(
  commandId,
  reason
) {
  return updateCommandStatus(
    commandId,
    "REJECTED",
    reason
  );
}

export async function getRecentCommands(
  limit = 100
) {
  return Command.find({})
    .sort({
      createdAt: -1,
    })
    .limit(limit)
    .lean();
}

export async function getVehicleCommands(
  vehicleId,
  limit = 100
) {
  return Command.find({
    vehicleId,
  })
    .sort({
      createdAt: -1,
    })
    .limit(limit)
    .lean();
}
