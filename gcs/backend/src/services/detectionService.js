import { randomUUID } from "crypto";

import { Detection } from "../models/Detection.js";
import { Vehicle } from "../models/Vehicle.js";

export async function ingestDetection(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Detection payload must be an object");
  }

  const {
    vehicleId,
    timestamp,
    data,
  } = payload;

  if (!vehicleId) {
    throw new Error("vehicleId is required");
  }

  if (!timestamp) {
    throw new Error("timestamp is required");
  }

  if (!data || typeof data !== "object") {
    throw new Error("data is required");
  }

  const vehicle =
    await Vehicle.findOne({
      vehicleId,
    });

  if (!vehicle) {
    throw new Error(
      "vehicle is not registered"
    );
  }

  const detectionId =
    payload.detectionId || randomUUID();

  const detection =
    await Detection.create({
      vehicleId,
      detectionId,
      timestamp: new Date(timestamp),
      data,
    });

  await Vehicle.findOneAndUpdate(
    { vehicleId },
    {
      $set: {
        connected: true,
        lastSeen: new Date(),
      },
    }
  );

  return detection.toObject();
}
