import unittest

from src.communication.messages import (
    HazardMessage,
    MapUpdateMessage,
    MissionEventMessage,
    MissionStateMessage,
    PersonDetectionMessage,
    RiskEventMessage,
    SensorStateMessage,
    VehicleStateMessage,
)


class TestVehicleStateMessage(unittest.TestCase):

    def test_minimum_vehicle_state(self):
        message = VehicleStateMessage(
            vehicle_id="real-vehicle",
            vehicle_type="drone",
            timestamp="2026-08-29T00:00:00+00:00",
            connected=True,
        )

        self.assertEqual(
            message.to_payload(),
            {
                "vehicle_id": "real-vehicle",
                "vehicle_type": "drone",
                "timestamp": "2026-08-29T00:00:00+00:00",
                "connected": True,
            },
        )

    def test_invalid_vehicle_type(self):
        with self.assertRaises(ValueError):
            VehicleStateMessage(
                vehicle_id="real-vehicle",
                vehicle_type="unknown",
                timestamp="2026-08-29T00:00:00+00:00",
                connected=True,
            )


class TestSensorStateMessage(unittest.TestCase):

    def test_sensor_payload(self):
        message = SensorStateMessage(
            vehicle_id="real-rover",
            sensor_id="sensor-a",
            sensor_type="gas",
            timestamp="2026-08-29T00:00:00+00:00",
            value=123,
            unit="ppm",
            status="ok",
        )

        payload = message.to_payload()

        self.assertEqual(payload["vehicle_id"], "real-rover")
        self.assertEqual(payload["sensor_id"], "sensor-a")
        self.assertEqual(payload["value"], 123)
        self.assertEqual(payload["unit"], "ppm")


class TestPersonDetectionMessage(unittest.TestCase):

    def test_detection_payload(self):
        message = PersonDetectionMessage(
            vehicle_id="real-drone",
            timestamp="2026-08-29T00:00:00+00:00",
            detection_id="detection-a",
            confidence=0.91,
        )

        payload = message.to_payload()

        self.assertEqual(
            payload["detection_id"],
            "detection-a",
        )
        self.assertEqual(
            payload["confidence"],
            0.91,
        )

    def test_invalid_confidence(self):
        with self.assertRaises(ValueError):
            PersonDetectionMessage(
                vehicle_id="real-drone",
                timestamp="2026-08-29T00:00:00+00:00",
                detection_id="detection-a",
                confidence=1.5,
            )


class TestHazardMessage(unittest.TestCase):

    def test_hazard_payload(self):
        message = HazardMessage(
            vehicle_id="real-drone",
            timestamp="2026-08-29T00:00:00+00:00",
            hazard_id="hazard-a",
            hazard_type="gas",
            severity="high",
        )

        payload = message.to_payload()

        self.assertEqual(
            payload["hazard_type"],
            "gas",
        )
        self.assertEqual(
            payload["severity"],
            "high",
        )


class TestRiskEventMessage(unittest.TestCase):

    def test_risk_payload(self):
        message = RiskEventMessage(
            vehicle_id="real-drone",
            timestamp="2026-08-29T00:00:00+00:00",
            risk_id="risk-a",
            risk_level="high",
            score=82.0,
            reason="Observed risk condition",
        )

        payload = message.to_payload()

        self.assertEqual(
            payload["risk_level"],
            "high",
        )
        self.assertEqual(
            payload["score"],
            82.0,
        )


class TestMissionStateMessage(unittest.TestCase):

    def test_mission_payload(self):
        message = MissionStateMessage(
            mission_id="mission-a",
            status="active",
            timestamp="2026-08-29T00:00:00+00:00",
        )

        payload = message.to_payload()

        self.assertEqual(
            payload["mission_id"],
            "mission-a",
        )
        self.assertEqual(
            payload["status"],
            "active",
        )


class TestMissionEventMessage(unittest.TestCase):

    def test_event_payload(self):
        message = MissionEventMessage(
            mission_id="mission-a",
            timestamp="2026-08-29T00:00:00+00:00",
            event_id="event-a",
            event_type="mission",
            message="Mission event received",
        )

        payload = message.to_payload()

        self.assertEqual(
            payload["mission_id"],
            "mission-a",
        )
        self.assertEqual(
            payload["event_id"],
            "event-a",
        )


class TestMapUpdateMessage(unittest.TestCase):

    def test_map_payload(self):
        message = MapUpdateMessage(
            map_id="map-a",
            map_type="local",
            timestamp="2026-08-29T00:00:00+00:00",
            resolution=0.1,
            width=2,
            height=2,
            origin={
                "x": 0.0,
                "y": 0.0,
                "yaw": 0.0,
            },
            cells=[
                [0, 1],
                [1, 0],
            ],
            vehicle_id="real-drone",
        )

        payload = message.to_payload()

        self.assertEqual(
            payload["map_id"],
            "map-a",
        )
        self.assertEqual(
            payload["map_type"],
            "local",
        )
        self.assertEqual(
            payload["width"],
            2,
        )
        self.assertEqual(
            payload["height"],
            2,
        )

    def test_invalid_map_dimensions(self):
        with self.assertRaises(ValueError):
            MapUpdateMessage(
                map_id="map-a",
                map_type="local",
                timestamp="2026-08-29T00:00:00+00:00",
                resolution=0.1,
                width=2,
                height=2,
                origin={
                    "x": 0.0,
                    "y": 0.0,
                    "yaw": 0.0,
                },
                cells=[
                    [0, 1],
                ],
            )


if __name__ == "__main__":
    unittest.main()
