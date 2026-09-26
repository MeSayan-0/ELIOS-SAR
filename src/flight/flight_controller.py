"""
ELIOS-SAR
Phase 10 - Flight Controller Interface

This abstraction currently uses mock behavior and can later connect to PX4 or
Pixhawk through a MAVLink adapter.
"""

from __future__ import annotations

from src.flight.flight_command import FlightCommand


class FlightController:
    """High-level flight-controller abstraction; it does not control motors."""

    def __init__(self) -> None:
        self.connected = False
        self.armed = False
        self.current_mode = "IDLE"

    def connect(self) -> bool:
        self.connected = True
        return True

    def disconnect(self) -> None:
        self.connected = False
        self.armed = False
        self.current_mode = "IDLE"

    def arm(self) -> bool:
        if not self.connected:
            return False
        self.armed = True
        return True

    def disarm(self) -> bool:
        self.armed = False
        return True

    def set_mode(self, mode: str) -> bool:
        if not self.connected:
            return False
        self.current_mode = mode
        return True

    def takeoff(self, altitude: float) -> FlightCommand:
        self._require_armed()
        self.current_mode = "TAKEOFF"
        return FlightCommand(
            command="TAKEOFF",
            target_z=altitude,
            reason="Drone takeoff requested.",
        )

    def move_to(self, x: float, y: float, z: float) -> FlightCommand:
        self._require_armed()
        self.current_mode = "NAVIGATE"
        return FlightCommand(
            command="MOVE_TO",
            target_x=x,
            target_y=y,
            target_z=z,
            reason="Navigation command.",
        )

    def hover(self) -> FlightCommand:
        self._require_connected()
        self.current_mode = "HOVER"
        return FlightCommand(
            command="HOVER",
            reason="Drone should maintain current position.",
        )

    def return_to_home(self) -> FlightCommand:
        self._require_connected()
        self.current_mode = "RETURN"
        return FlightCommand(
            command="RETURN_TO_HOME",
            reason="Return-to-home requested.",
        )

    def land(self) -> FlightCommand:
        self._require_connected()
        self.current_mode = "LAND"
        return FlightCommand(
            command="LAND",
            reason="Landing requested.",
        )

    def _require_connected(self) -> None:
        if not self.connected:
            raise RuntimeError("Flight controller is not connected.")

    def _require_armed(self) -> None:
        if not self.connected or not self.armed:
            raise RuntimeError(
                "Flight controller must be connected and armed."
            )
