import unittest

from src.communication.drone_link import DroneLink
from src.communication.protocol import (
    MESSAGE_DRONE_STATE,
    MESSAGE_HAZARD,
    MESSAGE_PERSON_DETECTION,
)
from src.communication.transport import LocalTransport


class TestDroneLink(unittest.TestCase):

    def setUp(self):
        self.transport = LocalTransport()
        self.drone = DroneLink(
            drone_id="ELIOS-DRONE-01",
            transport=self.transport,
        )

        self.drone.connect()

    def test_send_drone_state(self):
        message = self.drone.send_drone_state(
            position={
                "x": 2.0,
                "y": 3.0,
                "z": 4.0,
            },
            battery=87.5,
            armed=True,
            flight_mode="AUTO",
        )

        self.assertEqual(
            message.message_type,
            MESSAGE_DRONE_STATE,
        )

        self.assertEqual(
            message.source,
            "ELIOS-DRONE-01",
        )

    def test_send_person_detection(self):
        message = self.drone.send_person_detection(
            person_id="PERSON-001",
            position={
                "x": 4.0,
                "y": 2.0,
                "z": 0.0,
            },
            confidence=0.91,
        )

        self.assertEqual(
            message.message_type,
            MESSAGE_PERSON_DETECTION,
        )

        self.assertEqual(
            message.payload["person_id"],
            "PERSON-001",
        )

    def test_send_hazard(self):
        message = self.drone.send_hazard(
            hazard_type="METHANE",
            position={
                "x": 5.0,
                "y": 1.0,
                "z": 2.0,
            },
            severity="HIGH",
            confidence=0.95,
        )

        self.assertEqual(
            message.message_type,
            MESSAGE_HAZARD,
        )

        self.assertEqual(
            message.payload["hazard_type"],
            "METHANE",
        )

    def test_message_reaches_transport(self):
        self.drone.send_drone_state(
            position={
                "x": 0.0,
                "y": 0.0,
                "z": 2.0,
            },
            battery=90.0,
            armed=False,
            flight_mode="HOVER",
        )

        self.assertEqual(
            self.transport.pending_messages(),
            1,
        )


if __name__ == "__main__":
    unittest.main()
