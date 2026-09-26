import unittest

from src.mission.drone_decision import DroneDecisionEngine
from src.mission.event_generator import MissionEvent


class DroneDecisionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DroneDecisionEngine()

    def test_normal_mission(self) -> None:
        event = MissionEvent(
            event_type="NORMAL_OPERATION",
            severity="LOW",
            priority_score=10,
            person_count=0,
            description="No significant event detected.",
            requires_attention=False,
        )
        self.assertEqual(self.engine.decide([event]).command, "CONTINUE_MISSION")

    def test_person_detection(self) -> None:
        event = MissionEvent(
            event_type="PERSON_DETECTED",
            severity="HIGH",
            priority_score=80,
            person_count=1,
            description="1 person detected.",
            requires_attention=True,
        )
        self.assertEqual(self.engine.decide([event]).command, "INVESTIGATE_PERSON")

    def test_hazard_detection(self) -> None:
        event = MissionEvent(
            event_type="HAZARD_DETECTED",
            severity="HIGH",
            priority_score=70,
            person_count=0,
            description="Hazard detected.",
            requires_attention=True,
        )
        self.assertEqual(self.engine.decide([event]).command, "INVESTIGATE_HAZARD")

    def test_critical_situation(self) -> None:
        event = MissionEvent(
            event_type="CRITICAL_SITUATION",
            severity="CRITICAL",
            priority_score=100,
            person_count=1,
            description="Critical situation.",
            requires_attention=True,
        )
        self.assertEqual(self.engine.decide([event]).command, "EMERGENCY_RETURN")

    def test_highest_priority_wins(self) -> None:
        normal_event = MissionEvent(
            event_type="NORMAL_OPERATION",
            severity="LOW",
            priority_score=10,
            person_count=0,
            description="Normal.",
            requires_attention=False,
        )
        critical_event = MissionEvent(
            event_type="CRITICAL_SITUATION",
            severity="CRITICAL",
            priority_score=100,
            person_count=1,
            description="Critical.",
            requires_attention=True,
        )
        self.assertEqual(
            self.engine.decide([normal_event, critical_event]).command,
            "EMERGENCY_RETURN",
        )


if __name__ == "__main__":
    unittest.main()
