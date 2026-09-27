from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


class VehicleManager:
    """
    Maintains the registry of vehicles that have actually reported state.

    This manager never creates a vehicle on its own.
    A vehicle exists only after real vehicle data is registered.
    """

    def __init__(self) -> None:
        self._vehicles: dict[str, dict[str, Any]] = {}

    def register_or_update(
        self,
        vehicle: dict[str, Any],
    ) -> None:
        if not isinstance(vehicle, dict):
            raise TypeError("vehicle must be a dictionary")

        vehicle_id = vehicle.get("vehicle_id")

        if not vehicle_id:
            raise ValueError("vehicle_id is required")

        vehicle_id = str(vehicle_id)

        stored_vehicle = dict(vehicle)

        stored_vehicle["vehicle_id"] = vehicle_id

        if "last_seen" not in stored_vehicle:
            stored_vehicle["last_seen"] = datetime.now(
                timezone.utc
            ).isoformat()

        self._vehicles[vehicle_id] = stored_vehicle

    def remove(self, vehicle_id: str) -> bool:
        if vehicle_id in self._vehicles:
            del self._vehicles[vehicle_id]
            return True

        return False

    def get(
        self,
        vehicle_id: str,
    ) -> dict[str, Any] | None:
        vehicle = self._vehicles.get(vehicle_id)

        if vehicle is None:
            return None

        return deepcopy(vehicle)

    def get_all(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self._vehicles)

    def mark_disconnected(
        self,
        vehicle_id: str,
    ) -> bool:
        vehicle = self._vehicles.get(vehicle_id)

        if vehicle is None:
            return False

        vehicle["connected"] = False

        return True

    def mark_stale(
        self,
        timeout_seconds: float,
    ) -> list[str]:
        if timeout_seconds < 0:
            raise ValueError(
                "timeout_seconds cannot be negative"
            )

        now = datetime.now(timezone.utc)

        disconnected: list[str] = []

        for vehicle_id, vehicle in self._vehicles.items():
            last_seen = vehicle.get("last_seen")

            if not last_seen:
                continue

            try:
                timestamp = datetime.fromisoformat(
                    str(last_seen).replace(
                        "Z",
                        "+00:00",
                    )
                )

            except ValueError:
                continue

            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(
                    tzinfo=timezone.utc
                )

            age_seconds = (
                now - timestamp
            ).total_seconds()

            if age_seconds > timeout_seconds:
                if vehicle.get("connected") is not False:
                    vehicle["connected"] = False
                    disconnected.append(vehicle_id)

        return disconnected

    def clear(self) -> None:
        self._vehicles.clear()
