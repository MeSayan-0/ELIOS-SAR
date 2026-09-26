from dataclasses import dataclass
from typing import List
import math


UNKNOWN = -1
FREE = 0
OCCUPIED = 100


@dataclass
class MapCell:
    x: int
    y: int
    value: int


class OccupancyGrid:
    """
    Simple 2D occupancy grid for ELIOS-SAR.

    Cell values:
        UNKNOWN  = -1
        FREE     = 0
        OCCUPIED = 100
    """

    def __init__(
        self,
        width: int = 200,
        height: int = 200,
        resolution: float = 0.1,
    ):
        if width <= 0:
            raise ValueError("width must be greater than zero")

        if height <= 0:
            raise ValueError("height must be greater than zero")

        if resolution <= 0:
            raise ValueError("resolution must be greater than zero")

        self.width = width
        self.height = height
        self.resolution = resolution

        self.grid = [
            [UNKNOWN for _ in range(width)]
            for _ in range(height)
        ]

    def world_to_grid(self, x: float, y: float):
        """
        Convert world coordinates in meters to grid coordinates.
        """

        grid_x = int(
            (x / self.resolution) + (self.width / 2)
        )

        grid_y = int(
            (y / self.resolution) + (self.height / 2)
        )

        return grid_x, grid_y

    def grid_to_world(self, grid_x: int, grid_y: int):
        """
        Convert grid coordinates back to world coordinates.
        """

        x = (
            grid_x - self.width / 2
        ) * self.resolution

        y = (
            grid_y - self.height / 2
        ) * self.resolution

        return x, y

    def is_inside(self, grid_x: int, grid_y: int) -> bool:
        return (
            0 <= grid_x < self.width
            and
            0 <= grid_y < self.height
        )

    def set_cell(
        self,
        grid_x: int,
        grid_y: int,
        value: int,
    ):
        if not self.is_inside(grid_x, grid_y):
            return

        self.grid[grid_y][grid_x] = value

    def get_cell(
        self,
        grid_x: int,
        grid_y: int,
    ) -> int:

        if not self.is_inside(grid_x, grid_y):
            return UNKNOWN

        return self.grid[grid_y][grid_x]

    def mark_free(self, grid_x: int, grid_y: int):
        self.set_cell(grid_x, grid_y, FREE)

    def mark_occupied(self, grid_x: int, grid_y: int):
        self.set_cell(grid_x, grid_y, OCCUPIED)

    def update_ray(
        self,
        robot_x: float,
        robot_y: float,
        angle_degrees: float,
        distance: float,
    ):
        """
        Update the occupancy grid using one LiDAR measurement.

        Cells along the ray are marked FREE.
        The endpoint is marked OCCUPIED.
        """

        if distance <= 0:
            return

        angle_radians = math.radians(angle_degrees)

        end_x = (
            robot_x
            + distance * math.cos(angle_radians)
        )

        end_y = (
            robot_y
            + distance * math.sin(angle_radians)
        )

        start_grid = self.world_to_grid(
            robot_x,
            robot_y,
        )

        end_grid = self.world_to_grid(
            end_x,
            end_y,
        )

        cells = self._bresenham_line(
            start_grid[0],
            start_grid[1],
            end_grid[0],
            end_grid[1],
        )

        if not cells:
            return

        for grid_x, grid_y in cells[:-1]:
            self.mark_free(grid_x, grid_y)

        endpoint_x, endpoint_y = cells[-1]

        self.mark_occupied(
            endpoint_x,
            endpoint_y,
        )

    def update_scan(
        self,
        robot_x: float,
        robot_y: float,
        measurements: List,
    ):
        """
        Update the map using a complete LiDAR scan.

        Each measurement must contain:

            angle
            distance
        """

        for measurement in measurements:
            self.update_ray(
                robot_x=robot_x,
                robot_y=robot_y,
                angle_degrees=measurement.angle,
                distance=measurement.distance,
            )

    def _bresenham_line(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
    ):
        """
        Return grid cells between two points.
        """

        cells = []

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)

        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        error = dx - dy

        x = x0
        y = y0

        while True:

            cells.append((x, y))

            if x == x1 and y == y1:
                break

            error_2 = 2 * error

            if error_2 > -dy:
                error -= dy
                x += sx

            if error_2 < dx:
                error += dx
                y += sy

        return cells

    def count_cells(self, value: int) -> int:
        """
        Count cells having a particular occupancy value.
        """

        return sum(
            row.count(value)
            for row in self.grid
        )

    def get_statistics(self):
        """
        Return basic map statistics.
        """

        return {
            "width": self.width,
            "height": self.height,
            "resolution": self.resolution,
            "unknown_cells": self.count_cells(UNKNOWN),
            "free_cells": self.count_cells(FREE),
            "occupied_cells": self.count_cells(OCCUPIED),
        }
