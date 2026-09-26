"""MQ-4 gas anomaly abstraction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class GasReading:
    methane_raw: float
    methane_level: float
    timestamp: str
    sensor_id: str
    valid: bool


class GasSensor:
    def __init__(self, sensor_id: str = "MQ4") -> None:
        self.sensor_id = sensor_id

    def read(self, methane_raw: float) -> GasReading:
        raw_value = float(methane_raw)
        methane_level = max(0.0, min(raw_value, 1.0))
        return GasReading(
            methane_raw=raw_value,
            methane_level=methane_level,
            timestamp=datetime.now(timezone.utc).isoformat(),
            sensor_id=self.sensor_id,
            valid=True,
        )
