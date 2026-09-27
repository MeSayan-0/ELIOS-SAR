import {
  normalizeAIMessage
} from "./detectionNormalizer.js";

import {
  calculateRisk
} from "./riskService.js";

import {
  registerVideoFrame,
  registerAIEvent,
  getLivePerception
} from "./frameSynchronizer.js";

import {
  markStreamActivity
} from "./streamHealthService.js";

import {
  broadcast
} from "../websocket/manager.js";

export function processVideoFrame({
  source = "drone-rgb",
  image,
  timestamp = new Date().toISOString(),
  timestamp_ms = Date.parse(timestamp),
  frame_id = null
}) {
  markStreamActivity("video", {
    source
  });

  const synchronized =
    registerVideoFrame({
      source,
      image,
      timestamp,
      timestamp_ms,
      frame_id
    });

  /*
   * 1. Video remains independently available.
   */
  broadcast({
    type: "video_frame",
    source,
    image,
    timestamp,
    frame_id
  });

  /*
   * 2. Live perception broadcast (latest video + fresh AI).
   */
  const livePerception = getLivePerception(source);
  if (livePerception) {
    broadcast(livePerception);
  } else if (
    synchronized &&
    synchronized.synchronized
  ) {
    broadcast(synchronized);
  }

  return synchronized;
}

export function processAIEvent(message) {
  const normalized =
    normalizeAIMessage(message);

  const risk = normalized.risk || calculateRisk(normalized);
  const enriched = {
    ...normalized,
    risk,
  };

  markStreamActivity("ai", {
    source: enriched.source,
    detections: enriched.detections.length
  });

  const synchronized =
    registerAIEvent(enriched);

  /*
   * 1. AI remains independently available (broadcast enriched with risk).
   */
  broadcast(enriched);

  /*
   * 2. Live perception broadcast (fresh AI + latest video).
   */
  const sourceKey = message.drone_id || message.source || enriched.source;
  const livePerception = getLivePerception(sourceKey);

  if (livePerception) {
    broadcast(livePerception);
  } else if (
    synchronized &&
    synchronized.synchronized
  ) {
    broadcast(synchronized);
  }

  return synchronized;
}
