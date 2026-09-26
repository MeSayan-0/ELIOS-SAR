export function normalizeBatteryStatus(message) {
  if (!message) {
    return null;
  }

  return {
    battery:
      typeof message.remaining === "number"
        ? Math.round(message.remaining * 100)
        : null,

    voltage:
      typeof message.voltage_v === "number"
        ? message.voltage_v
        : null,

    current:
      typeof message.current_a === "number"
        ? message.current_a
        : null,
  };
}

export function normalizeVehicleStatus(message) {
  if (!message) {
    return null;
  }

  return {
    navState:
      typeof message.nav_state === "number"
        ? message.nav_state
        : null,

    armingState:
      typeof message.arming_state === "number"
        ? message.arming_state
        : null,

       armed: message.arming_state === 2,

     failsafe:
      typeof message.failsafe === "boolean"
        ? message.failsafe
        : null,
  };
}

export function normalizeGlobalPosition(message) {
  if (!message) {
    return null;
  }

  return {
    latitude:
      typeof message.lat === "number"
        ? message.lat
        : null,

    longitude:
      typeof message.lon === "number"
        ? message.lon
        : null,

    altitude:
      typeof message.alt === "number"
        ? message.alt
        : null,

    relativeAltitude:
      typeof message.altitude_msl === "number"
        ? message.altitude_msl
        : null,
  };
}

export function normalizeLocalPosition(message) {
  if (!message) {
    return null;
  }

  return {
    x:
      typeof message.x === "number"
        ? message.x
        : null,

    y:
      typeof message.y === "number"
        ? message.y
        : null,

    z:
      typeof message.z === "number"
        ? message.z
        : null,

    vx:
      typeof message.vx === "number"
        ? message.vx
        : null,

    vy:
      typeof message.vy === "number"
        ? message.vy
        : null,

    vz:
      typeof message.vz === "number"
        ? message.vz
        : null,
  };
}

export function normalizeAttitude(message) {
  if (!message) {
    return null;
  }

  return {
    q: Array.isArray(message.q)
      ? message.q
      : [],
  };
}
