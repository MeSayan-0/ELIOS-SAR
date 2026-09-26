from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TelemetryMessage:
    """
    A container for telemetry supplied by a real vehicle.

    This class does not create, calculate, or default any
    operational telemetry values.
    """

    vehicle_id: str
    telemetry: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.vehicle_id:
            raise ValueError("vehicle_id is required")

        if not isinstance(self.telemetry, dict):
            raise TypeError(
                "telemetry must be a dictionary"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "vehicle_id": self.vehicle_id,
            "telemetry": dict(self.telemetry),
        }

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
    ) -> "TelemetryMessage":
        if not isinstance(payload, dict):
            raise TypeError(
                "payload must be a dictionary"
            )

        vehicle_id = payload.get("vehicle_id")

        if not vehicle_id:
            raise ValueError(
                "vehicle_id is required"
            )

        telemetry = payload.get("telemetry")

        if telemetry is None:
            raise ValueError(
                "telemetry is required"
            )

        if not isinstance(telemetry, dict):
            raise TypeError(
                "telemetry must be a dictionary"
            )

        return cls(
            vehicle_id=str(vehicle_id),
            telemetry=dict(telemetry),
        )
