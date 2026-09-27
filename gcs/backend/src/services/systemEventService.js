import mongoose from "mongoose";
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

  let eventData;

  if (mongoose.connection.readyState === 1) {
    try {
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
      eventData = record.toObject();
    } catch (_) {
      eventData = { timestamp, level, source, eventType, vehicleId, missionId, message, metadata };
    }
  } else {
    eventData = { timestamp, level, source, eventType, vehicleId, missionId, message, metadata };
  }

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
  if (mongoose.connection.readyState !== 1) {
    return [];
  }

  return SystemEvent.find()
    .sort({ timestamp: -1 })
    .limit(limit)
    .lean();
}
