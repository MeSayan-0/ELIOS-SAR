import { getVehicleByType } from "./gcsState.js";

function normalizeBoundingBox(box) {
  if (!box) return null;

  if (Array.isArray(box) && box.length >= 4) {
    return {
      x1: Number(box[0]),
      y1: Number(box[1]),
      x2: Number(box[2]),
      y2: Number(box[3])
    };
  }

  if (typeof box === "object") {
    if (
      box.x1 !== undefined &&
      box.y1 !== undefined &&
      box.x2 !== undefined &&
      box.y2 !== undefined
    ) {
      return {
        x1: Number(box.x1),
        y1: Number(box.y1),
        x2: Number(box.x2),
        y2: Number(box.y2)
      };
    }

    if (
      box.xmin !== undefined &&
      box.ymin !== undefined &&
      box.xmax !== undefined &&
      box.ymax !== undefined
    ) {
      return {
        x1: Number(box.xmin),
        y1: Number(box.ymin),
        x2: Number(box.xmax),
        y2: Number(box.ymax)
      };
    }

    if (
      box.x !== undefined &&
      box.y !== undefined &&
      box.width !== undefined &&
      box.height !== undefined
    ) {
      return {
        x1: Number(box.x),
        y1: Number(box.y),
        x2: Number(box.x) + Number(box.width),
        y2: Number(box.y) + Number(box.height)
      };
    }
  }

  return null;
}

function normalizeDetection(detection, index = 0) {
  const bbox =
    detection.bbox ||
    detection.box ||
    detection.xyxy ||
    detection.coordinates;

  const label =
    detection.label ||
    detection.class_name ||
    detection.class ||
    detection.name ||
    "unknown";

  let severity =
    detection.severity ||
    detection.risk ||
    null;

  const l = String(label).toLowerCase().trim();

  const canonicalLabel =
    (l === "civilian" ||
     l === "human" ||
     l === "rescuer" ||
     l === "person")
      ? "person"
      : l;

  if (!severity) {
    if (l === "fire" || l === "collapse" || l === "methane") {
      severity = "critical";
    } else if (
      l === "person" ||
      l === "human" ||
      l === "civilian" ||
      l === "rescuer"
    ) {
      severity = "high";
    } else {
      severity = "normal";
    }
  }

  return {
    id:
      detection.id ||
      detection.track_id ||
      `det-${Date.now()}-${index}`,

    label: canonicalLabel,

    confidence: Number(
      detection.confidence ??
      detection.score ??
      detection.probability ??
      0
    ),

    bbox: normalizeBoundingBox(bbox),

    track_id:
      detection.track_id ??
      detection.trackId ??
      null,

    severity
  };
}

export function normalizeRisk(risk) {
  if (!risk) return null;

  if (typeof risk === "string") {
    const level = risk.toUpperCase();
    const scores = { LOW: 20, MEDIUM: 50, HIGH: 80, CRITICAL: 100 };
    return {
      level,
      score: scores[level] ?? 50,
      reasons: []
    };
  }

  if (typeof risk === "object") {
    const level = String(
      risk.level ||
      risk.risk_level ||
      risk.overall_risk ||
      "UNKNOWN"
    ).toUpperCase();

    const score = Number(
      risk.score ??
      risk.priority_score ??
      risk.risk_score ??
      (level === "CRITICAL" ? 100 : level === "HIGH" ? 80 : level === "MEDIUM" ? 50 : 20)
    );

    const reasons = Array.isArray(risk.reasons)
      ? risk.reasons.map(String)
      : risk.reason
      ? [String(risk.reason)]
      : risk.explanation
      ? [String(risk.explanation)]
      : [];

    return {
      level,
      score,
      reasons
    };
  }

  return null;
}

export function normalizeAIMessage(message) {
  const detections = Array.isArray(message.detections)
    ? message.detections
    : [];

  return {
    type: "ai_event",

    source:
      message.source ||
      message.drone_id ||
      message.vehicle_id ||
      getVehicleByType("drone")?.vehicleId ||
      "DRONE-01",

    timestamp:
      message.timestamp ||
      new Date().toISOString(),

    frame_id:
      message.frame_id ??
      message.frameId ??
      null,

    inference_time_ms:
      Number(message.inference_time_ms ?? 0),

    inference_fps:
      Number(message.inference_fps ?? 0),

    detections: detections.map(normalizeDetection),

    risk: normalizeRisk(message.risk || message.risk_assessment),

    raw: message
  };
}
