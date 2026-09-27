import unittest

from src.simulation.lidar_simulator import (
    LidarSimulator,
    TunnelEnvironment,
)


class TestLidarSimulator(unittest.TestCase):

    def setUp(self):
        self.lidar = LidarSimulator(
            min_range=0.15,
            max_range=12.0,
            angle_step=10.0,
        )

        self.environment = TunnelEnvironment(
            min_x=0.0,
            max_x=20.0,
            min_y=0.0,
            max_y=10.0,
        )

    def test_environment_has_four_walls(self):
        self.assertEqual(
            len(self.environment.walls),
            4,
        )

    def test_scan_returns_measurements(self):
        measurements = self.lidar.scan(
            drone_x=10.0,
            drone_y=5.0,
            drone_yaw=0.0,
            environment=self.environment,
        )

        self.assertEqual(
            len(measurements),
            36,
        )

    def test_forward_distance(self):
        measurements = self.lidar.scan(
            drone_x=10.0,
            drone_y=5.0,
            drone_yaw=0.0,
            environment=self.environment,
        )

        forward_measurement = measurements[0]

        self.assertEqual(
            forward_measurement.angle,
            0.0,
        )

        self.assertAlmostEqual(
            forward_measurement.distance,
            10.0,
            places=5,
        )

    def test_backward_distance(self):
        measurements = self.lidar.scan(
            drone_x=10.0,
            drone_y=5.0,
            drone_yaw=0.0,
            environment=self.environment,
        )

        backward_measurement = measurements[18]

        self.assertEqual(
            backward_measurement.angle,
            180.0,
        )

        self.assertAlmostEqual(
            backward_measurement.distance,
            10.0,
            places=5,
        )

    def test_left_distance(self):
        measurements = self.lidar.scan(
            drone_x=10.0,
            drone_y=5.0,
            drone_yaw=0.0,
            environment=self.environment,
        )

        left_measurement = measurements[9]

        self.assertEqual(
            left_measurement.angle,
            90.0,
        )

        self.assertAlmostEqual(
            left_measurement.distance,
            5.0,
            places=5,
        )

    def test_right_distance(self):
        measurements = self.lidar.scan(
            drone_x=10.0,
            drone_y=5.0,
            drone_yaw=0.0,
            environment=self.environment,
        )

        right_measurement = measurements[27]

        self.assertEqual(
            right_measurement.angle,
            270.0,
        )

        self.assertAlmostEqual(
            right_measurement.distance,
            5.0,
            places=5,
        )

    def test_all_distances_are_within_sensor_range(self):
        measurements = self.lidar.scan(
            drone_x=10.0,
            drone_y=5.0,
            drone_yaw=0.0,
            environment=self.environment,
        )

        for measurement in measurements:

            self.assertGreaterEqual(
                measurement.distance,
                self.lidar.min_range,
            )

            self.assertLessEqual(
                measurement.distance,
                self.lidar.max_range,
            )


if __name__ == "__main__":
    unittest.main()
