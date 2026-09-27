"""Planar LiDAR measurement abstraction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math


@dataclass
class LidarReading:
    angles: list[float]
    distances: list[float]
    timestamp: str
    sensor_id: str
    valid: bool


class LidarSensor:
    def __init__(self, sensor_id: str = "LIDAR") -> None:
        self.sensor_id = sensor_id

    def create_reading(
        self,
        angles: list[float],
        distances: list[float],
    ) -> LidarReading:
        if len(angles) != len(distances):
            raise ValueError("Angles and distances must have the same length.")

        cleaned_distances = []
        for distance in distances:
            numeric_distance = float(distance)
            if numeric_distance < 0 or not math.isfinite(numeric_distance):
                raise ValueError("Invalid LiDAR distance.")
            cleaned_distances.append(numeric_distance)

        return LidarReading(
            angles=[float(angle) for angle in angles],
            distances=cleaned_distances,
            timestamp=datetime.now(timezone.utc).isoformat(),
            sensor_id=self.sensor_id,
            valid=True,
        )

    def closest_obstacle(self, reading: LidarReading) -> float:
        valid_distances = [
            distance
            for distance in reading.distances
            if distance > 0 and math.isfinite(distance)
        ]
        return min(valid_distances, default=float("inf"))
