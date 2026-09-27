"""Stable data contracts shared by ELIOS-SAR subsystems.

These structures deliberately contain no hardware or model-library code.  A
simulator, a physical sensor, or an AI adapter can all produce the same
messages for the rest of the pipeline.
"""

from dataclasses import dataclass, field
import time
from typing import List, Optional


@dataclass
class Position2D:
    """Local two-dimensional position in metres and heading in degrees."""

    x: float
    y: float
    heading: float = 0.0


@dataclass
class PersonDetection:
    """A person-class detection emitted by a perception adapter."""

    id: int
    confidence: float
    bbox: List[float]
    timestamp: float = field(default_factory=time.time)
    position: Optional[Position2D] = None


@dataclass
class HazardDetection:
    """A hazard detection emitted by a future perception adapter."""

    id: int
    hazard_type: str
    confidence: float
    bbox: List[float]
    timestamp: float = field(default_factory=time.time)
    position: Optional[Position2D] = None


@dataclass
class EnvironmentState:
    """Environmental readings collected at one point in time."""

    methane: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class LidarState:
    """One planar LiDAR scan."""

    ranges: List[float]
    angle_min: float
    angle_increment: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class FlightState:
    """Flight telemetry supplied by a simulator or flight-controller adapter."""

    armed: bool
    altitude: float
    battery: float
    position: Optional[Position2D] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class SituationalState:
    """Combined, model-agnostic state consumed by downstream decision modules."""

    people: List[PersonDetection]
    hazards: List[HazardDetection]
    environment: EnvironmentState
    lidar: LidarState
    flight: FlightState


@dataclass
class RiskAssessment:
    """A transparent risk result for one tracked subject."""

    subject_id: int
    risk_level: str
    risk_score: float
    reasons: List[str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class MissionEvent:
    """A prioritized event for future mission-control and GCS adapters."""

    event_type: str
    priority: str
    location: Optional[Position2D]
    description: str
    timestamp: float = field(default_factory=time.time)
