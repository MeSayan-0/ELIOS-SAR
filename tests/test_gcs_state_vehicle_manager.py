import unittest

from gcs.backend.state import GCSState


class TestGCSStateVehicleManager(unittest.TestCase):

    def test_initial_state_has_no_vehicles(self):
        state = GCSState()

        snapshot = state.get_snapshot()

        self.assertEqual(
            snapshot["vehicles"],
            {},
        )

    def test_vehicle_update_registers_vehicle(self):
        state = GCSState()

        state.update_vehicle(
            {
                "vehicle_id": "test-drone",
                "vehicle_type": "drone",
            }
        )

        snapshot = state.get_snapshot()

        self.assertIn(
            "test-drone",
            snapshot["vehicles"],
        )

    def test_drone_and_rover_are_independent(self):
        state = GCSState()

        state.update_vehicle(
            {
                "vehicle_id": "test-drone",
                "vehicle_type": "drone",
                "telemetry": {
                    "battery": 80.0,
                },
            }
        )

        state.update_vehicle(
            {
                "vehicle_id": "test-rover",
                "vehicle_type": "rover",
                "telemetry": {
                    "battery": 65.0,
                },
            }
        )

        snapshot = state.get_snapshot()

        self.assertEqual(
            len(snapshot["vehicles"]),
            2,
        )

        self.assertEqual(
            snapshot["vehicles"]["test-drone"]["vehicle_type"],
            "drone",
        )

        self.assertEqual(
            snapshot["vehicles"]["test-rover"]["vehicle_type"],
            "rover",
        )

        self.assertEqual(
            snapshot["vehicles"]["test-drone"]["telemetry"]["battery"],
            80.0,
        )

        self.assertEqual(
            snapshot["vehicles"]["test-rover"]["telemetry"]["battery"],
            65.0,
        )

    def test_vehicle_without_telemetry_has_no_fake_telemetry(self):
        state = GCSState()

        state.update_vehicle(
            {
                "vehicle_id": "test-rover",
                "vehicle_type": "rover",
            }
        )

        snapshot = state.get_snapshot()

        self.assertIsNone(
            snapshot["vehicles"]["test-rover"]["telemetry"]
        )

    def test_sensor_update_is_preserved(self):
        state = GCSState()

        state.update_sensor(
            {
                "vehicle_id": "test-rover",
                "sensor_id": "test-sensor",
                "sensor_type": "gas",
                "value": 42,
                "unit": "ppm",
            }
        )

        snapshot = state.get_snapshot()

        self.assertEqual(
            snapshot["sensors"]["test-sensor"]["value"],
            42,
        )

    def test_mission_update_is_preserved(self):
        state = GCSState()

        state.update_mission(
            "mission-a",
            {
                "status": "active",
            },
        )

        snapshot = state.get_snapshot()

        self.assertEqual(
            snapshot["missions"]["mission-a"]["status"],
            "active",
        )

    def test_map_starts_as_none(self):
        state = GCSState()

        snapshot = state.get_snapshot()

        self.assertIsNone(
            snapshot["map"]
        )

    def test_map_update_is_preserved(self):
        state = GCSState()

        map_payload = {
            "map_id": "real-map",
            "map_type": "global",
            "width": 2,
            "height": 2,
            "resolution": 0.1,
            "cells": [
                [0, 1],
                [1, 0],
            ],
        }

        state.set_map(map_payload)

        snapshot = state.get_snapshot()

        self.assertEqual(
            snapshot["map"],
            map_payload,
        )

    def test_snapshot_is_independent_copy(self):
        state = GCSState()

        state.update_vehicle(
            {
                "vehicle_id": "test-drone",
                "vehicle_type": "drone",
            }
        )

        snapshot = state.get_snapshot()

        snapshot["vehicles"]["test-drone"]["connected"] = False

        second_snapshot = state.get_snapshot()

        self.assertTrue(
            second_snapshot["vehicles"]["test-drone"]["connected"]
        )


if __name__ == "__main__":
    unittest.main()
