import unittest

from src.communication.drone_link import DroneLink
from src.communication.gcs_link import GCSLink
from src.communication.protocol import (
    MESSAGE_DRONE_STATE,
    MESSAGE_HAZARD,
    MESSAGE_PERSON_DETECTION,
    MESSAGE_RISK_EVENT,
)
from src.communication.transport import LocalTransport


class TestGCSLink(unittest.TestCase):

    def setUp(self):
        self.transport = LocalTransport()

        self.drone = DroneLink(
            drone_id="ELIOS-DRONE-01",
            transport=self.transport,
        )

        self.gcs = GCSLink(
            gcs_id="ELIOS-GCS-01",
            transport=self.transport,
        )

        self.drone.connect()

    def test_gcs_receives_drone_state(self):
        self.drone.send_drone_state(
            position={
                "x": 10.0,
                "y": 5.0,
                "z": 3.0,
            },
            battery=82.0,
            armed=True,
            flight_mode="AUTO",
        )

        message = self.gcs.receive_message()

        self.assertIsNotNone(message)

        self.assertEqual(
            message.message_type,
            MESSAGE_DRONE_STATE,
        )

        state = self.gcs.get_latest_drone_state()

        self.assertIsNotNone(state)

        self.assertEqual(
            state["battery"],
            82.0,
        )

    def test_gcs_receives_person_detection(self):
        self.drone.send_person_detection(
            person_id="PERSON-001",
            position={
                "x": 4.0,
                "y": 6.0,
                "z": 0.0,
            },
            confidence=0.88,
        )

        message = self.gcs.receive_message()

        self.assertEqual(
            message.message_type,
            MESSAGE_PERSON_DETECTION,
        )

        detections = self.gcs.get_person_detections()

        self.assertEqual(
            len(detections),
            1,
        )

        self.assertEqual(
            detections[0]["person_id"],
            "PERSON-001",
        )

    def test_gcs_receives_hazard(self):
        self.drone.send_hazard(
            hazard_type="METHANE",
            position={
                "x": 7.0,
                "y": 2.0,
                "z": 1.0,
            },
            severity="CRITICAL",
            confidence=0.97,
        )

        message = self.gcs.receive_message()

        self.assertEqual(
            message.message_type,
            MESSAGE_HAZARD,
        )

        hazards = self.gcs.get_hazards()

        self.assertEqual(
            len(hazards),
            1,
        )

        self.assertEqual(
            hazards[0]["severity"],
            "CRITICAL",
        )

    def test_gcs_receives_risk_event(self):
        self.drone.send_risk_event(
            risk_level="HIGH",
            score=78.0,
            affected_person_id="PERSON-001",
            reason="Person detected near methane hazard",
        )

        message = self.gcs.receive_message()

        self.assertEqual(
            message.message_type,
            MESSAGE_RISK_EVENT,
        )

        events = self.gcs.get_risk_events()

        self.assertEqual(
            len(events),
            1,
        )

        self.assertEqual(
            events[0]["risk_level"],
            "HIGH",
        )


if __name__ == "__main__":
    unittest.main()
