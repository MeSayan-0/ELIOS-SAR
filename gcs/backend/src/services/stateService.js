import mongoose from "mongoose";
import { Vehicle } from "../models/Vehicle.js";
import { Telemetry } from "../models/Telemetry.js";
import { Detection } from "../models/Detection.js";
import { Sensor } from "../models/Sensor.js";
import { Hazard } from "../models/Hazard.js";
import { RiskEvent } from "../models/RiskEvent.js";
import { Mission } from "../models/Mission.js";
import { Map } from "../models/Map.js";
import { Command } from "../models/Command.js";
import {
  getAllVehicles as getInMemoryVehicles,
  getStateSnapshot as getInMemorySnapshot,
} from "./gcsState.js";

export async function getStateSnapshot() {
  const inMemoryState = getInMemorySnapshot();

  // Baseline vehicle state comes directly from live in-memory registry (single source of truth)
  const vehicleState = { ...inMemoryState.vehicles };

  if (mongoose.connection.readyState !== 1) {
    return {
      vehicles: vehicleState,
      telemetry: [],
      detections: inMemoryState.detections || {},
      sensors: inMemoryState.sensors || {},
      hazards: {},
      risk_events: {},
      missions: inMemoryState.missions || {},
      map: null,
      commands: [],
    };
  }

  try {
    const [
      dbVehicles,
      telemetry,
      detections,
      sensors,
      hazards,
      riskEvents,
      missions,
      latestMap,
      commands,
    ] = await Promise.all([
      Vehicle.find({}).lean().catch(() => []),
      Telemetry.find({}).sort({ timestamp: -1 }).limit(100).lean().catch(() => []),
      Detection.find({}).sort({ timestamp: -1 }).limit(100).lean().catch(() => []),
      Sensor.find({}).sort({ timestamp: -1 }).lean().catch(() => []),
      Hazard.find({}).sort({ timestamp: -1 }).limit(100).lean().catch(() => []),
      RiskEvent.find({}).sort({ timestamp: -1 }).limit(100).lean().catch(() => []),
      Mission.find({}).sort({ timestamp: -1 }).lean().catch(() => []),
      Map.findOne({}).sort({ timestamp: -1 }).lean().catch(() => null),
      Command.find({}).sort({ createdAt: -1 }).limit(100).lean().catch(() => []),
    ]);

    // Merge in-memory live vehicles with DB metadata
    for (const dbV of dbVehicles) {
      if (!vehicleState[dbV.vehicleId]) {
        vehicleState[dbV.vehicleId] = {
          ...dbV,
          connected: false,
        };
      }
    }

    const detectionState = Object.fromEntries(
      (detections || []).map((detection) => [detection.detectionId, detection])
    );

    const sensorState = Object.fromEntries(
      (sensors || []).map((sensor) => [sensor.sensorId, sensor])
    );

    const hazardState = Object.fromEntries(
      (hazards || []).map((hazard) => [hazard.hazardId, hazard])
    );

    const riskEventState = Object.fromEntries(
      (riskEvents || []).map((event) => [event.riskId, event])
    );

    const missionState = Object.fromEntries(
      (missions || []).map((mission) => [mission.missionId, mission])
    );

    return {
      vehicles: vehicleState,
      telemetry: telemetry || [],
      detections: { ...inMemoryState.detections, ...detectionState },
      sensors: { ...inMemoryState.sensors, ...sensorState },
      hazards: hazardState,
      risk_events: riskEventState,
      missions: { ...inMemoryState.missions, ...missionState },
      map: latestMap,
      commands: commands || [],
    };
  } catch (err) {
    console.debug("[StateService] DB informant lookup notice:", err.message);
    return {
      vehicles: vehicleState,
      telemetry: [],
      detections: inMemoryState.detections || {},
      sensors: inMemoryState.sensors || {},
      hazards: {},
      risk_events: {},
      missions: inMemoryState.missions || {},
      map: null,
      commands: [],
    };
  }
}
