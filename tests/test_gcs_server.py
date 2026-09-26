import unittest

from src.communication.protocol import (
    MESSAGE_VEHICLE_STATE,
)

from gcs.backend.state import GCSState
from gcs.backend.map_service import GCSMapService
from gcs.backend import server as srv


class TestTelemetryIntegration(unittest.TestCase):

    def setUp(self):
        srv.gcs_state = GCSState()
        srv.map_service = GCSMapService()

        from src.telemetry import TelemetryManager

        srv.telemetry_manager = TelemetryManager()

    def test_startup_has_no_telemetry(self):
        state = srv.get_authoritative_state()

        self.assertEqual(
            state["telemetry"],
            {},
        )

    def test_received_telemetry_is_stored(self):
        srv.process_message({
            "message_type": "TELEMETRY",
            "payload": {
                "vehicle_id": "test-drone",
                "telemetry": {
                    "battery": 72.5,
                    "altitude": 4.2,
                    "speed": 1.8,
                },
            },
        })

        state = srv.get_authoritative_state()

        self.assertEqual(
            state["telemetry"]["test-drone"],
            {
                "battery": 72.5,
                "altitude": 4.2,
                "speed": 1.8,
            },
        )

    def test_multiple_vehicle_telemetry_is_separate(self):
        srv.process_message({
            "message_type": "TELEMETRY",
            "payload": {
                "vehicle_id": "test-drone",
                "telemetry": {
                    "battery": 72.5,
                },
            },
        })

        srv.process_message({
            "message_type": "TELEMETRY",
            "payload": {
                "vehicle_id": "test-rover",
                "telemetry": {
                    "battery": 61.0,
                },
            },
        })

        state = srv.get_authoritative_state()

        self.assertEqual(
            state["telemetry"]["test-drone"]["battery"],
            72.5,
        )

        self.assertEqual(
            state["telemetry"]["test-rover"]["battery"],
            61.0,
        )

    def test_vehicle_state_does_not_create_telemetry(self):
        srv.process_message({
            "message_type": MESSAGE_VEHICLE_STATE,
            "payload": {
                "vehicle_id": "test-drone",
                "vehicle_type": "drone",
            },
        })

        state = srv.get_authoritative_state()

        self.assertEqual(
            state["telemetry"],
            {},
        )

    def test_missing_telemetry_is_rejected(self):
        with self.assertRaises(ValueError):
            srv.process_message({
                "message_type": "TELEMETRY",
                "payload": {
                    "vehicle_id": "test-drone",
                },
            })

    def test_invalid_telemetry_payload_is_rejected(self):
        with self.assertRaises(TypeError):
            srv.process_message({
                "message_type": "TELEMETRY",
                "payload": {
                    "vehicle_id": "test-drone",
                    "telemetry": 100,
                },
            })


if __name__ == "__main__":
    unittest.main()
