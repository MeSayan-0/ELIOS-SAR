import { DEFAULT_FLEET } from "../config/vehicles.js";

const state = {
  vehicles: new Map(),
  sensors: new Map(),
  detections: new Map(),
  missions: new Map(),
};

// Initialize vehicles from single source of truth (DEFAULT_FLEET)
for (const def of DEFAULT_FLEET) {
  state.vehicles.set(def.vehicleId, {
    ...def,
    connected: false,
    lastSeen: null,
    telemetry: {},
    position: { x: 0, y: 0, z: 0 },
  });
}

export function getStateSnapshot() {
  return {
    vehicles: Object.fromEntries(state.vehicles),
    sensors: Object.fromEntries(state.sensors),
    detections: Object.fromEntries(state.detections),
    missions: Object.fromEntries(state.missions),
  };
}

export function getVehicle(vehicleId) {
  return state.vehicles.get(vehicleId) || null;
}

export function getVehicleByType(vehicleType) {
  for (const v of state.vehicles.values()) {
    if (v.vehicleType === vehicleType) return v;
  }
  return null;
}

export function getAllVehicles() {
  return Array.from(state.vehicles.values());
}

export function isVehicleOnline(vehicleId, timeoutMs = 15000) {
  const v = state.vehicles.get(vehicleId);
  if (!v) return false;
  if (!v.lastSeen) return Boolean(v.connected);
  const elapsed = Date.now() - new Date(v.lastSeen).getTime();
  return Boolean(v.connected && elapsed < timeoutMs);
}

export function registerVehicle(vehicle) {
  if (!vehicle?.vehicleId) {
    throw new Error("vehicleId is required");
  }

  if (!vehicle?.vehicleType) {
    throw new Error("vehicleType is required");
  }

  const existing = state.vehicles.get(vehicle.vehicleId) || {};
  const now = new Date().toISOString();

  const registeredVehicle = {
    ...existing,
    ...vehicle,
    connected: true,
    lastSeen: vehicle.lastSeen ?? now,
  };

  state.vehicles.set(vehicle.vehicleId, registeredVehicle);
  return registeredVehicle;
}

export function updateVehicle(vehicleId, update) {
  if (!vehicleId) {
    throw new Error("vehicleId is required");
  }

  const existing = state.vehicles.get(vehicleId) || {
    vehicleId,
    vehicleType: update.vehicleType || "drone",
  };

  const updated = {
    ...existing,
    ...update,
    vehicleId: existing.vehicleId,
    vehicleType: existing.vehicleType,
    lastSeen: new Date().toISOString(),
    connected: true,
  };

  state.vehicles.set(vehicleId, updated);
  return updated;
}

export function updateTelemetry(vehicleId, telemetry) {
  if (!vehicleId) {
    throw new Error("vehicleId is required");
  }

  if (!telemetry || typeof telemetry !== "object") {
    throw new Error("telemetry must be an object");
  }

  const existing = state.vehicles.get(vehicleId) || {
    vehicleId,
    vehicleType: "drone",
  };

  const updated = {
    ...existing,
    telemetry: {
      ...(existing.telemetry ?? {}),
      ...telemetry,
    },
    position: telemetry.position ?? existing.position,
    connected: true,
    lastSeen: new Date().toISOString(),
  };

  state.vehicles.set(vehicleId, updated);
  return updated;
}

export function markVehicleDisconnected(vehicleId) {
  const existing = state.vehicles.get(vehicleId);
  if (!existing) return null;

  const updated = {
    ...existing,
    connected: false,
  };

  state.vehicles.set(vehicleId, updated);
  return updated;
}

export function markStaleVehicles(timeoutMs = 15000) {
  const now = Date.now();
  let changed = false;

  for (const [id, v] of state.vehicles.entries()) {
    if (v.connected && v.lastSeen) {
      const elapsed = now - new Date(v.lastSeen).getTime();
      if (elapsed > timeoutMs) {
        v.connected = false;
        changed = true;
      }
    }
  }

  return changed;
}

export function removeVehicle(vehicleId) {
  state.vehicles.delete(vehicleId);
}

export function updateSensor(sensor) {
  if (!sensor?.sensorId) {
    throw new Error("sensorId is required");
  }
  state.sensors.set(sensor.sensorId, { ...sensor });
}

export function updateDetection(detection) {
  if (!detection?.detectionId) {
    throw new Error("detectionId is required");
  }
  state.detections.set(detection.detectionId, { ...detection });
}

export function updateMission(mission) {
  if (!mission?.missionId) {
    throw new Error("missionId is required");
  }
  state.missions.set(mission.missionId, { ...mission });
}
