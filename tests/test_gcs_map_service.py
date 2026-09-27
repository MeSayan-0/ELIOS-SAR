import unittest

from gcs.backend.map_service import GCSMapService


class TestGCSMapService(unittest.TestCase):

    def test_initial_snapshot_is_none(self):
        """GCSMapService starts with no map — nothing fabricated."""
        service = GCSMapService()

        self.assertIsNone(service.get_snapshot())

    def test_update_stores_map(self):
        """update() persists the payload so get_snapshot() returns it."""
        service = GCSMapService()

        payload = {
            "width": 100,
            "height": 100,
            "resolution": 0.1,
            "origin": {"x": -5.0, "y": -5.0},
            "cells": [[0] * 100 for _ in range(100)],
        }

        service.update(payload)

        snapshot = service.get_snapshot()

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot["width"], 100)
        self.assertEqual(snapshot["height"], 100)
        self.assertEqual(snapshot["resolution"], 0.1)

    def test_clear_removes_map(self):
        """clear() returns the service to a no-map state."""
        service = GCSMapService()

        service.update({"width": 50, "height": 50, "cells": []})

        service.clear()

        self.assertIsNone(service.get_snapshot())

    def test_snapshot_is_independent_copy(self):
        """Mutating the returned snapshot must not corrupt internal state."""
        service = GCSMapService()

        service.update({"width": 10, "height": 10, "cells": [[0] * 10]})

        snapshot = service.get_snapshot()
        snapshot["width"] = 9999

        self.assertEqual(service.get_snapshot()["width"], 10)

    def test_update_rejects_non_dict(self):
        """update() must raise ValueError for non-dict payloads."""
        service = GCSMapService()

        with self.assertRaises(ValueError):
            service.update("not-a-dict")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
