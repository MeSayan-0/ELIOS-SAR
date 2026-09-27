"""Tests for ELIOS-SAR's standard data contracts."""

import time
import unittest

from src.utils.messages import (
    EnvironmentState,
    FlightState,
    HazardDetection,
    LidarState,
    MissionEvent,
    PersonDetection,
    Position2D,
    RiskAssessment,
    SituationalState,
)


class MessageContractTests(unittest.TestCase):
    def test_detection_contracts_keep_optional_positions(self) -> None:
        position = Position2D(x=4.2, y=2.7, heading=83.0)
        person = PersonDetection(
            id=1,
            confidence=0.91,
            bbox=[120.0, 80.0, 300.0, 500.0],
            position=position,
        )
        hazard = HazardDetection(
            id=2,
            hazard_type="unclassified",
            confidence=0.75,
            bbox=[20.0, 30.0, 80.0, 90.0],
        )

        self.assertEqual(person.position, position)
        self.assertIsNone(hazard.position)
        self.assertGreater(person.timestamp, 0.0)

    def test_situational_state_composes_independent_subsystems(self) -> None:
        state = SituationalState(
            people=[PersonDetection(id=1, confidence=0.91, bbox=[1, 2, 3, 4])],
            hazards=[],
            environment=EnvironmentState(methane=0.8, temperature=31.4, humidity=78.0),
            lidar=LidarState(ranges=[1.2, 1.6], angle_min=-1.57, angle_increment=0.01),
            flight=FlightState(armed=True, altitude=2.5, battery=87.0),
        )

        self.assertEqual(len(state.people), 1)
        self.assertEqual(state.environment.methane, 0.8)
        self.assertEqual(state.lidar.ranges[1], 1.6)

    def test_events_and_risk_receive_independent_timestamps(self) -> None:
        before = time.time()
        assessment = RiskAssessment(
            subject_id=1,
            risk_level="LOW",
            risk_score=0.0,
            reasons=[],
        )
        event = MissionEvent(
            event_type="PERSON_DETECTED",
            priority="LOW",
            location=None,
            description="A person was detected.",
        )

        self.assertGreaterEqual(assessment.timestamp, before)
        self.assertGreaterEqual(event.timestamp, before)
        self.assertIsNone(event.location)


if __name__ == "__main__":
    unittest.main()
