"""Temperature and humidity sensor abstraction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class EnvironmentReading:
    temperature_c: float
    humidity_percent: float
    timestamp: str
    sensor_id: str
    valid: bool


class EnvironmentSensor:
    def __init__(self, sensor_id: str = "ENVIRONMENT") -> None:
        self.sensor_id = sensor_id

    def read(
        self,
        temperature_c: float,
        humidity_percent: float,
    ) -> EnvironmentReading:
        temperature = float(temperature_c)
        humidity = float(humidity_percent)
        if not -50.0 <= temperature <= 100.0:
            raise ValueError("Temperature outside supported range.")
        if not 0.0 <= humidity <= 100.0:
            raise ValueError("Humidity must be between 0 and 100.")

        return EnvironmentReading(
            temperature_c=temperature,
            humidity_percent=humidity,
            timestamp=datetime.now(timezone.utc).isoformat(),
            sensor_id=self.sensor_id,
            valid=True,
        )
