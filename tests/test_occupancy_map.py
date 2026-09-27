import unittest

from src.mapping.occupancy_map import (
    OccupancyGrid,
    UNKNOWN,
    FREE,
    OCCUPIED,
)

from src.simulation.lidar_simulator import LidarMeasurement


class TestOccupancyGrid(unittest.TestCase):

    def setUp(self):
        self.map = OccupancyGrid(
            width=100,
            height=100,
            resolution=0.1,
        )

    def test_initial_map_is_unknown(self):

        statistics = self.map.get_statistics()

        self.assertEqual(
            statistics["unknown_cells"],
            100 * 100,
        )

        self.assertEqual(
            statistics["free_cells"],
            0,
        )

        self.assertEqual(
            statistics["occupied_cells"],
            0,
        )

    def test_world_to_grid_and_back(self):

        grid_x, grid_y = self.map.world_to_grid(
            0.0,
            0.0,
        )

        x, y = self.map.grid_to_world(
            grid_x,
            grid_y,
        )

        self.assertAlmostEqual(
            x,
            0.0,
            delta=0.1,
        )

        self.assertAlmostEqual(
            y,
            0.0,
            delta=0.1,
        )

    def test_set_and_get_cell(self):

        self.map.set_cell(
            50,
            50,
            OCCUPIED,
        )

        self.assertEqual(
            self.map.get_cell(50, 50),
            OCCUPIED,
        )

    def test_free_cell(self):

        self.map.mark_free(
            50,
            50,
        )

        self.assertEqual(
            self.map.get_cell(50, 50),
            FREE,
        )

    def test_ray_creates_free_space_and_obstacle(self):

        self.map.update_ray(
            robot_x=0.0,
            robot_y=0.0,
            angle_degrees=0.0,
            distance=2.0,
        )

        statistics = self.map.get_statistics()

        self.assertGreater(
            statistics["free_cells"],
            0,
        )

        self.assertGreater(
            statistics["occupied_cells"],
            0,
        )

    def test_lidar_scan_updates_map(self):

        measurements = [
            LidarMeasurement(
                angle=0.0,
                distance=2.0,
            ),
            LidarMeasurement(
                angle=90.0,
                distance=2.0,
            ),
            LidarMeasurement(
                angle=180.0,
                distance=2.0,
            ),
            LidarMeasurement(
                angle=270.0,
                distance=2.0,
            ),
        ]

        self.map.update_scan(
            robot_x=0.0,
            robot_y=0.0,
            measurements=measurements,
        )

        statistics = self.map.get_statistics()

        self.assertGreater(
            statistics["free_cells"],
            0,
        )

        self.assertGreater(
            statistics["occupied_cells"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
