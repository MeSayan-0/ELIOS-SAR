import { Vehicle } from "../models/Vehicle.js";

export async function registerVehicle(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Vehicle payload must be an object");
  }

  const vehicleId = payload.vehicleId;
  const vehicleType = payload.vehicleType;

  if (!vehicleId) {
    throw new Error("vehicleId is required");
  }

  if (!vehicleType) {
    throw new Error("vehicleType is required");
  }

  if (!["drone", "rover"].includes(vehicleType)) {
    throw new Error("vehicleType must be drone or rover");
  }

  const now = new Date();

  const vehicle = await Vehicle.findOneAndUpdate(
    { vehicleId },
    {
      $set: {
        vehicleId,
        vehicleType,
        connected: true,
        lastSeen: now,
      },
    },
    {
      new: true,
      upsert: true,
      setDefaultsOnInsert: true,
    }
  ).lean();

  return vehicle;
}
