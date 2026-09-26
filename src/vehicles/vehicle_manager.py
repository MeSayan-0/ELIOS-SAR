from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .vehicle import Vehicle


class VehicleManager:
    """
    Manages vehicles that have actually communicated with the GCS.

    Important:
    - No vehicles are created at startup.
    - No default telemetry is generated.
    - No battery values are generated.
    - No positions are generated.
    """

    def __init__(
        self,
        disconnect_timeout_seconds: float = 10.0,
    ) -> None:
        if disconnect_timeout_seconds <= 0:
            raise ValueError(
                "disconnect_timeout_seconds must be positive"
            )

        self.disconnect_timeout_seconds = (
            disconnect_timeout_seconds
        )

        self._vehicles: dict[str, Vehicle] = {}

    def register_vehicle(
        self,
        vehicle_id: str,
        vehicle_type: str,
    ) -> Vehicle:
        """
        Register a vehicle after receiving real vehicle data.
        """

        if not vehicle_id:
            raise ValueError("vehicle_id is required")

        if not vehicle_type:
            raise ValueError("vehicle_type is required")

        if vehicle_id not in self._vehicles:
            self._vehicles[vehicle_id] = Vehicle(
                vehicle_id=vehicle_id,
                vehicle_type=vehicle_type,
            )
        else:
            existing = self._vehicles[vehicle_id]

            if existing.vehicle_type != vehicle_type:
                raise ValueError(
                    "vehicle_type cannot change for an existing vehicle"
                )

        return self._vehicles[vehicle_id]

    def update_vehicle(
        self,
        payload: dict[str, Any],
    ) -> Vehicle:
        """
        Register/update a vehicle using an inbound vehicle-state payload.
        """

        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")

        vehicle_id = payload.get("vehicle_id")
        vehicle_type = payload.get("vehicle_type")

        if not vehicle_id:
            raise ValueError("vehicle_id is required")

        if not vehicle_type:
            raise ValueError("vehicle_type is required")

        vehicle = self.register_vehicle(
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
        )

        telemetry = payload.get("telemetry")

        if telemetry is not None:
            vehicle.update_telemetry(telemetry)
        else:
            flat_telemetry = {
                k: v
                for k, v in payload.items()
                if k not in ("vehicle_id", "vehicle_type", "connected", "timestamp")
            }
            if flat_telemetry:
                vehicle.update_telemetry(flat_telemetry)
            else:
                vehicle.mark_seen()

        return vehicle

    def get_vehicle(
        self,
        vehicle_id: str,
    ) -> Vehicle | None:
        return self._vehicles.get(vehicle_id)

    def get_all(self) -> list[Vehicle]:
        return list(self._vehicles.values())

    def get_snapshot(self) -> dict[str, dict[str, Any]]:
        return {
            vehicle.vehicle_id: vehicle.to_dict()
            for vehicle in self._vehicles.values()
        }

    def mark_stale_vehicles_disconnected(self) -> None:
        """
        Mark vehicles disconnected when their last real message
        is older than the configured timeout.
        """

        now = datetime.now(timezone.utc)

        for vehicle in self._vehicles.values():

            if vehicle.last_seen is None:
                continue

            try:
                last_seen = datetime.fromisoformat(
                    vehicle.last_seen
                )
            except ValueError:
                continue

            elapsed = (
                now - last_seen
            ).total_seconds()

            if elapsed > self.disconnect_timeout_seconds:
                vehicle.mark_disconnected()
