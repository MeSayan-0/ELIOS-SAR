import {
  shouldCreateIncident
} from "./incidentDeduplicator.js";

export async function processPersistentDetections({
  source,
  detections,
  createIncident
}) {
  for (const detection of detections) {
    const isCritical =
      detection.label === "fire" ||
      detection.label === "smoke" ||
      detection.label === "collapse" ||
      detection.label === "person";

    if (!isCritical) continue;

    const allowed = shouldCreateIncident({
      source,
      label: detection.label,
      bbox: detection.bbox
    });

    if (!allowed) continue;

    if (typeof createIncident === "function") {
      await createIncident({
        source,
        label: detection.label,
        confidence: detection.confidence,
        bbox: detection.bbox,
        timestamp: new Date()
      });
    }
  }
}
