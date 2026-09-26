const state = {
  vehicles: new Map(),
  sensors: new Map(),
  detections: new Map(),
  missions: new Map(),
};

export function getStateSnapshot() {
  return {
    vehicles: Object.fromEntries(state.vehicles),
    sensors: Object.fromEntries(state.sensors),
    detections: Object.fromEntries(state.detections),
    missions: Object.fromEntries(state.missions),
  };
}

export function registerVehicle(vehicle) {
  if (!vehicle?.vehicleId) {
    throw new Error("vehicleId is required");
  }

  if (!vehicle?.vehicleType) {
    throw new Error("vehicleType is required");
  }

  const now = new Date().toISOString();

  const registeredVehicle = {
    ...vehicle,
    connected: true,
    lastSeen: vehicle.lastSeen ?? now,
  };

  state.vehicles.set(
    vehicle.vehicleId,
    registeredVehicle
  );

  return registeredVehicle;
}

export function updateVehicle(vehicleId, update) {
  if (!vehicleId) {
    throw new Error("vehicleId is required");
  }

  const existing = state.vehicles.get(vehicleId);

  if (!existing) {
    throw new Error("vehicle is not registered");
  }

  const updated = {
    ...existing,
    ...update,
    vehicleId: existing.vehicleId,
    vehicleType: existing.vehicleType,
    lastSeen: new Date().toISOString(),
    connected: true,
  };

  state.vehicles.set(
    vehicleId,
    updated
  );

  return updated;
}

export function updateTelemetry(
  vehicleId,
  telemetry
) {
  if (!vehicleId) {
    throw new Error("vehicleId is required");
  }

  if (!telemetry || typeof telemetry !== "object") {
    throw new Error("telemetry must be an object");
  }

  const existing =
    state.vehicles.get(vehicleId);

  if (!existing) {
    throw new Error(
      "vehicle is not registered"
    );
  }

  const updated = {
    ...existing,
    telemetry: {
      ...(existing.telemetry ?? {}),
      ...telemetry,
    },
    connected: true,
    lastSeen:
      new Date().toISOString(),
  };

  state.vehicles.set(
    vehicleId,
    updated
  );

  return updated;
}

export function markVehicleDisconnected(
  vehicleId
) {
  const existing =
    state.vehicles.get(vehicleId);

  if (!existing) {
    return null;
  }

  const updated = {
    ...existing,
    connected: false,
  };

  state.vehicles.set(
    vehicleId,
    updated
  );

  return updated;
}

export function removeVehicle(
  vehicleId
) {
  state.vehicles.delete(vehicleId);
}

export function updateSensor(sensor) {
  if (!sensor?.sensorId) {
    throw new Error(
      "sensorId is required"
    );
  }

  state.sensors.set(
    sensor.sensorId,
    {
      ...sensor,
    }
  );
}

export function updateDetection(
  detection
) {
  if (!detection?.detectionId) {
    throw new Error(
      "detectionId is required"
    );
  }

  state.detections.set(
    detection.detectionId,
    {
      ...detection,
    }
  );
}

export function updateMission(
  mission
) {
  if (!mission?.missionId) {
    throw new Error(
      "missionId is required"
    );
  }

  state.missions.set(
    mission.missionId,
    {
      ...mission,
    }
  );
}
