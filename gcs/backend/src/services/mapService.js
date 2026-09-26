import { Map } from "../models/Map.js";
import { Vehicle } from "../models/Vehicle.js";

function validateMapPayload(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Map payload must be an object");
  }

  if (!payload.mapId) {
    throw new Error("mapId is required");
  }

  if (!["global", "local"].includes(payload.mapType)) {
    throw new Error(
      "mapType must be global or local"
    );
  }

  if (!payload.frameId) {
    throw new Error("frameId is required");
  }

  if (!payload.timestamp) {
    throw new Error("timestamp is required");
  }

  if (
    typeof payload.resolution !== "number" ||
    payload.resolution <= 0
  ) {
    throw new Error(
      "resolution must be a positive number"
    );
  }

  if (
    !Number.isInteger(payload.width) ||
    payload.width <= 0
  ) {
    throw new Error(
      "width must be a positive integer"
    );
  }

  if (
    !Number.isInteger(payload.height) ||
    payload.height <= 0
  ) {
    throw new Error(
      "height must be a positive integer"
    );
  }

  if (!payload.origin || typeof payload.origin !== "object") {
    throw new Error("origin is required");
  }

  if (
    typeof payload.origin.x !== "number" ||
    typeof payload.origin.y !== "number"
  ) {
    throw new Error(
      "origin.x and origin.y are required"
    );
  }

  if (!Array.isArray(payload.grid)) {
    throw new Error("grid must be an array");
  }

  const expectedCells =
    payload.width * payload.height;

  if (payload.grid.length !== expectedCells) {
    throw new Error(
      `grid length must equal width * height (${expectedCells})`
    );
  }
}

export async function ingestMap(payload) {
  validateMapPayload(payload);

  if (payload.vehicleId) {
    const vehicle = await Vehicle.findOne({
      vehicleId: payload.vehicleId,
    });

    if (!vehicle) {
      throw new Error(
        `Vehicle not registered: ${payload.vehicleId}`
      );
    }
  }

  const map = await Map.findOneAndUpdate(
    {
      mapId: payload.mapId,
    },
    {
      $set: {
        mapId: payload.mapId,
        mapType: payload.mapType,
        vehicleId: payload.vehicleId ?? null,
        missionId: payload.missionId ?? null,
        frameId: payload.frameId,
        timestamp: new Date(payload.timestamp),
        resolution: payload.resolution,
        width: payload.width,
        height: payload.height,
        origin: {
          x: payload.origin.x,
          y: payload.origin.y,
          z: payload.origin.z ?? 0,
          yaw: payload.origin.yaw ?? 0,
        },
        grid: payload.grid,
        metadata: payload.metadata ?? {},
      },
    },
    {
      new: true,
      upsert: true,
      setDefaultsOnInsert: true,
    }
  ).lean();

  return map;
}

export async function getMap(mapId) {
  return Map.findOne({
    mapId,
  }).lean();
}

export async function getLatestMap({
  mapType,
  vehicleId,
  missionId,
}) {
  const query = {
    mapType,
  };

  if (vehicleId) {
    query.vehicleId = vehicleId;
  }

  if (missionId) {
    query.missionId = missionId;
  }

  return Map.findOne(query)
    .sort({ timestamp: -1 })
    .lean();
}

export async function getMaps({
  mapType,
  vehicleId,
  missionId,
}) {
  const query = {};

  if (mapType) {
    query.mapType = mapType;
  }

  if (vehicleId) {
    query.vehicleId = vehicleId;
  }

  if (missionId) {
    query.missionId = missionId;
  }

  return Map.find(query)
    .sort({ timestamp: -1 })
    .lean();
}
