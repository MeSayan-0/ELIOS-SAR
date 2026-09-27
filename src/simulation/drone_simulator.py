from dataclasses import dataclass


@dataclass
class DroneState:
    """
    Represents the simulated state of the ELIOS-SAR drone.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    velocity_x: float = 0.0
    velocity_y: float = 0.0
    velocity_z: float = 0.0

    battery: float = 100.0

    armed: bool = False
    connected: bool = False

    flight_mode: str = "DISCONNECTED"


class DroneSimulator:
    """
    Software-only drone simulator for ELIOS-SAR.

    This simulator does not control real hardware.
    It provides a predictable drone state for development
    of mapping, perception, mission logic and communication.
    """

    def __init__(self):
        self.state = DroneState()

    # ---------------------------------------------------------
    # CONNECTION
    # ---------------------------------------------------------

    def connect(self) -> bool:
        """Connect the simulated drone."""

        self.state.connected = True
        self.state.flight_mode = "STANDBY"

        return True

    def disconnect(self) -> bool:
        """Disconnect the simulated drone."""

        self.state.connected = False
        self.state.armed = False
        self.state.flight_mode = "DISCONNECTED"

        return True

    # ---------------------------------------------------------
    # ARMING
    # ---------------------------------------------------------

    def arm(self) -> bool:
        """
        Arm the simulated drone.

        The drone must be connected before arming.
        """

        if not self.state.connected:
            return False

        if self.state.battery <= 10.0:
            return False

        self.state.armed = True
        self.state.flight_mode = "ARMED"

        return True

    def disarm(self) -> bool:
        """Disarm the simulated drone."""

        self.state.armed = False

        if self.state.z <= 0.0:
            self.state.flight_mode = "STANDBY"

        return True

    # ---------------------------------------------------------
    # TAKEOFF
    # ---------------------------------------------------------

    def takeoff(self, altitude: float) -> bool:
        """
        Simulate takeoff to a specified altitude.
        """

        if not self.state.connected:
            return False

        if not self.state.armed:
            return False

        if altitude <= 0.0:
            return False

        self.state.z = altitude
        self.state.velocity_z = 0.0
        self.state.flight_mode = "FLIGHT"

        self._consume_battery(1.0)

        return True

    # ---------------------------------------------------------
    # MOVEMENT
    # ---------------------------------------------------------

    def move(self, x: float, y: float, z: float | None = None) -> bool:
        """
        Move the simulated drone to a target position.
        """

        if not self.state.connected:
            return False

        if not self.state.armed:
            return False

        if self.state.z <= 0.0:
            return False

        self.state.x = x
        self.state.y = y

        if z is not None:
            if z < 0.0:
                return False

            self.state.z = z

        self.state.velocity_x = 0.0
        self.state.velocity_y = 0.0
        self.state.velocity_z = 0.0

        self._consume_battery(0.5)

        return True

    # ---------------------------------------------------------
    # YAW
    # ---------------------------------------------------------

    def set_yaw(self, yaw: float) -> bool:
        """Set simulated drone heading."""

        if not self.state.connected:
            return False

        self.state.yaw = yaw % 360.0

        return True

    # ---------------------------------------------------------
    # HOVER
    # ---------------------------------------------------------

    def hover(self) -> bool:
        """Keep the drone at its current position."""

        if not self.state.connected:
            return False

        if not self.state.armed:
            return False

        self.state.velocity_x = 0.0
        self.state.velocity_y = 0.0
        self.state.velocity_z = 0.0
        self.state.flight_mode = "HOVER"

        return True

    # ---------------------------------------------------------
    # RETURN
    # ---------------------------------------------------------

    def return_to_home(self) -> bool:
        """
        Simulate return to the home position.

        Home position is x=0, y=0.
        """

        if not self.state.connected:
            return False

        if not self.state.armed:
            return False

        self.state.x = 0.0
        self.state.y = 0.0

        self.state.velocity_x = 0.0
        self.state.velocity_y = 0.0

        self.state.flight_mode = "RETURN"

        self._consume_battery(0.5)

        return True

    # ---------------------------------------------------------
    # LAND
    # ---------------------------------------------------------

    def land(self) -> bool:
        """Simulate landing."""

        if not self.state.connected:
            return False

        if not self.state.armed:
            return False

        self.state.z = 0.0

        self.state.velocity_x = 0.0
        self.state.velocity_y = 0.0
        self.state.velocity_z = 0.0

        self.state.flight_mode = "LANDED"

        return True

    # ---------------------------------------------------------
    # BATTERY
    # ---------------------------------------------------------

    def _consume_battery(self, amount: float) -> None:
        """Reduce simulated battery."""

        self.state.battery = max(
            0.0,
            self.state.battery - amount
        )

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------

    def get_state(self) -> DroneState:
        """Return the current simulated drone state."""

        return self.state
