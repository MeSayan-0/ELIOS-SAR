from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class Vehicle:
    """
    Runtime representation of a vehicle known to the GCS.

    A Vehicle instance exists only after real vehicle data has
    been received by the backend.

    No operational values are generated here.
    """

    vehicle_id: str
    vehicle_type: str

    connected: bool = False
    last_seen: str | None = None

    telemetry: dict[str, Any] | None = None

    def mark_seen(self) -> None:
        """
        Record the time at which real data was received.
        """

        self.connected = True
        self.last_seen = datetime.now(
            timezone.utc
        ).isoformat()

    def update_telemetry(
        self,
        telemetry: dict[str, Any],
    ) -> None:
        """
        Store telemetry supplied by the vehicle.

        The GCS does not create or modify telemetry values.
        """

        if not isinstance(telemetry, dict):
            raise TypeError("telemetry must be a dictionary")

        self.telemetry = dict(telemetry)
        self.mark_seen()

    def mark_disconnected(self) -> None:
        """
        Mark the vehicle disconnected.

        Existing telemetry is retained because it represents
        the last data actually received.
        """

        self.connected = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "vehicle_id": self.vehicle_id,
            "vehicle_type": self.vehicle_type,
            "connected": self.connected,
            "last_seen": self.last_seen,
            "telemetry": (
                dict(self.telemetry)
                if self.telemetry is not None
                else None
            ),
        }
