import { getVehicleByType } from "./gcsState.js";

const latestVideoFrames = new Map();
const latestAIEvents = new Map();

const MAX_VIDEO_HISTORY = 60;
const videoHistory = new Map();

const MAX_TIMESTAMP_DIFFERENCE_MS = 1500;
const AI_FRESHNESS_TTL_MS = 1000;

const SOURCE_ALIASES = {
  "elios-01": "DRONE-01",
  "elios": "DRONE-01",
  "drone-01": "DRONE-01",
  "drone-01-rgb": "DRONE-01",
  "drone-rgb": "DRONE-01",
  "drone": "DRONE-01",
  "rover-01": "ROVER-01",
  "rover-01-rgb": "ROVER-01",
  "rover-rgb": "ROVER-01",
  "rover": "ROVER-01",
};

export function canonicalSource(source) {
  if (!source) return "DRONE-01";
  const normalized = String(source).trim().toLowerCase();
  return SOURCE_ALIASES[normalized] || String(source).trim().toUpperCase();
}

export const canonicalizeSource = canonicalSource;

function safeTimestamp(value) {
  if (typeof value === "number") {
    return Number.isFinite(value)
      ? value
      : Date.now();
  }

  const parsed = Date.parse(value);

  return Number.isFinite(parsed)
    ? parsed
    : Date.now();
}

export function storeVideoFrame(source, frame) {
  const key = canonicalSource(source);
  if (!key) return;

  latestVideoFrames.set(key, frame);

  if (!videoHistory.has(key)) {
    videoHistory.set(key, []);
  }

  const history = videoHistory.get(key);
  history.push(frame);

  while (history.length > MAX_VIDEO_HISTORY) {
    history.shift();
  }
}

export function getEventTimestampMs(event) {
  if (!event) return null;

  if (typeof event.timestamp_ms === "number") {
    return event.timestamp_ms;
  }

  if (typeof event.timestamp === "number") {
    return event.timestamp;
  }

  if (typeof event.timestamp === "string") {
    const parsed = Date.parse(event.timestamp);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }

  return null;
}

export function isAIEventFresh(event, now = Date.now()) {
  const timestamp = getEventTimestampMs(event);
  if (timestamp === null) {
    return false;
  }

  const age = now - timestamp;
  return age >= 0 && age <= AI_FRESHNESS_TTL_MS;
}

export function registerVideoFrame({
  source = "drone-rgb",
  image,
  timestamp,
  timestamp_ms,
  frame_id = null,
}) {
  const canonical = canonicalSource(source);

  const frame = {
    source,
    canonical,
    image,
    timestamp,
    timestamp_ms:
      timestamp_ms ??
      safeTimestamp(timestamp),
    frame_id,
    received_at: Date.now(),
  };

  storeVideoFrame(source, frame);
  storeVideoFrame(canonical, frame);

  return synchronize(canonical);
}

export function registerAIEvent(event) {
  const key = canonicalSource(
    event.drone_id ||
    event.source ||
    getVehicleByType("drone")?.vehicleId ||
    "DRONE-01"
  );

  const normalized = {
    ...event,
    source: key,
    canonical: key,
    timestamp_ms:
      safeTimestamp(event.timestamp),
    received_at: Date.now(),
  };

  if (key) {
    latestAIEvents.set(key, normalized);
    if (event.source && event.source !== key) {
      latestAIEvents.set(event.source, normalized);
    }
  }

  return synchronize(key);
}

export function getLivePerception(source) {
  const key = canonicalSource(source);
  if (!key) {
    return null;
  }

  const video = latestVideoFrames.get(key) || latestVideoFrames.get("drone-rgb");
  const ai = latestAIEvents.get(key) || latestAIEvents.get("DRONE-01");

  if (!video || !ai) {
    return null;
  }

  if (!isAIEventFresh(ai)) {
    return null;
  }

  return {
    type: "perception_frame",
    synchronized: true,
    mode: "live",
    source: key,
    vehicle_id: key,
    stream_id: `${key.toLowerCase()}-rgb`,
    video,
    image: video.image,
    ai,
    frame_id: video.frame_id ?? null,
    ai_frame_id: ai.frame_id ?? null,
    detections: Array.isArray(ai.detections)
      ? ai.detections
      : [],
    risk: ai.risk || null,
    inference_time_ms: ai.inference_time_ms || 0,
    inference_fps: ai.inference_fps || 0,
    timestamp: video.timestamp,
    ai_timestamp: getEventTimestampMs(ai),
    ai_age_ms: Date.now() - (getEventTimestampMs(ai) || Date.now()),
  };
}

export function synchronize(key) {
  const canonical = canonicalSource(key);

  const video =
    latestVideoFrames.get(canonical) ||
    latestVideoFrames.get(key) ||
    latestVideoFrames.get("drone-rgb");

  const ai =
    latestAIEvents.get(canonical) ||
    latestAIEvents.get(key) ||
    latestAIEvents.get("DRONE-01");

  if (!video || !ai) {
    return null;
  }

  let synchronized = false;
  let difference_ms = null;

  /*
   * 1. Frame ID is the primary synchronization key.
   * Also check videoHistory for matching historical frame!
   */
  if (
    video.frame_id !== null &&
    ai.frame_id !== null
  ) {
    if (String(video.frame_id) === String(ai.frame_id)) {
      synchronized = true;
    } else {
      const history = videoHistory.get(canonical) || [];
      const matchingVideo = history.find(
        (f) => String(f.frame_id) === String(ai.frame_id)
      );
      if (matchingVideo) {
        return {
          type: "perception_frame",
          source: canonical,
          vehicle_id: canonical,
          stream_id: `${canonical.toLowerCase()}-rgb`,
          frame_id: ai.frame_id,
          timestamp: matchingVideo.timestamp,
          synchronized: true,
          timestamp_difference_ms: 0,
          image: matchingVideo.image,
          detections: ai.detections || [],
          risk: ai.risk || null,
          inference_time_ms: ai.inference_time_ms || 0,
          inference_fps: ai.inference_fps || 0,
          ai_timestamp: ai.timestamp,
          video_timestamp: matchingVideo.timestamp,
        };
      }
    }
  }

  /*
   * 2. Timestamp is only the fallback.
   */
  else {
    difference_ms =
      Math.abs(
        video.timestamp_ms -
        ai.timestamp_ms
      );

    synchronized =
      difference_ms <=
      MAX_TIMESTAMP_DIFFERENCE_MS;
  }

  return {
    type: "perception_frame",
    source: canonical,
    vehicle_id: canonical,
    stream_id: `${canonical.toLowerCase()}-rgb`,
    frame_id:
      ai.frame_id ??
      video.frame_id ??
      null,
    timestamp: video.timestamp,
    synchronized,
    timestamp_difference_ms:
      difference_ms,
    image:
      video.image,
    detections:
      ai.detections || [],
    risk:
      ai.risk || null,
    inference_time_ms:
      ai.inference_time_ms || 0,
    inference_fps:
      ai.inference_fps || 0,
    ai_timestamp:
      ai.timestamp,
    video_timestamp:
      video.timestamp,
  };
}

export function getSynchronizationState() {
  return {
    videos:
      latestVideoFrames.size,
    ai_sources:
      latestAIEvents.size,
  };
}
