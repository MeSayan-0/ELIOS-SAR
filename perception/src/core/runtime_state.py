from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class RuntimeState:
    frame_id: int = 0
    started_at: float = field(
        default_factory=time.time
    )
    running: bool = True
    last_detection_time: float = 0.0
    last_hazard_time: float = 0.0
    last_risk_time: float = 0.0
    counters: dict[str, int] = field(
        default_factory=dict
    )

    def increment(self, key: str) -> None:
        self.counters[key] = (
            self.counters.get(key, 0) + 1
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "started_at": self.started_at,
            "running": self.running,
            "last_detection_time": (
                self.last_detection_time
            ),
            "last_hazard_time": (
                self.last_hazard_time
            ),
            "last_risk_time": (
                self.last_risk_time
            ),
            "counters": dict(self.counters),
            "uptime_seconds": (
                time.time() - self.started_at
            ),
        }
