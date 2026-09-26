export const EMPTY_GCS_STATE = {
  system: {
    status: "UNKNOWN",
  },

  vehicles: {},

  telemetry: [],

  detections: {},

  persons: [],

  sensors: {},

  hazards: {},

  risk_events: {},

  mission_events: [],

  missions: {},

  map: null,

  commands: {},

  liveImages: {},

  ai: null,
};

export function normalizeGCSState(input) {
  if (!input || typeof input !== "object") {
    return EMPTY_GCS_STATE;
  }

  const payload =
    input.type === "state" && input.state && typeof input.state === "object"
      ? input.state
      : input.state && typeof input.state === "object" && !input.sensors && !input.vehicles
      ? input.state
      : input;

  return {
    system: {
      ...EMPTY_GCS_STATE.system,
      ...(payload.system ?? {}),
    },

    vehicles:
      payload.vehicles &&
      typeof payload.vehicles === "object"
        ? payload.vehicles
        : {},

    telemetry: Array.isArray(payload.telemetry)
      ? payload.telemetry
      : [],

    detections:
      payload.detections &&
      typeof payload.detections === "object"
        ? payload.detections
        : {},

    persons: Array.isArray(payload.persons)
      ? payload.persons
      : [],

    sensors:
      payload.sensors &&
      typeof payload.sensors === "object"
        ? payload.sensors
        : {},

    hazards:
      payload.hazards &&
      typeof payload.hazards === "object"
        ? payload.hazards
        : {},

    risk_events:
      payload.risk_events &&
      typeof payload.risk_events === "object"
        ? payload.risk_events
        : {},

    mission_events: Array.isArray(
      payload.mission_events
    )
      ? payload.mission_events
      : [],

    missions:
      payload.missions &&
      typeof payload.missions === "object"
        ? payload.missions
        : {},

    map: payload.map ?? null,

    commands:
      payload.commands &&
      typeof payload.commands === "object"
        ? payload.commands
        : {},

    liveImages:
      payload.liveImages &&
      typeof payload.liveImages === "object"
        ? payload.liveImages
        : {},

    ai: payload.ai ?? null,
  };
}
