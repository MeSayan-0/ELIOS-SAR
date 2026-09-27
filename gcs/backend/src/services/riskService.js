/**
 * Risk Assessment Service for ELIOS-SAR
 * Computes situational hazard risk score and level from AI detection metadata.
 */

export function calculateRisk(event) {
  const detections = Array.isArray(event?.detections)
    ? event.detections
    : [];

  let score = 0;
  const reasons = [];

  for (const detection of detections) {
    const label = String(
      detection.label ??
      detection.class_name ??
      detection.class ??
      ""
    ).toLowerCase();

    const severity = String(
      detection.severity ??
      "low"
    ).toLowerCase();

    if (
      label === "person" ||
      label === "civilian" ||
      label === "human" ||
      label === "rescuer"
    ) {
      score += 35;
      reasons.push("PERSON DETECTED");
    }

    if (
      label.includes("fire") ||
      label.includes("flame")
    ) {
      score += 35;
      reasons.push("FIRE DETECTED");
    }

    if (
      label.includes("gas") ||
      label.includes("leak")
    ) {
      if (severity === "critical") {
        score += 50;
      } else if (severity === "high") {
        score += 30;
      } else {
        score += 10;
      }

      reasons.push("GAS HAZARD");
    }

    if (
      label.includes("obstruction") ||
      label.includes("debris")
    ) {
      if (severity === "critical") {
        score += 40;
      } else if (severity === "high") {
        score += 25;
      } else {
        score += 10;
      }

      reasons.push("OBSTRUCTION");
    }

    if (
      label.includes("flood") ||
      label.includes("water")
    ) {
      score += 25;
      reasons.push("WATER/FLOOD");
    }
  }

  let level = "LOW";

  if (score >= 80) {
    level = "CRITICAL";
  } else if (score >= 50) {
    level = "HIGH";
  } else if (score >= 20) {
    level = "MEDIUM";
  }

  return {
    level,
    score,
    reason: reasons.length
      ? reasons.join(" • ")
      : "NO ACTIVE HAZARD",
  };
}

export default {
  calculateRisk,
};
