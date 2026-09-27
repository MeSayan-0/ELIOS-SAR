from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VehicleStateMessage:
    """
    State reported by a real rover or drone.

    This class does not generate telemetry.
    Every field represents information supplied by the vehicle.
    """

    vehicle_id: str
    vehicle_type: str
    timestamp: str

    connected: bool

    position: dict[str, float] | None = None
    velocity: dict[str, float] | None = None
    orientation: dict[str, float] | None = None

    battery: dict[str, Any] | None = None

    flight_mode: str | None = None
    armed: bool | None = None

    link: dict[str, Any] | None = None

    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.vehicle_id:
            raise ValueError("vehicle_id is required")

        if self.vehicle_type not in {"drone", "rover"}:
            raise ValueError(
                "vehicle_type must be 'drone' or 'rover'"
            )

        if not self.timestamp:
            raise ValueError("timestamp is required")

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "vehicle_id": self.vehicle_id,
            "vehicle_type": self.vehicle_type,
            "timestamp": self.timestamp,
            "connected": self.connected,
        }

        if self.position is not None:
            payload["position"] = dict(self.position)

        if self.velocity is not None:
            payload["velocity"] = dict(self.velocity)

        if self.orientation is not None:
            payload["orientation"] = dict(self.orientation)

        if self.battery is not None:
            payload["battery"] = dict(self.battery)

        if self.flight_mode is not None:
            payload["flight_mode"] = self.flight_mode

        if self.armed is not None:
            payload["armed"] = self.armed

        if self.link is not None:
            payload["link"] = dict(self.link)

        if self.extra:
            payload["extra"] = dict(self.extra)

        return payload


@dataclass(frozen=True)
class SensorStateMessage:
    """
    Measurement reported by a real sensor attached to a vehicle.
    """

    vehicle_id: str
    sensor_id: str
    sensor_type: str
    timestamp: str

    value: Any
    unit: str | None = None
    status: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.vehicle_id:
            raise ValueError("vehicle_id is required")

        if not self.sensor_id:
            raise ValueError("sensor_id is required")

        if not self.sensor_type:
            raise ValueError("sensor_type is required")

        if not self.timestamp:
            raise ValueError("timestamp is required")

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "vehicle_id": self.vehicle_id,
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "timestamp": self.timestamp,
            "value": self.value,
        }

        if self.unit is not None:
            payload["unit"] = self.unit

        if self.status is not None:
            payload["status"] = self.status

        if self.metadata:
            payload["metadata"] = dict(self.metadata)

        return payload


@dataclass(frozen=True)
class PersonDetectionMessage:
    """
    Person detection produced by an actual perception system.
    """

    vehicle_id: str
    timestamp: str

    detection_id: str
    confidence: float

    bbox: dict[str, float] | None = None
    position: dict[str, float] | None = None

    source: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.vehicle_id:
            raise ValueError("vehicle_id is required")

        if not self.detection_id:
            raise ValueError("detection_id is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if not self.timestamp:
            raise ValueError("timestamp is required")

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "vehicle_id": self.vehicle_id,
            "timestamp": self.timestamp,
            "detection_id": self.detection_id,
            "confidence": self.confidence,
        }

        if self.bbox is not None:
            payload["bbox"] = dict(self.bbox)

        if self.position is not None:
            payload["position"] = dict(self.position)

        if self.source is not None:
            payload["source"] = self.source

        if self.metadata:
            payload["metadata"] = dict(self.metadata)

        return payload


@dataclass(frozen=True)
class HazardMessage:
    """
    Hazard observation produced by a real sensor/perception subsystem.
    """

    vehicle_id: str
    timestamp: str

    hazard_id: str
    hazard_type: str
    severity: str

    confidence: float | None = None

    position: dict[str, float] | None = None

    source: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.vehicle_id:
            raise ValueError("vehicle_id is required")

        if not self.hazard_id:
            raise ValueError("hazard_id is required")

        if not self.hazard_type:
            raise ValueError("hazard_type is required")

        if not self.severity:
            raise ValueError("severity is required")

        if self.confidence is not None:
            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError(
                    "confidence must be between 0.0 and 1.0"
                )

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "vehicle_id": self.vehicle_id,
            "timestamp": self.timestamp,
            "hazard_id": self.hazard_id,
            "hazard_type": self.hazard_type,
            "severity": self.severity,
        }

        if self.confidence is not None:
            payload["confidence"] = self.confidence

        if self.position is not None:
            payload["position"] = dict(self.position)

        if self.source is not None:
            payload["source"] = self.source

        if self.metadata:
            payload["metadata"] = dict(self.metadata)

        return payload


