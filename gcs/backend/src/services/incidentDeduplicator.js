const activeIncidents = new Map();

const INCIDENT_COOLDOWN_MS = 10000;

export function shouldCreateIncident({
  source,
  label,
  bbox
}) {
  const key = `${source}:${label}`;

  const now = Date.now();

  const previous = activeIncidents.get(key);

  if (
    previous &&
    now - previous < INCIDENT_COOLDOWN_MS
  ) {
    return false;
  }

  activeIncidents.set(key, now);

  return true;
}

export function clearIncidentCache() {
  activeIncidents.clear();
}
