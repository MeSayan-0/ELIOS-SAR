import { useEffect, useRef } from "react";

const UNKNOWN = -1;
const FREE = 0;
const OCCUPIED = 100;

function normalizeVehicles(vehicles) {
  if (!vehicles) return [];

  if (Array.isArray(vehicles)) {
    return vehicles;
  }

  return Object.entries(vehicles).map(([vehicleId, vehicle]) => ({
    ...vehicle,
    vehicleId:
      vehicle?.vehicleId ??
      vehicle?.vehicle_id ??
      vehicleId,
  }));
}

function getPosition(vehicle) {
  const position =
    vehicle?.position ??
    vehicle?.telemetry?.position ??
    vehicle?.data?.position ??
    vehicle?.localPosition ??
    vehicle?.local_position ??
    vehicle?.pose?.position;

  if (!position) return null;

  const x = Number(position.x);
  const y = Number(position.y);

  if (!Number.isFinite(x) || !Number.isFinite(y)) {
    return null;
  }

  return { x, y };
}

function drawTrail(
  ctx,
  vehicle,
  mapData,
  width,
  height,
  trail
) {
  if (
    !Array.isArray(trail) ||
    trail.length < 2 ||
    !mapData?.origin
  ) {
    return;
  }

  const resolution = Number(
    mapData.resolution
  );

  if (!Number.isFinite(resolution) || resolution <= 0) {
    return;
  }

  ctx.save();

  ctx.beginPath();

  trail.forEach((point, index) => {
    const gridX =
      (point.x - Number(mapData.origin.x || 0)) /
      resolution;

    const gridY =
      (point.y - Number(mapData.origin.y || 0)) /
      resolution;

    const canvasY = height - gridY;

    if (index === 0) {
      ctx.moveTo(gridX, canvasY);
    } else {
      ctx.lineTo(gridX, canvasY);
    }
  });

  const vehicleType =
    String(
      vehicle?.vehicleType ??
      vehicle?.vehicle_type ??
      vehicle?.type ??
      ""
    ).toLowerCase();

  ctx.strokeStyle = vehicleType === "rover" ? "#45d0c4" : "#00e5ff";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  ctx.restore();
}

function drawVehicle(
  ctx,
  vehicle,
  mapData,
  width,
  height
) {
  const position = getPosition(vehicle);

  if (!position || !mapData?.origin) {
    return;
  }

  const resolution = Number(mapData.resolution);

  if (!Number.isFinite(resolution) || resolution <= 0) {
    return;
  }

  const gridX =
    (position.x - Number(mapData.origin.x || 0)) /
    resolution;

  const gridY =
    (position.y - Number(mapData.origin.y || 0)) /
    resolution;

  const canvasY = height - gridY;

  if (
    gridX < -10 ||
    gridX > width + 10 ||
    canvasY < -10 ||
    canvasY > height + 10
  ) {
    return;
  }

  const vehicleType =
    String(
      vehicle?.vehicleType ??
      vehicle?.vehicle_type ??
      vehicle?.type ??
      ""
    ).toLowerCase();

  const isRover = vehicleType === "rover";

  ctx.save();

  ctx.beginPath();
  ctx.arc(
    gridX,
    canvasY,
    isRover ? 4 : 5,
    0,
    Math.PI * 2
  );

  ctx.fillStyle = isRover
    ? "#45d0c4"
    : "#00e5ff";

  ctx.fill();

  ctx.lineWidth = 1;
  ctx.strokeStyle = "#ffffff";
  ctx.stroke();

  ctx.font = "10px monospace";
  ctx.fillStyle = "#ffffff";

  const vehicleId =
    vehicle?.vehicleId ??
    vehicle?.vehicle_id ??
    "UNKNOWN";

  ctx.fillText(
    String(vehicleId),
    gridX + 7,
    canvasY - 7
  );

  ctx.restore();
}

