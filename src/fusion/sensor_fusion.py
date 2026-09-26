"""Build a fault-aware situational snapshot from standardized inputs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class SensorFusion:
    def __init__(
        self,
        methane_warning: float = 0.40,
        methane_critical: float = 0.75,
        obstacle_warning_distance: float = 1.00,
    ) -> None:
        if not 0.0 <= methane_warning <= methane_critical <= 1.0:
            raise ValueError(
                "Methane thresholds must satisfy 0 <= warning <= critical <= 1."
            )
        if obstacle_warning_distance < 0.0:
            raise ValueError("Obstacle warning distance must not be negative.")

        self.methane_warning = methane_warning
        self.methane_critical = methane_critical
        self.obstacle_warning_distance = obstacle_warning_distance

    def build_state(
        self,
        person_detections: list[Any],
        hazard_detections: list[Any],
        methane_level: float | None,
        temperature_c: float | None,
        humidity_percent: float | None,
        nearest_obstacle_m: float | None,
        position: dict[str, float] | None,
    ) -> dict[str, Any]:
        gas_status = self._gas_status(methane_level)
        obstacle_status = self._obstacle_status(nearest_obstacle_m)
        hazard_types = [
            self._hazard_type(hazard)
            for hazard in hazard_detections
            if self._hazard_type(hazard) is not None
        ]

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "person_count": len(person_detections),
            "persons": person_detections,
            "hazards": hazard_detections,
            "hazard_types": hazard_types,
            "methane_level": methane_level,
            "gas_status": gas_status,
            "temperature_c": temperature_c,
            "humidity_percent": humidity_percent,
            "nearest_obstacle_m": nearest_obstacle_m,
            "obstacle_status": obstacle_status,
            "position": position,
        }

    def _gas_status(self, methane_level: float | None) -> str:
        if methane_level is None:
            return "UNKNOWN"
        if methane_level >= self.methane_critical:
            return "CRITICAL"
        if methane_level >= self.methane_warning:
            return "WARNING"
        return "NORMAL"

    def _obstacle_status(self, nearest_obstacle_m: float | None) -> str:
        if nearest_obstacle_m is None:
            return "UNKNOWN"
        return (
            "WARNING"
            if nearest_obstacle_m <= self.obstacle_warning_distance
            else "NORMAL"
        )

    @staticmethod
    def _hazard_type(hazard: Any) -> str | None:
        if isinstance(hazard, dict):
            value = hazard.get("class_name", hazard.get("hazard_type"))
        else:
            value = getattr(hazard, "hazard_type", None)
        return None if value is None else str(value)
