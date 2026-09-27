"""Coordinate normalized readings from the prototype sensors."""

from __future__ import annotations

from dataclasses import dataclass

from src.sensors.environment_sensor import EnvironmentReading, EnvironmentSensor
from src.sensors.gas_sensor import GasReading, GasSensor
from src.sensors.lidar_sensor import LidarReading, LidarSensor


@dataclass
class SensorSnapshot:
    gas: GasReading | None = None
    environment: EnvironmentReading | None = None
    lidar: LidarReading | None = None


class SensorManager:
    def __init__(self) -> None:
        self.gas_sensor = GasSensor()
        self.environment_sensor = EnvironmentSensor()
        self.lidar_sensor = LidarSensor()
        self.snapshot = SensorSnapshot()

    def update_gas(self, methane_raw: float) -> GasReading:
        reading = self.gas_sensor.read(methane_raw)
        self.snapshot.gas = reading
        return reading

    def update_environment(
        self,
        temperature_c: float,
        humidity_percent: float,
    ) -> EnvironmentReading:
        reading = self.environment_sensor.read(temperature_c, humidity_percent)
        self.snapshot.environment = reading
        return reading

    def update_lidar(
        self,
        angles: list[float],
        distances: list[float],
    ) -> LidarReading:
        reading = self.lidar_sensor.create_reading(angles, distances)
        self.snapshot.lidar = reading
        return reading

    def get_snapshot(self) -> SensorSnapshot:
        return self.snapshot