function drawDetection(
  ctx,
  detection,
  mapData,
  width,
  height
) {
  const position =
    detection?.position ??
    detection?.data?.position;

  if (!position || !mapData?.origin) {
    return;
  }

  const resolution = Number(mapData.resolution);

  if (!Number.isFinite(resolution) || resolution <= 0) {
    return;
  }

  const x = Number(position.x);
  const y = Number(position.y);

  if (!Number.isFinite(x) || !Number.isFinite(y)) {
    return;
  }

  const gridX =
    (x - Number(mapData.origin.x || 0)) /
    resolution;

  const gridY =
    (y - Number(mapData.origin.y || 0)) /
    resolution;

  const canvasY = height - gridY;

  ctx.save();

  ctx.beginPath();
  ctx.arc(
    gridX,
    canvasY,
    4,
    0,
    Math.PI * 2
  );

  ctx.lineWidth = 2;
  ctx.strokeStyle = "#ffcc00";
  ctx.stroke();

  ctx.font = "10px monospace";
  ctx.fillStyle = "#ffcc00";

  const confidence =
    Number(
      detection?.confidence ??
      detection?.data?.confidence
    );

  const label =
    detection?.label ??
    detection?.data?.label ??
    "PERSON";

  const text = Number.isFinite(confidence)
    ? `${label} ${Math.round(confidence * 100)}%`
    : label;

  ctx.fillText(
    text,
    gridX + 7,
    canvasY + 4
  );

  ctx.restore();
}

function drawHazard(
  ctx,
  hazard,
  mapData,
  width,
  height
) {
  const position =
    hazard?.position ??
    hazard?.data?.position;

  if (!position || !mapData?.origin) {
    return;
  }

  const resolution = Number(mapData.resolution);

  if (!Number.isFinite(resolution) || resolution <= 0) {
    return;
  }

  const x = Number(position.x);
  const y = Number(position.y);

  if (!Number.isFinite(x) || !Number.isFinite(y)) {
    return;
  }

  const gridX =
    (x - Number(mapData.origin.x || 0)) /
    resolution;

  const gridY =
    (y - Number(mapData.origin.y || 0)) /
    resolution;

  const canvasY = height - gridY;

  ctx.save();

  ctx.beginPath();

  ctx.moveTo(gridX, canvasY - 6);
  ctx.lineTo(gridX + 6, canvasY + 5);
  ctx.lineTo(gridX - 6, canvasY + 5);
  ctx.closePath();

  ctx.fillStyle = "#ff3366";
  ctx.fill();

  ctx.font = "10px monospace";
  ctx.fillStyle = "#ff3366";

  const hazardType =
    hazard?.hazard_type ??
    hazard?.hazardType ??
    hazard?.data?.hazard_type ??
    "HAZARD";

  ctx.fillText(
    String(hazardType),
    gridX + 8,
    canvasY + 4
  );

  ctx.restore();
}

function drawRiskZone(
  ctx,
  risk,
  mapData,
  width,
  height
) {
  const position =
    risk?.position ??
    risk?.data?.position;

  if (!position || !mapData?.origin) {
    return;
  }

  const resolution = Number(mapData.resolution);

  if (!Number.isFinite(resolution) || resolution <= 0) {
    return;
  }

  const originX = Number(mapData.origin.x || 0);
  const originY = Number(mapData.origin.y || 0);

  const gridX =
    (Number(position.x) - originX) /
    resolution;

  const gridY =
    (Number(position.y) - originY) /
    resolution;

  const canvasY = height - gridY;

  const score = Number(risk?.score ?? risk?.data?.score ?? 0);

  const radius =
    score >= 80 ? 25 :
    score >= 60 ? 20 :
    15;

  ctx.save();

  ctx.beginPath();
  ctx.arc(gridX, canvasY, radius, 0, Math.PI * 2);

  ctx.setLineDash([4, 3]);

  ctx.strokeStyle =
    score >= 80
      ? "#ff3333"
      : "#ffaa00";

  ctx.lineWidth = 1.5;

  ctx.stroke();

  ctx.font = "9px monospace";
  ctx.fillStyle = score >= 80 ? "#ff3333" : "#ffaa00";
  const level = String(risk?.risk_level ?? risk?.data?.risk_level ?? "RISK");
  ctx.fillText(`${level} (${score})`, gridX + radius + 4, canvasY + 3);

  ctx.restore();
}

