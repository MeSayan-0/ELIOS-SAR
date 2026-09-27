import unittest

from src.flight.flight_controller import FlightController


class FlightControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = FlightController()

    def test_connection(self) -> None:
        self.assertTrue(self.controller.connect())
        self.assertTrue(self.controller.connected)

    def test_arm(self) -> None:
        self.controller.connect()
        self.assertTrue(self.controller.arm())
        self.assertTrue(self.controller.armed)

    def test_takeoff(self) -> None:
        self.controller.connect()
        self.controller.arm()
        command = self.controller.takeoff(altitude=3.0)
        self.assertEqual(command.command, "TAKEOFF")
        self.assertEqual(command.target_z, 3.0)

    def test_move(self) -> None:
        self.controller.connect()
        self.controller.arm()
        command = self.controller.move_to(x=5.0, y=2.0, z=3.0)
        self.assertEqual(command.command, "MOVE_TO")
        self.assertEqual(command.target_x, 5.0)

    def test_hover(self) -> None:
        self.controller.connect()
        self.assertEqual(self.controller.hover().command, "HOVER")

    def test_return_to_home(self) -> None:
        self.controller.connect()
        self.assertEqual(
            self.controller.return_to_home().command,
            "RETURN_TO_HOME",
        )

    def test_land(self) -> None:
        self.controller.connect()
        self.assertEqual(self.controller.land().command, "LAND")

    def test_takeoff_without_connection_fails(self) -> None:
        with self.assertRaises(RuntimeError):
            self.controller.takeoff(altitude=3.0)


if __name__ == "__main__":
    unittest.main()
