from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import TelemetryMessage


class TelemetryManager:
    """
    Stores the latest telemetry actually received from vehicles.

    This manager never creates telemetry values.
    """

    def __init__(self) -> None:
        self._telemetry: dict[
            str,
            dict[str, Any],
        ] = {}

    def update(
        self,
        message: TelemetryMessage,
    ) -> None:
        if not isinstance(
            message,
            TelemetryMessage,
        ):
            raise TypeError(
                "message must be a TelemetryMessage"
            )

        self._telemetry[
            message.vehicle_id
        ] = deepcopy(
            message.telemetry
        )

    def update_from_payload(
        self,
        payload: dict[str, Any],
    ) -> None:
        message = TelemetryMessage.from_payload(
            payload
        )

        self.update(message)

    def get(
        self,
        vehicle_id: str,
    ) -> dict[str, Any] | None:
        if not vehicle_id:
            raise ValueError(
                "vehicle_id is required"
            )

        telemetry = self._telemetry.get(
            vehicle_id
        )

        if telemetry is None:
            return None

        return deepcopy(telemetry)

    def get_all(
        self,
    ) -> dict[str, dict[str, Any]]:
        return deepcopy(
            self._telemetry
        )

    def remove(
        self,
        vehicle_id: str,
    ) -> bool:
        if vehicle_id in self._telemetry:
            del self._telemetry[
                vehicle_id
            ]
            return True

        return False

    def clear(self) -> None:
        self._telemetry.clear()
