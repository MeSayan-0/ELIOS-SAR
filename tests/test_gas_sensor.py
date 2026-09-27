import unittest

from src.sensors.gas_sensor import GasSensor


class GasSensorTests(unittest.TestCase):
    def test_normal_value(self) -> None:
        reading = GasSensor().read(0.25)
        self.assertEqual(reading.methane_raw, 0.25)
        self.assertEqual(reading.methane_level, 0.25)
        self.assertTrue(reading.valid)

    def test_value_is_clamped(self) -> None:
        reading = GasSensor().read(1.5)
        self.assertEqual(reading.methane_level, 1.0)


if __name__ == "__main__":
    unittest.main()
