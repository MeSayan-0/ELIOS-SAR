import unittest
from datetime import datetime, timedelta, timezone

from gcs.backend.vehicle_manager import VehicleManager


class TestVehicleManager(unittest.TestCase):

    def test_starts_empty(self):
        manager = VehicleManager()

        self.assertEqual(
            manager.get_all(),
            {},
        )

    def test_registers_real_vehicle_payload(self):
        manager = VehicleManager()

        vehicle = {
            "vehicle_id": "drone-test",
            "vehicle_type": "drone",
            "connected": True,
            "battery": 82.5,
        }

        manager.register_or_update(vehicle)

        result = manager.get("drone-test")

        self.assertIsNotNone(result)
        self.assertEqual(
            result["vehicle_id"],
            "drone-test",
        )
        self.assertEqual(
            result["vehicle_type"],
            "drone",
        )
        self.assertEqual(
            result["battery"],
            82.5,
        )

    def test_registration_does_not_change_original_payload(self):
        manager = VehicleManager()

        vehicle = {
            "vehicle_id": "rover-test",
            "connected": True,
        }

        manager.register_or_update(vehicle)

        self.assertNotIn(
            "last_seen",
            vehicle,
        )

    def test_update_replaces_existing_vehicle_state(self):
        manager = VehicleManager()

        manager.register_or_update({
            "vehicle_id": "drone-test",
            "battery": 90,
            "connected": True,
        })

        manager.register_or_update({
            "vehicle_id": "drone-test",
            "battery": 70,
            "connected": True,
        })

        result = manager.get("drone-test")

        self.assertEqual(
            result["battery"],
            70,
        )

        self.assertEqual(
            len(manager.get_all()),
            1,
        )

    def test_multiple_vehicles_are_kept_separately(self):
        manager = VehicleManager()

        manager.register_or_update({
            "vehicle_id": "drone-test",
            "vehicle_type": "drone",
        })

        manager.register_or_update({
            "vehicle_id": "rover-test",
            "vehicle_type": "rover",
        })

        vehicles = manager.get_all()

        self.assertEqual(
            len(vehicles),
            2,
        )

        self.assertIn(
            "drone-test",
            vehicles,
        )

        self.assertIn(
            "rover-test",
            vehicles,
        )

    def test_missing_vehicle_id_is_rejected(self):
        manager = VehicleManager()

        with self.assertRaises(ValueError):
            manager.register_or_update({
                "vehicle_type": "drone",
            })

    def test_invalid_payload_is_rejected(self):
        manager = VehicleManager()

        with self.assertRaises(TypeError):
            manager.register_or_update(
                "invalid"
            )

    def test_get_unknown_vehicle_returns_none(self):
        manager = VehicleManager()

        self.assertIsNone(
            manager.get("does-not-exist")
        )

    def test_remove_vehicle(self):
        manager = VehicleManager()

        manager.register_or_update({
            "vehicle_id": "drone-test",
        })

        removed = manager.remove(
            "drone-test"
        )

        self.assertTrue(removed)

        self.assertIsNone(
            manager.get("drone-test")
        )

    def test_remove_unknown_vehicle(self):
        manager = VehicleManager()

        self.assertFalse(
            manager.remove("unknown")
        )

    def test_mark_disconnected(self):
        manager = VehicleManager()

        manager.register_or_update({
            "vehicle_id": "drone-test",
            "connected": True,
        })

        changed = manager.mark_disconnected(
            "drone-test"
        )

        self.assertTrue(changed)

        result = manager.get("drone-test")

        self.assertFalse(
            result["connected"]
        )

    def test_mark_disconnected_unknown_vehicle(self):
        manager = VehicleManager()

        self.assertFalse(
            manager.mark_disconnected(
                "unknown"
            )
        )

    def test_stale_vehicle_is_disconnected(self):
        manager = VehicleManager()

        old_timestamp = (
            datetime.now(timezone.utc)
            - timedelta(seconds=30)
        ).isoformat()

        manager.register_or_update({
            "vehicle_id": "drone-test",
            "connected": True,
            "last_seen": old_timestamp,
        })

        disconnected = manager.mark_stale(
            timeout_seconds=5
        )

        self.assertEqual(
            disconnected,
            ["drone-test"],
        )

        result = manager.get("drone-test")

        self.assertFalse(
            result["connected"]
        )

    def test_recent_vehicle_is_not_disconnected(self):
        manager = VehicleManager()

        recent_timestamp = (
            datetime.now(timezone.utc)
            - timedelta(seconds=1)
        ).isoformat()

        manager.register_or_update({
            "vehicle_id": "drone-test",
            "connected": True,
            "last_seen": recent_timestamp,
        })

        disconnected = manager.mark_stale(
            timeout_seconds=5
        )

        self.assertEqual(
            disconnected,
            [],
        )

        result = manager.get("drone-test")

        self.assertTrue(
            result["connected"]
        )

    def test_already_disconnected_vehicle_not_reported_again(self):
        manager = VehicleManager()

        old_timestamp = (
            datetime.now(timezone.utc)
            - timedelta(seconds=30)
        ).isoformat()

        manager.register_or_update({
            "vehicle_id": "drone-test",
            "connected": False,
            "last_seen": old_timestamp,
        })

        disconnected = manager.mark_stale(
            timeout_seconds=5
        )

        self.assertEqual(
            disconnected,
            [],
        )

    def test_invalid_timeout_is_rejected(self):
        manager = VehicleManager()

        with self.assertRaises(ValueError):
            manager.mark_stale(-1)

    def test_get_returns_copy(self):
        manager = VehicleManager()

        manager.register_or_update({
            "vehicle_id": "drone-test",
            "battery": 80,
        })

        result = manager.get(
            "drone-test"
        )

        result["battery"] = 10

        original = manager.get(
            "drone-test"
        )

        self.assertEqual(
            original["battery"],
            80,
        )

    def test_get_all_returns_copy(self):
        manager = VehicleManager()

        manager.register_or_update({
            "vehicle_id": "drone-test",
            "battery": 80,
        })

        result = manager.get_all()

        result["drone-test"]["battery"] = 10

        original = manager.get(
            "drone-test"
        )

        self.assertEqual(
            original["battery"],
            80,
        )

    def test_clear_removes_all_registered_vehicles(self):
        manager = VehicleManager()

        manager.register_or_update({
            "vehicle_id": "drone-test",
        })

        manager.register_or_update({
            "vehicle_id": "rover-test",
        })

        manager.clear()

        self.assertEqual(
            manager.get_all(),
            {},
        )


if __name__ == "__main__":
    unittest.main()
