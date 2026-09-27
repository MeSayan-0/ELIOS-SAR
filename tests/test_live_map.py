import unittest

from src.mapping.occupancy_map import OccupancyGrid
from src.visualization.live_map import LiveMapVisualizer


class TestLiveMapVisualizer(unittest.TestCase):

    def setUp(self):

        self.occupancy_grid = OccupancyGrid(
            width=50,
            height=50,
            resolution=0.1,
        )

    def test_visualizer_creation(self):

        visualizer = LiveMapVisualizer(
            self.occupancy_grid
        )

        self.assertIsNotNone(
            visualizer.figure
        )

        self.assertIsNotNone(
            visualizer.axis
        )

        visualizer.close()

    def test_visualizer_update(self):

        visualizer = LiveMapVisualizer(
            self.occupancy_grid
        )

        visualizer.update(
            drone_x=0.0,
            drone_y=0.0,
        )

        self.assertTrue(
            visualizer.figure
        )

        visualizer.close()


if __name__ == "__main__":
    unittest.main()
