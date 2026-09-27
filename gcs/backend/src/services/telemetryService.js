import { Telemetry } from "../models/Telemetry.js";
import { Vehicle } from "../models/Vehicle.js";

export async function ingestTelemetry(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Telemetry payload must be an object");
  }

  const {
    vehicleId,
    timestamp,
    data,
  } = payload;

  if (!vehicleId) {
    throw new Error("vehicleId is required");
  }

  if (!data || typeof data !== "object") {
    throw new Error("data is required");
  }

  const vehicle = await Vehicle.findOne({
    vehicleId,
  });

  if (!vehicle) {
    throw new Error(
      `Vehicle ${vehicleId} is not registered`
    );
  }

  const telemetryTimestamp =
    timestamp
      ? new Date(timestamp)
      : new Date();

  if (
    Number.isNaN(
      telemetryTimestamp.getTime()
    )
  ) {
    throw new Error(
      "timestamp must be a valid date"
    );
  }

  const telemetry =
    await Telemetry.create({
      vehicleId,
      timestamp: telemetryTimestamp,
      data,
    });

  vehicle.connected = true;
  vehicle.lastSeen = new Date();
  vehicle.telemetry = data;

  await vehicle.save();

  return {
    telemetry: telemetry.toObject(),
    vehicle: vehicle.toObject(),
  };
}
