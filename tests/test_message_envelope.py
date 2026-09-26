import json
import unittest

from src.communication.message_envelope import (
    MessageEnvelope,
)


class TestMessageEnvelope(unittest.TestCase):

    def test_create_envelope(self):
        payload = {
            "vehicle_id": "real-drone",
            "connected": True,
        }

        envelope = MessageEnvelope.create(
            message_type="vehicle_state",
            source="real-drone",
            payload=payload,
        )

        self.assertEqual(
            envelope.message_type,
            "vehicle_state",
        )

        self.assertEqual(
            envelope.source,
            "real-drone",
        )

        self.assertEqual(
            envelope.payload,
            payload,
        )

        self.assertTrue(
            envelope.message_id
        )

        self.assertTrue(
            envelope.timestamp
        )

    def test_create_does_not_modify_payload(self):
        payload = {
            "vehicle_id": "real-rover",
        }

        envelope = MessageEnvelope.create(
            message_type="vehicle_state",
            source="real-rover",
            payload=payload,
        )

        self.assertEqual(
            envelope.payload,
            payload,
        )

        self.assertIsNot(
            envelope.payload,
            payload,
        )

    def test_to_dict(self):
        envelope = MessageEnvelope(
            message_type="sensor_state",
            message_id="message-001",
            timestamp="2026-08-29T00:00:00+00:00",
            source="real-rover",
            payload={
                "vehicle_id": "real-rover",
                "sensor_id": "mq4",
                "value": 123,
            },
        )

        result = envelope.to_dict()

        self.assertEqual(
            result["message_type"],
            "sensor_state",
        )

        self.assertEqual(
            result["message_id"],
            "message-001",
        )

        self.assertEqual(
            result["source"],
            "real-rover",
        )

        self.assertEqual(
            result["payload"]["sensor_id"],
            "mq4",
        )

    def test_json_round_trip(self):
        envelope = MessageEnvelope(
            message_type="vehicle_state",
            message_id="message-002",
            timestamp="2026-08-29T00:00:00+00:00",
            source="real-drone",
            payload={
                "vehicle_id": "real-drone",
                "connected": True,
            },
        )

        encoded = envelope.to_json()

        decoded = MessageEnvelope.from_json(
            encoded
        )

        self.assertEqual(
            decoded,
            envelope,
        )

    def test_from_dict(self):
        data = {
            "message_type": "map_update",
            "message_id": "message-003",
            "timestamp": "2026-08-29T00:00:00+00:00",
            "source": "real-rover",
            "payload": {
                "map_id": "global-map",
                "map_type": "global",
            },
        }

        envelope = MessageEnvelope.from_dict(
            data
        )

        self.assertEqual(
            envelope.message_type,
            "map_update",
        )

        self.assertEqual(
            envelope.source,
            "real-rover",
        )

        self.assertEqual(
            envelope.payload["map_id"],
            "global-map",
        )

    def test_missing_message_type_rejected(self):
        data = {
            "message_id": "message-004",
            "timestamp": "2026-08-29T00:00:00+00:00",
            "source": "real-drone",
            "payload": {},
        }

        with self.assertRaises(ValueError):
            MessageEnvelope.from_dict(data)

    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError):
            MessageEnvelope(
                message_type="vehicle_state",
                message_id="message-005",
                timestamp="2026-08-29T00:00:00+00:00",
                source="",
                payload={},
            )

    def test_non_dict_payload_rejected(self):
        with self.assertRaises(TypeError):
            MessageEnvelope(
                message_type="vehicle_state",
                message_id="message-006",
                timestamp="2026-08-29T00:00:00+00:00",
                source="real-drone",
                payload="invalid",
            )

    def test_json_is_valid(self):
        envelope = MessageEnvelope(
            message_type="risk_event",
            message_id="message-007",
            timestamp="2026-08-29T00:00:00+00:00",
            source="real-drone",
            payload={
                "risk_level": "HIGH",
            },
        )

        encoded = envelope.to_json()

        parsed = json.loads(encoded)

        self.assertEqual(
            parsed["message_type"],
            "risk_event",
        )

        self.assertEqual(
            parsed["payload"]["risk_level"],
            "HIGH",
        )


if __name__ == "__main__":
    unittest.main()
