import { SystemEvent } from "../models/SystemEvent.js";
import { broadcast } from "../websocket/manager.js";

export async function createSystemEvent({
  level = "INFO",
  source,
  eventType,
  vehicleId = null,
  missionId = null,
  message,
  metadata = {},
  timestamp = new Date(),
}) {
  if (!source) {
    throw new Error("source is required");
  }

  if (!eventType) {
    throw new Error("eventType is required");
  }

  if (!message) {
    throw new Error("message is required");
  }

  const record = await SystemEvent.create({
    timestamp,
    level,
    source,
    eventType,
    vehicleId,
    missionId,
    message,
    metadata,
  });

  const eventData = record.toObject();

  try {
    broadcast({
      type: "system_event",
      event: eventData,
    });
  } catch (err) {
    // broadcast non-blocking
  }

  return eventData;
}

export async function getSystemEvents(limit = 100) {
  return SystemEvent.find()
    .sort({ timestamp: -1 })
    .limit(limit)
    .lean();
}
