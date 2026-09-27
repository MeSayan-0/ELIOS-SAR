export function getVehicles(state) {
  return Object.values(
    state?.vehicles ?? {}
  );
}

export function getDrones(state) {
  return getVehicles(state).filter(
    (vehicle) =>
      (
        vehicle.vehicleType ??
        vehicle.vehicle_type ??
        ""
      ).toLowerCase() === "drone"
  );
}

export function getRovers(state) {
  return getVehicles(state).filter(
    (vehicle) =>
      (
        vehicle.vehicleType ??
        vehicle.vehicle_type ??
        ""
      ).toLowerCase() === "rover"
  );
}

export function getDetections(state) {
  return Object.values(
    state?.detections ?? {}
  );
}

export function getSensors(state) {
  return Object.values(
    state?.sensors ?? {}
  );
}

export function getHazards(state) {
  return Object.values(
    state?.hazards ?? {}
  );
}

export function getRiskEvents(state) {
  return Object.values(
    state?.risk_events ?? {}
  );
}

export function getMissions(state) {
  return Object.values(
    state?.missions ?? {}
  );
}

export function getActiveMissions(state) {
  return getMissions(state).filter(
    (mission) => {
      const status =
        mission.status ??
        mission.state ??
        "";

      return [
        "ACTIVE",
        "IN_PROGRESS",
        "CREATED",
      ].includes(
        String(status).toUpperCase()
      );
    }
  );
}
