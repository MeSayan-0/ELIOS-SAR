import { randomUUID } from "crypto";

import { Vehicle } from "../models/Vehicle.js";
import { Sensor } from "../models/Sensor.js";
import { Hazard } from "../models/Hazard.js";
import { RiskEvent } from "../models/RiskEvent.js";
import { Mission } from "../models/Mission.js";

async function requireVehicle(vehicleId) {
  if (!vehicleId) {
    throw new Error("vehicleId is required");
  }

  const vehicle =
    await Vehicle.findOne({ vehicleId });

  if (!vehicle) {
    throw new Error(
      "vehicle is not registered"
    );
  }

  return vehicle;
}

function requireTimestamp(timestamp) {
  if (!timestamp) {
    throw new Error("timestamp is required");
  }

  const parsed =
    new Date(timestamp);

  if (Number.isNaN(parsed.getTime())) {
    throw new Error(
      "timestamp must be a valid date"
    );
  }

  return parsed;
}

function requireData(data) {
  if (
    !data ||
    typeof data !== "object" ||
    Array.isArray(data)
  ) {
    throw new Error(
      "data must be an object"
    );
  }
}

export async function ingestSensor(
  payload
) {
  const {
    vehicleId,
    sensorId,
    sensorType,
    timestamp,
    data,
  } = payload;

  await requireVehicle(vehicleId);

  if (!sensorId) {
    throw new Error(
      "sensorId is required"
    );
  }

  if (!sensorType) {
    throw new Error(
      "sensorType is required"
    );
  }

  requireData(data);

  const parsedTimestamp =
    requireTimestamp(timestamp);

  const sensor =
    await Sensor.findOneAndUpdate(
      { sensorId },
      {
        vehicleId,
        sensorId,
        sensorType,
        timestamp: parsedTimestamp,
        data,
      },
      {
        new: true,
        upsert: true,
        setDefaultsOnInsert: true,
      }
    );

  return sensor.toObject();
}

export async function ingestHazard(
  payload
) {
  const {
    vehicleId,
    hazardId,
    timestamp,
    data,
  } = payload;

  await requireVehicle(vehicleId);

  const finalHazardId =
    hazardId || randomUUID();

  requireData(data);

  const parsedTimestamp =
    requireTimestamp(timestamp);

  const hazard =
    await Hazard.findOneAndUpdate(
      { hazardId: finalHazardId },
      {
        vehicleId,
        hazardId: finalHazardId,
        timestamp: parsedTimestamp,
        data,
      },
      {
        new: true,
        upsert: true,
        setDefaultsOnInsert: true,
      }
    );

  return hazard.toObject();
}

export async function ingestRiskEvent(
  payload
) {
  const {
    vehicleId,
    riskId,
    timestamp,
    data,
  } = payload;

  await requireVehicle(vehicleId);

  const finalRiskId =
    riskId || randomUUID();

  requireData(data);

  const parsedTimestamp =
    requireTimestamp(timestamp);

  const riskEvent =
    await RiskEvent.findOneAndUpdate(
      { riskId: finalRiskId },
      {
        vehicleId,
        riskId: finalRiskId,
        timestamp: parsedTimestamp,
        data,
      },
      {
        new: true,
        upsert: true,
        setDefaultsOnInsert: true,
      }
    );

  return riskEvent.toObject();
}

export async function ingestMission(
  payload
) {
  const {
    missionId,
    vehicleId,
    timestamp,
    data,
  } = payload;

  if (!missionId) {
    throw new Error(
      "missionId is required"
    );
  }

  if (vehicleId) {
    await requireVehicle(vehicleId);
  }

  requireData(data);

  const parsedTimestamp =
    requireTimestamp(timestamp);

  const mission =
    await Mission.findOneAndUpdate(
      { missionId },
      {
        missionId,
        vehicleId,
        timestamp: parsedTimestamp,
        data,
      },
      {
        new: true,
        upsert: true,
        setDefaultsOnInsert: true,
      }
    );

  return mission.toObject();
}
