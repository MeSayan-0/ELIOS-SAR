from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Any

from src.vehicles import VehicleManager


class GCSState:
    """
    Authoritative in-memory state for the ELIOS-SAR GCS.

    Important rules:
    - No operational data is created at startup.
    - Vehicles only appear after inbound vehicle data is received.
    - Telemetry is never fabricated.
    - Sensor readings are never fabricated.
    - Persons, hazards and events are never fabricated.
    - Maps are only stored after real map data is received.
    """

    def __init__(
        self,
        vehicle_manager: VehicleManager | None = None,
    ) -> None:
        self._lock = RLock()

        self.vehicle_manager = (
            vehicle_manager
            if vehicle_manager is not None
            else VehicleManager()
        )

        self.sensors: dict[str, dict[str, Any]] = {}
        self.persons: list[dict[str, Any]] = []
        self.hazards: list[dict[str, Any]] = []
        self.risk_events: list[dict[str, Any]] = []
        self.mission_events: list[dict[str, Any]] = []
        self.missions: dict[str, dict[str, Any]] = {}

        self.map: dict[str, Any] | None = None

    def update_vehicle(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Store a vehicle state received from an actual vehicle source.
        """

        if not isinstance(payload, dict):
            raise TypeError("vehicle payload must be a dictionary")

        with self._lock:
            self.vehicle_manager.update_vehicle(payload)

    def update_sensor(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Store a sensor reading received from an actual vehicle.
        """

        if not isinstance(payload, dict):
            raise TypeError("sensor payload must be a dictionary")

        sensor_id = payload.get("sensor_id")

        if not sensor_id:
            raise ValueError("sensor_id is required")

        with self._lock:
            self.sensors[str(sensor_id)] = deepcopy(payload)

    def add_person(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Store a real person-detection event.
        """

        if not isinstance(payload, dict):
            raise TypeError("person payload must be a dictionary")

        with self._lock:
            self.persons.append(deepcopy(payload))

    def add_person_detection(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Alias for add_person().
        """
        self.add_person(payload)

    def add_hazard(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Store a real hazard event.
        """

        if not isinstance(payload, dict):
            raise TypeError("hazard payload must be a dictionary")

        with self._lock:
            self.hazards.append(deepcopy(payload))

    def add_risk_event(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Store a real risk event.
        """

        if not isinstance(payload, dict):
            raise TypeError("risk event payload must be a dictionary")

        with self._lock:
            self.risk_events.append(deepcopy(payload))

    def add_mission_event(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Store a real mission event.
        """

        if not isinstance(payload, dict):
            raise TypeError(
                "mission event payload must be a dictionary"
            )

        with self._lock:
            self.mission_events.append(
                deepcopy(payload)
            )

    def update_mission(
        self,
        mission_id: str,
        payload: dict[str, Any],
    ) -> None:
        """
        Store/update mission state received from the mission subsystem.
        """

        if not mission_id:
            raise ValueError("mission_id is required")

        if not isinstance(payload, dict):
            raise TypeError(
                "mission payload must be a dictionary"
            )

        with self._lock:
            self.missions[str(mission_id)] = deepcopy(
                payload
            )

    def set_map(
        self,
        payload: dict[str, Any],
    ) -> None:
        """
        Store the latest real map update.

        The GCS does not create an empty or synthetic map.
        """

        if not isinstance(payload, dict):
            raise TypeError("map payload must be a dictionary")

        with self._lock:
            self.map = deepcopy(payload)

    def mark_stale_vehicles_disconnected(self) -> None:
        """
        Update vehicle connection state based on real last-seen times.
        """

        with self._lock:
            self.vehicle_manager.mark_stale_vehicles_disconnected()

    def get_snapshot(self) -> dict[str, Any]:
        """
        Return a complete snapshot for REST/WebSocket consumers.

        Deep copies prevent callers from modifying the authoritative
        backend state accidentally.
        """

        with self._lock:
            return {
                "vehicles": deepcopy(
                    self.vehicle_manager.get_snapshot()
                ),
                "sensors": deepcopy(
                    self.sensors
                ),
                "persons": deepcopy(
                    self.persons
                ),
                "hazards": deepcopy(
                    self.hazards
                ),
                "risk_events": deepcopy(
                    self.risk_events
                ),
                "mission_events": deepcopy(
                    self.mission_events
                ),
                "missions": deepcopy(
                    self.missions
                ),
                "map": deepcopy(
                    self.map
                ),
            }

    def snapshot(self) -> dict[str, Any]:
        """
        Backwards-compatible alias for get_snapshot().
        """

        return self.get_snapshot()