@dataclass(frozen=True)
class RiskEventMessage:
    """
    Risk result produced by the ELIOS-SAR intelligence layer.
    """

    vehicle_id: str
    timestamp: str

    risk_id: str
    risk_level: str
    score: float

    reason: str

    person_id: str | None = None
    position: dict[str, float] | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.vehicle_id:
            raise ValueError("vehicle_id is required")

        if not self.risk_id:
            raise ValueError("risk_id is required")

        if not self.risk_level:
            raise ValueError("risk_level is required")

        if not self.reason:
            raise ValueError("reason is required")

        if self.score < 0.0:
            raise ValueError("score cannot be negative")

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "vehicle_id": self.vehicle_id,
            "timestamp": self.timestamp,
            "risk_id": self.risk_id,
            "risk_level": self.risk_level,
            "score": self.score,
            "reason": self.reason,
        }

        if self.person_id is not None:
            payload["person_id"] = self.person_id

        if self.position is not None:
            payload["position"] = dict(self.position)

        if self.metadata:
            payload["metadata"] = dict(self.metadata)

        return payload


@dataclass(frozen=True)
class MissionStateMessage:
    """
    Mission state reported to the GCS.
    """

    mission_id: str
    status: str
    timestamp: str

    assigned_vehicle_id: str | None = None

    anchor: dict[str, Any] | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.mission_id:
            raise ValueError("mission_id is required")

        if not self.status:
            raise ValueError("status is required")

        if not self.timestamp:
            raise ValueError("timestamp is required")

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "mission_id": self.mission_id,
            "status": self.status,
            "timestamp": self.timestamp,
        }

        if self.assigned_vehicle_id is not None:
            payload["assigned_vehicle_id"] = (
                self.assigned_vehicle_id
            )

        if self.anchor is not None:
            payload["anchor"] = dict(self.anchor)

        if self.metadata:
            payload["metadata"] = dict(self.metadata)

        return payload


@dataclass(frozen=True)
class MissionEventMessage:
    """
    Event generated during a real mission.
    """

    mission_id: str
    timestamp: str

    event_id: str
    event_type: str
    message: str

    vehicle_id: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.mission_id:
            raise ValueError("mission_id is required")

        if not self.event_id:
            raise ValueError("event_id is required")

        if not self.event_type:
            raise ValueError("event_type is required")

        if not self.message:
            raise ValueError("message is required")

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "mission_id": self.mission_id,
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "message": self.message,
        }

        if self.vehicle_id is not None:
            payload["vehicle_id"] = self.vehicle_id

        if self.metadata:
            payload["metadata"] = dict(self.metadata)

        return payload


@dataclass(frozen=True)
class MapUpdateMessage:
    """
    Map information produced by a real mapping subsystem.

    The GCS does not manufacture map cells.
    """

    map_id: str
    map_type: str
    timestamp: str

    resolution: float
    width: int
    height: int

    origin: dict[str, float]

    cells: list[list[int]]

    vehicle_id: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.map_id:
            raise ValueError("map_id is required")

        if self.map_type not in {"global", "local"}:
            raise ValueError(
                "map_type must be 'global' or 'local'"
            )

        if self.resolution <= 0.0:
            raise ValueError(
                "resolution must be greater than zero"
            )

        if self.width <= 0:
            raise ValueError("width must be greater than zero")

        if self.height <= 0:
            raise ValueError("height must be greater than zero")

        if len(self.cells) != self.height:
            raise ValueError(
                "cells height does not match height"
            )

        for row in self.cells:
            if len(row) != self.width:
                raise ValueError(
                    "cells width does not match width"
                )

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "map_id": self.map_id,
            "map_type": self.map_type,
            "timestamp": self.timestamp,
            "resolution": self.resolution,
            "width": self.width,
            "height": self.height,
            "origin": dict(self.origin),
            "cells": [list(row) for row in self.cells],
        }

        if self.vehicle_id is not None:
            payload["vehicle_id"] = self.vehicle_id

        if self.metadata:
            payload["metadata"] = dict(self.metadata)

        return payload
