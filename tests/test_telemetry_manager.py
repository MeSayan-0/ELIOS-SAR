import unittest

from src.telemetry import (
    TelemetryManager,
    TelemetryMessage,
)


class TestTelemetryMessage(unittest.TestCase):

    def test_requires_vehicle_id(self):
        with self.assertRaises(ValueError):
            TelemetryMessage(
                vehicle_id="",
                telemetry={},
            )

    def test_requires_dictionary(self):
        with self.assertRaises(TypeError):
            TelemetryMessage(
                vehicle_id="test-drone",
                telemetry="invalid",
            )

    def test_from_payload(self):
        payload = {
            "vehicle_id": "test-drone",
            "telemetry": {
                "battery": 72.5,
                "altitude": 4.2,
            },
        }

        message = TelemetryMessage.from_payload(
            payload
        )

        self.assertEqual(
            message.vehicle_id,
            "test-drone",
        )

        self.assertEqual(
            message.telemetry,
            payload["telemetry"],
        )

    def test_missing_telemetry_rejected(self):
        with self.assertRaises(ValueError):
            TelemetryMessage.from_payload({
                "vehicle_id": "test-drone",
            })


class TestTelemetryManager(unittest.TestCase):

    def test_starts_empty(self):
        manager = TelemetryManager()

        self.assertEqual(
            manager.get_all(),
            {},
        )

    def test_does_not_create_telemetry(self):
        manager = TelemetryManager()

        self.assertIsNone(
            manager.get("test-drone")
        )

        self.assertEqual(
            manager.get_all(),
            {},
        )

    def test_stores_received_telemetry(self):
        manager = TelemetryManager()

        message = TelemetryMessage(
            vehicle_id="test-drone",
            telemetry={
                "battery": 72.5,
                "altitude": 4.2,
                "speed": 1.8,
            },
        )

        manager.update(message)

        result = manager.get(
            "test-drone"
        )

        self.assertEqual(
            result,
            {
                "battery": 72.5,
                "altitude": 4.2,
                "speed": 1.8,
            },
        )

    def test_update_replaces_latest_telemetry(self):
        manager = TelemetryManager()

        manager.update(
            TelemetryMessage(
                vehicle_id="test-drone",
                telemetry={
                    "battery": 80.0,
                },
            )
        )

        manager.update(
            TelemetryMessage(
                vehicle_id="test-drone",
                telemetry={
                    "battery": 70.0,
                },
            )
        )

        result = manager.get(
            "test-drone"
        )

        self.assertEqual(
            result["battery"],
            70.0,
        )

    def test_multiple_vehicles_are_separate(self):
        manager = TelemetryManager()

        manager.update(
            TelemetryMessage(
                vehicle_id="test-drone",
                telemetry={
                    "battery": 80.0,
                },
            )
        )

        manager.update(
            TelemetryMessage(
                vehicle_id="test-rover",
                telemetry={
                    "battery": 60.0,
                },
            )
        )

        result = manager.get_all()

        self.assertEqual(
            result["test-drone"]["battery"],
            80.0,
        )

        self.assertEqual(
            result["test-rover"]["battery"],
            60.0,
        )

    def test_update_from_payload(self):
        manager = TelemetryManager()

        manager.update_from_payload({
            "vehicle_id": "test-drone",
            "telemetry": {
                "altitude": 8.5,
            },
        })

        result = manager.get(
            "test-drone"
        )

        self.assertEqual(
            result["altitude"],
            8.5,
        )

    def test_get_returns_copy(self):
        manager = TelemetryManager()

        manager.update(
            TelemetryMessage(
                vehicle_id="test-drone",
                telemetry={
                    "battery": 80.0,
                },
            )
        )

        result = manager.get(
            "test-drone"
        )

        result["battery"] = 10.0

        original = manager.get(
            "test-drone"
        )

        self.assertEqual(
            original["battery"],
            80.0,
        )

    def test_get_all_returns_copy(self):
        manager = TelemetryManager()

        manager.update(
            TelemetryMessage(
                vehicle_id="test-drone",
                telemetry={
                    "battery": 80.0,
                },
            )
        )

        result = manager.get_all()

        result["test-drone"]["battery"] = 10.0

        original = manager.get(
            "test-drone"
        )

        self.assertEqual(
            original["battery"],
            80.0,
        )

    def test_remove(self):
        manager = TelemetryManager()

        manager.update(
            TelemetryMessage(
                vehicle_id="test-drone",
                telemetry={
                    "battery": 80.0,
                },
            )
        )

        removed = manager.remove(
            "test-drone"
        )

        self.assertTrue(removed)

        self.assertIsNone(
            manager.get("test-drone")
        )

    def test_remove_unknown_is_safe(self):
        manager = TelemetryManager()

        self.assertFalse(
            manager.remove("unknown")
        )

    def test_clear(self):
        manager = TelemetryManager()

        manager.update(
            TelemetryMessage(
                vehicle_id="test-drone",
                telemetry={
                    "battery": 80.0,
                },
            )
        )

        manager.clear()

        self.assertEqual(
            manager.get_all(),
            {},
        )


if __name__ == "__main__":
    unittest.main()