export default function LiveMap({
  mapData,
  vehicles = {},
  detections = [],
  hazards = [],
  risks = [],
}) {
  const canvasRef = useRef(null);
  const trailRef = useRef({});

  useEffect(() => {
    const canvas = canvasRef.current;

    if (!canvas || !mapData) {
      return;
    }

    const ctx = canvas.getContext("2d");

    if (!ctx) {
      return;
    }

    const width = Number(mapData.width);
    const height = Number(mapData.height);

    if (
      !Number.isFinite(width) ||
      !Number.isFinite(height) ||
      width <= 0 ||
      height <= 0
    ) {
      return;
    }

    const cells =
      mapData.cells ??
      mapData.grid ??
      [];

    canvas.width = width;
    canvas.height = height;

    const image =
      ctx.createImageData(
        width,
        height
      );

    for (
      let y = 0;
      y < height;
      y += 1
    ) {
      for (
        let x = 0;
        x < width;
        x += 1
      ) {
        const index =
          y * width + x;

        const value =
          Array.isArray(cells[y])
            ? cells[y]?.[x] ?? UNKNOWN
            : cells[index] ?? UNKNOWN;

        const pixel =
          index * 4;

        if (value === OCCUPIED) {
          image.data[pixel] = 20;
          image.data[pixel + 1] = 22;
          image.data[pixel + 2] = 24;
          image.data[pixel + 3] = 255;
        } else if (value === FREE) {
          image.data[pixel] = 175;
          image.data[pixel + 1] = 180;
          image.data[pixel + 2] = 184;
          image.data[pixel + 3] = 255;
        } else {
          image.data[pixel] = 65;
          image.data[pixel + 1] = 69;
          image.data[pixel + 2] = 73;
          image.data[pixel + 3] = 255;
        }
      }
    }

    ctx.putImageData(
      image,
      0,
      0
    );

    const vehicleList =
      normalizeVehicles(
        vehicles
      );

    vehicleList.forEach((vehicle) => {
      const vehicleId =
        vehicle?.vehicleId ??
        vehicle?.vehicle_id;

      const position = getPosition(vehicle);

      if (!vehicleId || !position) {
        return;
      }

      if (!trailRef.current[vehicleId]) {
        trailRef.current[vehicleId] = [];
      }

      const trail =
        trailRef.current[vehicleId];

      const last =
        trail[trail.length - 1];

      if (
        !last ||
        last.x !== position.x ||
        last.y !== position.y
      ) {
        trail.push(position);
      }

      if (trail.length > 100) {
        trail.shift();
      }

      drawTrail(
        ctx,
        vehicle,
        mapData,
        width,
        height,
        trail
      );
    });

    vehicleList.forEach(
      (vehicle) => {
        drawVehicle(
          ctx,
          vehicle,
          mapData,
          width,
          height
        );
      }
    );

    const detectionList =
      Array.isArray(detections)
        ? detections
        : Object.values(detections || {});

    detectionList.forEach(
      (detection) => {
        drawDetection(
          ctx,
          detection,
          mapData,
          width,
          height
        );
      }
    );

    const hazardList =
      Array.isArray(hazards)
        ? hazards
        : Object.values(hazards || {});

    hazardList.forEach(
      (hazard) => {
        drawHazard(
          ctx,
          hazard,
          mapData,
          width,
          height
        );
      }
    );

    const riskList =
      Array.isArray(risks)
        ? risks
        : Object.values(risks || {});

    riskList.forEach(
      (risk) => {
        drawRiskZone(
          ctx,
          risk,
          mapData,
          width,
          height
        );
      }
    );
  }, [
    mapData,
    vehicles,
    detections,
    hazards,
    risks,
  ]);

  return (
    <div className="live-map-wrapper">
      <canvas
        ref={canvasRef}
        className="live-map-canvas"
      />
    </div>
  );
}
