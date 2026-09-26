import unittest

from src.communication.protocol import (
    create_message,
    MESSAGE_PERSON_DETECTION,
)


class TestCommunicationProtocol(unittest.TestCase):

    def test_message_creation(self):

        message = create_message(
            message_type=MESSAGE_PERSON_DETECTION,
            source="DRONE-01",
            payload={
                "person_count": 2,
                "confidence": 0.91,
            },
        )

        self.assertEqual(
            message.message_type,
            MESSAGE_PERSON_DETECTION,
        )

        self.assertEqual(
            message.source,
            "DRONE-01",
        )

        self.assertEqual(
            message.payload["person_count"],
            2,
        )

        self.assertTrue(message.timestamp)


if __name__ == "__main__":
    unittest.main()
