import { Vehicle } from "../models/Vehicle.js";
import { Telemetry } from "../models/Telemetry.js";
import { Detection } from "../models/Detection.js";
import { Sensor } from "../models/Sensor.js";
import { Hazard } from "../models/Hazard.js";
import { RiskEvent } from "../models/RiskEvent.js";
import { Mission } from "../models/Mission.js";
import { Map } from "../models/Map.js";
import { Command } from "../models/Command.js";

export async function getStateSnapshot() {
  const [
    vehicles,
    telemetry,
    detections,
    sensors,
    hazards,
    riskEvents,
    missions,
    latestMap,
    commands,
  ] = await Promise.all([
    Vehicle.find({}).lean(),

    Telemetry.find({})
      .sort({ timestamp: -1 })
      .limit(100)
      .lean(),

    Detection.find({})
      .sort({ timestamp: -1 })
      .limit(100)
      .lean(),

    Sensor.find({})
      .sort({ timestamp: -1 })
      .lean(),

    Hazard.find({})
      .sort({ timestamp: -1 })
      .limit(100)
      .lean(),

    RiskEvent.find({})
      .sort({ timestamp: -1 })
      .limit(100)
      .lean(),

    Mission.find({})
      .sort({ timestamp: -1 })
      .lean(),

    Map.findOne({})
      .sort({ timestamp: -1 })
      .lean(),

    Command.find({})
      .sort({ createdAt: -1 })
      .limit(100)
      .lean(),
  ]);

  const latestTelemetryByVehicle = {};
  for (const t of telemetry) {
    if (!latestTelemetryByVehicle[t.vehicleId]) {
      latestTelemetryByVehicle[t.vehicleId] = t.data;
    }
  }

  const vehicleState =
    Object.fromEntries(
      vehicles.map((vehicle) => {
        const latest = latestTelemetryByVehicle[vehicle.vehicleId] || vehicle.telemetry;
        return [
          vehicle.vehicleId,
          {
            ...vehicle,
            telemetry: latest,
            position: latest?.position ?? vehicle.position,
          },
        ];
      })
    );

  const detectionState =
    Object.fromEntries(
      detections.map((detection) => [
        detection.detectionId,
        detection,
      ])
    );

  const sensorState =
    Object.fromEntries(
      sensors.map((sensor) => [
        sensor.sensorId,
        sensor,
      ])
    );

  const hazardState =
    Object.fromEntries(
      hazards.map((hazard) => [
        hazard.hazardId,
        hazard,
      ])
    );

  const riskEventState =
    Object.fromEntries(
      riskEvents.map((event) => [
        event.riskId,
        event,
      ])
    );

  const missionState =
    Object.fromEntries(
      missions.map((mission) => [
        mission.missionId,
        mission,
      ])
    );

  return {
    vehicles: vehicleState,
    telemetry,
    detections: detectionState,
    sensors: sensorState,
    hazards: hazardState,
    risk_events: riskEventState,
    missions: missionState,
    map: latestMap,
    commands,
  };
}
