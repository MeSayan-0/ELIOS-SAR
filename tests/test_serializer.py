import unittest

from src.communication.protocol import (
    create_message,
    MESSAGE_HAZARD,
)

from src.communication.serializer import MessageSerializer


class TestMessageSerializer(unittest.TestCase):

    def test_serialize_and_deserialize(self):

        original = create_message(
            message_type=MESSAGE_HAZARD,
            source="DRONE-01",
            payload={
                "hazard_type": "FIRE",
                "confidence": 0.88,
            },
            message_id="MSG-001",
        )

        encoded = MessageSerializer.serialize(original)

        decoded = MessageSerializer.deserialize(encoded)

        self.assertEqual(
            decoded.message_id,
            "MSG-001",
        )

        self.assertEqual(
            decoded.message_type,
            MESSAGE_HAZARD,
        )

        self.assertEqual(
            decoded.payload["hazard_type"],
            "FIRE",
        )


if __name__ == "__main__":
    unittest.main()
