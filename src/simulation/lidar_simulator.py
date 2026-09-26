from dataclasses import dataclass
import math


@dataclass
class LidarMeasurement:
    """
    Represents one simulated LiDAR measurement.
    """

    angle: float
    distance: float


class LidarSimulator:
    """
    Software-only 2D LiDAR simulator for ELIOS-SAR.

    The simulator represents a circular scanning LiDAR
    operating in a 2D environment.

    It does not control real hardware.
    """

    def __init__(
        self,
        min_range: float = 0.15,
        max_range: float = 12.0,
        angle_step: float = 10.0,
    ):
        self.min_range = min_range
        self.max_range = max_range
        self.angle_step = angle_step

    # ---------------------------------------------------------
    # SCAN
    # ---------------------------------------------------------

    def scan(
        self,
        drone_x: float,
        drone_y: float,
        drone_yaw: float,
        environment,
    ):
        """
        Perform one complete 2D LiDAR scan.

        Parameters
        ----------
        drone_x:
            Drone X position in metres.

        drone_y:
            Drone Y position in metres.

        drone_yaw:
            Drone heading in degrees.

        environment:
            Environment object containing rectangular walls.

        Returns
        -------
        list[LidarMeasurement]
            Simulated LiDAR measurements.
        """

        measurements = []

        angle = 0.0

        while angle < 360.0:

            world_angle = drone_yaw + angle

            distance = self._cast_ray(
                drone_x,
                drone_y,
                world_angle,
                environment,
            )

            measurements.append(
                LidarMeasurement(
                    angle=angle,
                    distance=distance,
                )
            )

            angle += self.angle_step

        return measurements

    # ---------------------------------------------------------
    # RAY CASTING
    # ---------------------------------------------------------

    def _cast_ray(
        self,
        origin_x: float,
        origin_y: float,
        angle: float,
        environment,
    ) -> float:
        """
        Calculate the distance from the drone to the
        nearest wall along a ray.
        """

        radians = math.radians(angle)

        direction_x = math.cos(radians)
        direction_y = math.sin(radians)

        nearest_distance = self.max_range

        for wall in environment.walls:

            distance = self._ray_rectangle_distance(
                origin_x,
                origin_y,
                direction_x,
                direction_y,
                wall,
            )

            if distance is not None:

                if self.min_range <= distance < nearest_distance:
                    nearest_distance = distance

        return nearest_distance

    # ---------------------------------------------------------
    # RECTANGLE INTERSECTION
    # ---------------------------------------------------------

    def _ray_rectangle_distance(
        self,
        origin_x,
        origin_y,
        direction_x,
        direction_y,
        rectangle,
    ):
        """
        Calculate the nearest intersection between
        a ray and a rectangular wall boundary.
        """

        min_x = rectangle["min_x"]
        max_x = rectangle["max_x"]
        min_y = rectangle["min_y"]
        max_y = rectangle["max_y"]

        distances = []

        # -----------------------------------------------------
        # Vertical wall: x = min_x
        # -----------------------------------------------------

        if abs(direction_x) > 1e-9:

            t = (min_x - origin_x) / direction_x

            if t >= 0:

                y = origin_y + t * direction_y

                if min_y <= y <= max_y:
                    distances.append(t)

        # -----------------------------------------------------
        # Vertical wall: x = max_x
        # -----------------------------------------------------

        if abs(direction_x) > 1e-9:

            t = (max_x - origin_x) / direction_x

            if t >= 0:

                y = origin_y + t * direction_y

                if min_y <= y <= max_y:
                    distances.append(t)

        # -----------------------------------------------------
        # Horizontal wall: y = min_y
        # -----------------------------------------------------

        if abs(direction_y) > 1e-9:

            t = (min_y - origin_y) / direction_y

            if t >= 0:

                x = origin_x + t * direction_x

                if min_x <= x <= max_x:
                    distances.append(t)

        # -----------------------------------------------------
        # Horizontal wall: y = max_y
        # -----------------------------------------------------

        if abs(direction_y) > 1e-9:

            t = (max_y - origin_y) / direction_y

            if t >= 0:

                x = origin_x + t * direction_x

                if min_x <= x <= max_x:
                    distances.append(t)

        if not distances:
            return None

        return min(distances)


class TunnelEnvironment:
    """
    Simple rectangular underground tunnel environment.

    Coordinates are expressed in metres.
    """

    def __init__(
        self,
        min_x: float = 0.0,
        max_x: float = 20.0,
        min_y: float = 0.0,
        max_y: float = 10.0,
    ):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

        self.walls = [
            {
                "min_x": min_x,
                "max_x": max_x,
                "min_y": min_y,
                "max_y": min_y,
            },
            {
                "min_x": min_x,
                "max_x": max_x,
                "min_y": max_y,
                "max_y": max_y,
            },
            {
                "min_x": min_x,
                "max_x": min_x,
                "min_y": min_y,
                "max_y": max_y,
            },
            {
                "min_x": max_x,
                "max_x": max_x,
                "min_y": min_y,
                "max_y": max_y,
            },
        ]
