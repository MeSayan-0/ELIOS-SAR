import unittest

from src.sensors.sensor_manager import SensorManager


class SensorManagerTests(unittest.TestCase):
    def test_sensor_updates(self) -> None:
        manager = SensorManager()
        manager.update_gas(0.35)
        manager.update_environment(29.0, 70.0)
        manager.update_lidar([0.0, 1.0, 2.0], [2.0, 1.5, 3.0])

        snapshot = manager.get_snapshot()
        self.assertIsNotNone(snapshot.gas)
        self.assertIsNotNone(snapshot.environment)
        self.assertIsNotNone(snapshot.lidar)


if __name__ == "__main__":
    unittest.main()
