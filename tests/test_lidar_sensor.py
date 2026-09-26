import unittest

from src.sensors.lidar_sensor import LidarSensor


class LidarSensorTests(unittest.TestCase):
    def test_create_reading(self) -> None:
        reading = LidarSensor().create_reading(
            angles=[0.0, 1.0, 2.0],
            distances=[2.5, 1.8, 3.2],
        )
        self.assertEqual(len(reading.angles), 3)
        self.assertEqual(len(reading.distances), 3)
        self.assertTrue(reading.valid)

    def test_closest_obstacle(self) -> None:
        sensor = LidarSensor()
        reading = sensor.create_reading([0.0, 1.0, 2.0], [2.5, 1.8, 3.2])
        self.assertEqual(sensor.closest_obstacle(reading), 1.8)

    def test_invalid_distance(self) -> None:
        with self.assertRaises(ValueError):
            LidarSensor().create_reading([0.0], [-1.0])


if __name__ == "__main__":
    unittest.main()
