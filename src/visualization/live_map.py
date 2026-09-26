import matplotlib.pyplot as plt

from src.mapping.occupancy_map import (
    UNKNOWN,
    FREE,
    OCCUPIED,
)


class LiveMapVisualizer:
    """
    Live 2D occupancy-map visualizer for ELIOS-SAR.
    """

    def __init__(self, occupancy_grid):

        self.occupancy_grid = occupancy_grid

        self.figure, self.axis = plt.subplots(
            figsize=(8, 8)
        )

        self.axis.set_title(
            "ELIOS-SAR Local 2D Map"
        )

        self.axis.set_xlabel(
            "X (meters)"
        )

        self.axis.set_ylabel(
            "Y (meters)"
        )

        self.axis.set_aspect(
            "equal"
        )

    def update(
        self,
        drone_x: float,
        drone_y: float,
    ):
        """
        Redraw the occupancy map and drone position.
        """

        self.axis.clear()

        self.axis.set_title(
            "ELIOS-SAR Local 2D Map"
        )

        self.axis.set_xlabel(
            "X (meters)"
        )

        self.axis.set_ylabel(
            "Y (meters)"
        )

        self.axis.set_aspect(
            "equal"
        )

        grid = self.occupancy_grid.grid

        display_grid = []

        for row in grid:

            display_row = []

            for cell in row:

                if cell == UNKNOWN:
                    display_row.append(0.5)

                elif cell == FREE:
                    display_row.append(1.0)

                elif cell == OCCUPIED:
                    display_row.append(0.0)

                else:
                    display_row.append(0.5)

            display_grid.append(display_row)

        extent = [
            -(
                self.occupancy_grid.width
                * self.occupancy_grid.resolution
                / 2
            ),
            (
                self.occupancy_grid.width
                * self.occupancy_grid.resolution
                / 2
            ),
            -(
                self.occupancy_grid.height
                * self.occupancy_grid.resolution
                / 2
            ),
            (
                self.occupancy_grid.height
                * self.occupancy_grid.resolution
                / 2
            ),
        ]

        self.axis.imshow(
            display_grid,
            origin="lower",
            extent=extent,
            interpolation="nearest",
        )

        self.axis.plot(
            drone_x,
            drone_y,
            marker="^",
            markersize=10,
        )

        self.axis.grid(
            True,
            alpha=0.2,
        )

        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def show(self):

        plt.show()

    def close(self):

        plt.close(
            self.figure
        )
