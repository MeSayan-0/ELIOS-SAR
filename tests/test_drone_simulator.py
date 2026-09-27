import unittest

from src.simulation.drone_simulator import (
    DroneSimulator,
)


class TestDroneSimulator(unittest.TestCase):

    def setUp(self):
        self.drone = DroneSimulator()

    def test_initial_state(self):
        state = self.drone.get_state()

        self.assertFalse(state.connected)
        self.assertFalse(state.armed)
        self.assertEqual(state.x, 0.0)
        self.assertEqual(state.y, 0.0)
        self.assertEqual(state.z, 0.0)
        self.assertEqual(state.battery, 100.0)

    def test_connection(self):
        result = self.drone.connect()

        self.assertTrue(result)
        self.assertTrue(self.drone.state.connected)
        self.assertEqual(
            self.drone.state.flight_mode,
            "STANDBY",
        )

    def test_cannot_arm_without_connection(self):
        result = self.drone.arm()

        self.assertFalse(result)
        self.assertFalse(self.drone.state.armed)

    def test_arm_after_connection(self):
        self.drone.connect()

        result = self.drone.arm()

        self.assertTrue(result)
        self.assertTrue(self.drone.state.armed)

    def test_takeoff(self):
        self.drone.connect()
        self.drone.arm()

        result = self.drone.takeoff(3.0)

        self.assertTrue(result)
        self.assertEqual(self.drone.state.z, 3.0)
        self.assertEqual(
            self.drone.state.flight_mode,
            "FLIGHT",
        )

    def test_move(self):
        self.drone.connect()
        self.drone.arm()
        self.drone.takeoff(3.0)

        result = self.drone.move(10.0, 5.0)

        self.assertTrue(result)

        self.assertEqual(self.drone.state.x, 10.0)
        self.assertEqual(self.drone.state.y, 5.0)
        self.assertEqual(self.drone.state.z, 3.0)

    def test_hover(self):
        self.drone.connect()
        self.drone.arm()
        self.drone.takeoff(3.0)

        result = self.drone.hover()

        self.assertTrue(result)
        self.assertEqual(
            self.drone.state.flight_mode,
            "HOVER",
        )

    def test_return_to_home(self):
        self.drone.connect()
        self.drone.arm()
        self.drone.takeoff(3.0)
        self.drone.move(10.0, 5.0)

        result = self.drone.return_to_home()

        self.assertTrue(result)
        self.assertEqual(self.drone.state.x, 0.0)
        self.assertEqual(self.drone.state.y, 0.0)

    def test_land(self):
        self.drone.connect()
        self.drone.arm()
        self.drone.takeoff(3.0)

        result = self.drone.land()

        self.assertTrue(result)
        self.assertEqual(self.drone.state.z, 0.0)
        self.assertEqual(
            self.drone.state.flight_mode,
            "LANDED",
        )


if __name__ == "__main__":
    unittest.main()
