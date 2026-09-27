import unittest

from src.communication.protocol import (
    create_message,
    MESSAGE_SENSOR_STATE,
)

from src.communication.transport import LocalTransport


class TestLocalTransport(unittest.TestCase):

    def test_connection(self):

        transport = LocalTransport()

        self.assertFalse(transport.connected)

        transport.connect()

        self.assertTrue(transport.connected)

        transport.disconnect()

        self.assertFalse(transport.connected)

    def test_send_and_receive(self):

        transport = LocalTransport()

        transport.connect()

        message = create_message(
            message_type=MESSAGE_SENSOR_STATE,
            source="DRONE-01",
            payload={
                "methane_ppm": 150,
                "temperature": 29.5,
                "humidity": 71.0,
            },
        )

        transport.send(message)

        self.assertEqual(
            transport.pending_messages(),
            1,
        )

        received = transport.receive()

        self.assertIsNotNone(received)

        self.assertEqual(
            received.message_type,
            MESSAGE_SENSOR_STATE,
        )

        self.assertEqual(
            received.payload["methane_ppm"],
            150,
        )

        self.assertEqual(
            transport.pending_messages(),
            0,
        )


if __name__ == "__main__":
    unittest.main()
