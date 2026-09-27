const streams = new Map();

export function markStreamActivity(name, metadata = {}) {
  streams.set(name, {
    name,
    last_activity: new Date().toISOString(),
    last_activity_ms: Date.now(),
    status: "online",
    ...metadata
  });
}

export function getStreamHealth() {
  const now = Date.now();
  const result = {};

  for (const [name, stream] of streams.entries()) {
    const age = now - stream.last_activity_ms;

    result[name] = {
      ...stream,
      age_ms: age,
      status: age > 5000 ? "stale" : "online"
    };
  }

  return result;
}
