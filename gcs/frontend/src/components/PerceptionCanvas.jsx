import { useEffect, useRef } from "react";

export default function PerceptionCanvas({
  image,
  detections = [],
  perception = null,
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!image || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    // Step 14 — Do NOT draw boxes if AI is stale
    const aiAge = perception?.ai_age_ms;
    const aiFresh =
      typeof aiAge === "number"
        ? aiAge <= 1000
        : true;

    const activeDetections = aiFresh ? detections : [];

    const img = new Image();

    img.onload = () => {
      const imgWidth = img.naturalWidth || img.width || 640;
      const imgHeight = img.naturalHeight || img.height || 480;

      canvas.width = imgWidth;
      canvas.height = imgHeight;

      context.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
      );

      context.drawImage(
        img,
        0,
        0,
        canvas.width,
        canvas.height
      );

      for (const detection of activeDetections) {
        const box = detection.bbox || detection.box || detection.xyxy;
        if (!box) continue;

        let x1 = Number(box.x1 !== undefined ? box.x1 : box[0]);
        let y1 = Number(box.y1 !== undefined ? box.y1 : box[1]);
        let x2 = Number(box.x2 !== undefined ? box.x2 : box[2]);
        let y2 = Number(box.y2 !== undefined ? box.y2 : box[3]);

        // Normalize if coordinates are proportional (0.0 to 1.0)
        if (x1 <= 1.0 && y1 <= 1.0 && x2 <= 1.0 && y2 <= 1.0 && (x2 - x1) < 0.99) {
          x1 *= imgWidth;
          y1 *= imgHeight;
          x2 *= imgWidth;
          y2 *= imgHeight;
        }

        const width = x2 - x1;
        const height = y2 - y1;

        if (width <= 0 || height <= 0) continue;

        // Step 12 — Accept label or class_name
        const label =
          detection.label ??
          detection.class_name ??
          detection.class ??
          "unknown";

        const confidence =
          Number(detection.confidence ?? detection.score ?? 0);

        const trackId =
          detection.track_id ??
          detection.trackId ??
          null;

        const severity = String(detection.severity || "").toLowerCase();
        const labelLower = String(label).toLowerCase();

        let strokeColor = "#00ff66"; // Default person/survivor neon green
        let badgeBg = "#00ff66";
        let badgeText = "#000000";

        if (
          labelLower.includes("fire") ||
          labelLower.includes("smoke") ||
          labelLower.includes("collapse") ||
          labelLower.includes("gas") ||
          severity === "critical"
        ) {
          strokeColor = "#ff3333"; // Critical hazard red
          badgeBg = "#ff3333";
          badgeText = "#ffffff";
        } else if (
          labelLower.includes("hazard") ||
          labelLower.includes("obstacle") ||
          labelLower.includes("boulder") ||
          severity === "high"
        ) {
          strokeColor = "#ffaa00"; // Warning amber
          badgeBg = "#ffaa00";
          badgeText = "#000000";
        } else if (!labelLower.includes("person") && !labelLower.includes("human") && !labelLower.includes("civilian")) {
          strokeColor = "#00d4ff"; // Generic object cyan
          badgeBg = "#00d4ff";
          badgeText = "#000000";
        }

        // Bounding Box
        context.strokeStyle = strokeColor;
        context.lineWidth = 3;
        context.strokeRect(x1, y1, width, height);

        // Corner accents
        const cornerLen = Math.min(16, width / 4, height / 4);
        context.lineWidth = 5;
        context.beginPath();
        // Top-left
        context.moveTo(x1, y1 + cornerLen);
        context.lineTo(x1, y1);
        context.lineTo(x1 + cornerLen, y1);
        // Top-right
        context.moveTo(x2 - cornerLen, y1);
        context.lineTo(x2, y1);
        context.lineTo(x2, y1 + cornerLen);
        // Bottom-left
        context.moveTo(x1, y2 - cornerLen);
        context.lineTo(x1, y2);
        context.lineTo(x1 + cornerLen, y2);
        // Bottom-right
        context.moveTo(x2 - cornerLen, y2);
        context.lineTo(x2, y2);
        context.lineTo(x2, y2 - cornerLen);
        context.stroke();

        // Step 13 — Draw label above the box
        const confPercent = Math.round(confidence * 100);
        const trackTag = trackId != null ? ` #${trackId}` : "";
        const labelText = `${String(label).toUpperCase()} ${confPercent}%${trackTag}`;

        context.font = "bold 15px monospace";
        const textWidth = context.measureText(labelText).width;
        const badgeHeight = 22;
        const badgeY = Math.max(0, y1 - badgeHeight);

        context.fillStyle = badgeBg;
        context.fillRect(x1, badgeY, textWidth + 10, badgeHeight);

        context.fillStyle = badgeText;
        context.fillText(labelText, x1 + 4, Math.max(badgeY + 16, 14));
      }
    };

    img.src = image;
  }, [image, detections, perception]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: "100%",
        height: "auto",
        display: "block",
      }}
    />
  );
}
