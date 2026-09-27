from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional
import time


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float

    def to_list(self) -> list[float]:
        return [
            float(self.x1),
            float(self.y1),
            float(self.x2),
            float(self.y2),
        ]


@dataclass
class Detection:
    label: str
    confidence: float
    bbox: list[float]
    source: str = "rgb"
    track_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HazardObservation:
    hazard_type: str
    confidence: float
    source: str
    bbox: Optional[list[float]] = None
    severity_hint: str = "unknown"
    persistent: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RiskResult:
    level: str
    score: float
    reasons: list[str] = field(default_factory=list)
    active_hazards: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FrameResult:
    frame_id: int
    timestamp: float
    persons: list[Detection] = field(default_factory=list)
    hazards: list[HazardObservation] = field(default_factory=list)
    risk: Optional[RiskResult] = None
    inference_ms: float = 0.0
    system_status: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        return result
