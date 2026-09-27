import unittest

from src.sensors.environment_sensor import EnvironmentSensor


class EnvironmentSensorTests(unittest.TestCase):
    def test_valid_reading(self) -> None:
        reading = EnvironmentSensor().read(28.5, 65.0)
        self.assertEqual(reading.temperature_c, 28.5)
        self.assertEqual(reading.humidity_percent, 65.0)
        self.assertTrue(reading.valid)

    def test_invalid_humidity(self) -> None:
        with self.assertRaises(ValueError):
            EnvironmentSensor().read(28.5, 120.0)


if __name__ == "__main__":
    unittest.main()
